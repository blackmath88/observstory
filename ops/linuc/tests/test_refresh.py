"""Synthetic-only acceptance for the owned-host Observstory publisher."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "refresh.py"
spec = importlib.util.spec_from_file_location("linuc_refresh", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class OwnedHostPilot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.producer = self.root / "producer"
        self.source.mkdir()
        (self.producer / "scripts").mkdir(parents=True)
        for repo in (self.source, self.producer):
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "synthetic@example.invalid")
            git(repo, "config", "user.name", "Synthetic pilot")
        (self.source / "README.md").write_text("First revision\n")
        self.commit(self.source, "First")
        (self.producer / "scripts/observstory.py").write_text(
            "import json, os, pathlib, sys\n"
            "if os.environ.get('TEST_FORCE_FAIL') == '1': sys.exit(2)\n"
            "out=pathlib.Path(os.environ['OBSERVSTORY_OUTPUT'])\n"
            "(out/'data').mkdir(parents=True)\n"
            "snap={'schema':'observstory.snapshot/v1',"
            "'repository':{'full_name':os.environ['OBSERVSTORY_REPOSITORY']},"
            "'trigger':{'sha':os.environ['OBSERVSTORY_SHA']},"
            "'provenance':{'degraded':[]},'generated_at':'2026-11-17T00:00:00Z'}\n"
            "(out/'data/snapshot.json').write_text(json.dumps(snap))\n"
            "(out/'index.html').write_text('<h1>Synthetic Observatory</h1>')\n"
        )
        (self.producer / "scripts/publish_workspace.py").write_text("# synthetic no-op\n")
        producer_sha = self.commit(self.producer, "Pinned producer")
        self.config = {
            "schema": "observstory.owned-host/v1",
            "state_root": str(self.root / "state"),
            "producer_root": str(self.producer),
            "producer_sha": producer_sha,
            "allow_local_test_sources": True,
            "repositories": [{
                "name": "synthetic/observstory-pilot",
                "source": self.source.as_uri(),
                "branch": "main",
                "frontend": "classic",
            }],
        }
        self.slug = runner.slug_for("synthetic/observstory-pilot")

    def commit(self, repo, message):
        git(repo, "add", ".")
        git(repo, "commit", "-qm", message)
        return git(repo, "rev-parse", "HEAD")

    def test_atomic_revision_and_failed_build_preserves_last_good(self):
        self.assertEqual(runner.refresh(self.config), 0)
        link = self.root / "state/public" / self.slug
        self.assertTrue(link.is_symlink())
        initial = link.resolve()
        self.assertEqual(json.loads((link / "build.json").read_text())["sha"],
                         git(self.source, "rev-parse", "HEAD"))
        self.assertIn("Synthetic Observatory", (link / "index.html").read_text())

        (self.source / "README.md").write_text("Second revision\n")
        self.commit(self.source, "Second")
        with patch.dict(os.environ, {"TEST_FORCE_FAIL": "1"}):
            self.assertEqual(runner.refresh(self.config), 1)
        self.assertEqual(link.resolve(), initial)
        status = json.loads((self.root / "state/status" / (self.slug + ".json")).read_text())
        self.assertEqual(status["status"], "failed")
        self.assertNotIn("synthetic@example.invalid", json.dumps(status))

        self.assertEqual(runner.refresh(self.config), 0)
        self.assertNotEqual(link.resolve(), initial)
        self.assertEqual(json.loads((link / "build.json").read_text())["sha"],
                         git(self.source, "rev-parse", "HEAD"))

    def test_rejects_unknown_source_and_duplicate_enrollment(self):
        bad = json.loads(json.dumps(self.config))
        bad["allow_local_test_sources"] = False
        with self.assertRaisesRegex(runner.RefreshError, "unapproved source"):
            runner.validate_config(bad)
        duplicate = json.loads(json.dumps(self.config))
        duplicate["repositories"].append(dict(duplicate["repositories"][0]))
        with self.assertRaisesRegex(runner.RefreshError, "duplicate"):
            runner.validate_config(duplicate)

    def test_pinned_producer_rejects_uncommitted_changes(self):
        (self.producer / "UNCOMMITTED").write_text("canary")
        with self.assertRaisesRegex(runner.RefreshError, "uncommitted"):
            runner.pinned_source(self.config)


if __name__ == "__main__":
    unittest.main()
