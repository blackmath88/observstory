"""Project Knowledge (opt-in). Every repository here is a SYNTHETIC fixture built in a temp dir; none of it is
project history. Each test commits files, then builds artifacts from Git objects exactly as the CLI does."""

import json
import pathlib
import re
import subprocess
import tempfile
import unittest

from observstory import knowledge
from observstory.knowledge_render import render_knowledge
from observstory.map_compiler import compile_scene
from observstory.map_render import render_map
from tests.helpers import snapshot

M = ".observstory/knowledge.json"


def manifest(records, links=(), imports=()):
    return json.dumps({"schema": knowledge.MANIFEST_SCHEMA, "title": "Synthetic fixture", "selection_policy": "explicit-declaration/v1",
                       "audience": "public", "records": list(records), "links": list(links), "imports": list(imports)})


CONCEPT_A = "# Concept A\n\n## Open questions\n\n- Is A enough?\n"
CONCEPT_B = "# Concept B\n\nA different direction.\n\n## Open questions\n\n- Is A enough?\n"
README = "# Fixture\n\nStart with [the current concept](CONCEPT.md).\n"
BASE_RECORDS = [
    {"id": "concept", "type": "concept", "path": "CONCEPT.md", "status": "current",
     "declared_in": [{"path": "README.md", "quote": "Start with [the current concept](CONCEPT.md)."}]},
    {"id": "old", "type": "concept", "path": "OLD.md", "status": "superseded"},
    {"id": "questions", "type": "question", "path": "CONCEPT.md", "section": "Open questions", "status": "open"},
]
BASE_LINKS = [{"from": "concept", "rel": "supersedes", "to": "old"}]


class Repo:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = self._tmp.name
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")

    def git(self, *args):
        return subprocess.run(["git", "-C", self.path, *args], check=True, capture_output=True, text=True).stdout.strip()

    def write(self, files):
        for name, text in files.items():
            p = pathlib.Path(self.path, name)
            if text is None:
                p.unlink()
                continue
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def commit(self, files, msg="fixture"):
        self.write(files)
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def build(self, ref="HEAD"):
        return knowledge.build(self.path, ref, M, "fixture/repo")

    def close(self):
        self._tmp.cleanup()


def base_files(concept=CONCEPT_A, records=BASE_RECORDS, links=BASE_LINKS):
    return {"README.md": README, "CONCEPT.md": concept, "OLD.md": "# Old\n", M: manifest(records, links)}


class KnowledgeTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)

    def test_feature_disabled_preserves_project_map(self):
        scene = compile_scene(snapshot("demo-t2"))
        self.assertEqual(render_map(scene), render_map(scene, knowledge_href=None))
        self.assertNotIn("project knowledge", render_map(scene))
        self.assertIn('<a href="knowledge.html">project knowledge</a>', render_map(scene, knowledge_href="knowledge.html"))

    def test_disabled_build_writes_no_knowledge_outputs(self):
        from observstory import cli
        with tempfile.TemporaryDirectory() as out:
            cli._write_outputs(pathlib.Path(out), None, snapshot("demo-t2"))
            self.assertFalse(pathlib.Path(out, "knowledge.html").exists())
            self.assertFalse(pathlib.Path(out, "data", "knowledge.json").exists())

    def test_brief_selects_verified_current_concept(self):
        self.repo.commit(base_files())
        a = self.repo.build()
        self.assertEqual(knowledge.artifact_errors(a), [])
        self.assertTrue(a["complete"])
        self.assertEqual(a["diagnostics"], [])
        b = knowledge.brief(a)
        cd = b["answer"]["current_direction"]
        self.assertEqual((cd["state"], cd["record"]["id"]), ("selected", "concept"))
        self.assertEqual(cd["record"]["basis"]["declarations"][0]["line"], 3)
        self.assertEqual([r["id"] for r in b["answer"]["retired"]], ["old"])
        q = b["answer"]["open_questions"][0]
        self.assertEqual(q["location"], {"start_line": 3, "end_line": 5})
        self.assertIn("Is A enough?", q["excerpt"])
        for key in ("repository", "requested_ref", "resolved_commit", "snapshot_id", "complete"):
            self.assertIn(key, b["snapshot"])
        rec = knowledge.record(a, "concept")["answer"]
        self.assertEqual(rec["outgoing"][0]["to"], "old")
        self.assertTrue(rec["record"]["url"].startswith(f"https://github.com/fixture/repo/blob/{a['resolved_commit']}/CONCEPT.md"))
        self.assertFalse(knowledge.record(a, "nope")["answer"]["found"])

    def test_reads_one_commit_not_the_working_tree(self):
        c1 = self.repo.commit(base_files())
        self.repo.commit({"CONCEPT.md": CONCEPT_B})
        self.repo.write({"CONCEPT.md": "# Uncommitted edit\n", "OLD.md": None})  # dirty tree must be invisible
        a1, a2 = self.repo.build(c1), self.repo.build("HEAD")
        self.assertEqual(a1["resolved_commit"], c1)
        self.assertTrue(a2["complete"])
        title = lambda a: next(r["title"] for r in a["records"] if r["id"] == "concept")  # noqa: E731
        self.assertEqual((title(a1), title(a2)), ("Concept A", "Concept B"))
        blob = self.repo.git("rev-parse", f"{c1}:CONCEPT.md")
        self.assertEqual(next(r["blob"] for r in a1["records"] if r["id"] == "concept"), blob)

    def test_branches_are_scoped_independently(self):
        self.repo.commit(base_files())
        self.repo.git("checkout", "-q", "-b", "proposal")
        alt = [dict(r) for r in BASE_RECORDS] + [{"id": "concept-b", "type": "concept", "path": "B.md", "status": "current"}]
        self.repo.commit({"B.md": CONCEPT_B, M: manifest(alt, BASE_LINKS)})
        self.repo.git("checkout", "-q", "main")
        main, prop = self.repo.build("main"), self.repo.build("proposal")
        self.assertNotEqual(main["snapshot_id"], prop["snapshot_id"])
        self.assertEqual(main["selection"]["current_direction"]["record"], "concept")
        self.assertEqual(prop["selection"]["current_direction"]["state"], "unresolved")
        self.assertNotIn("concept-b", {r["id"] for r in main["records"]})
        self.assertEqual(self.repo.build("main")["snapshot_id"], main["snapshot_id"])  # deterministic membership

    def test_a_b_a_revert_restores_a(self):
        c1 = self.repo.commit(base_files(CONCEPT_A))
        c2 = self.repo.commit({"CONCEPT.md": CONCEPT_B})
        c3 = self.repo.commit({"CONCEPT.md": CONCEPT_A})
        a1, a2, a3 = (self.repo.build(c) for c in (c1, c2, c3))
        h = lambda a: next(r["content_sha256"] for r in a["records"] if r["id"] == "concept")  # noqa: E731
        self.assertEqual(h(a1), h(a3))
        self.assertNotEqual(h(a2), h(a3))
        self.assertEqual(len({a1["snapshot_id"], a2["snapshot_id"], a3["snapshot_id"]}), 3)
        diff = knowledge.changes(a2, a3)
        self.assertEqual([x["id"] for x in diff["records"]["content_changed"]], ["concept"])
        self.assertEqual(diff["records"]["content_changed"][0]["to_sha256"], h(a1))

    def test_complete_removal_versus_incomplete_intake(self):
        c1 = self.repo.commit(base_files())
        removed = [r for r in BASE_RECORDS if r["id"] != "old"]
        c2 = self.repo.commit({M: manifest(removed)})
        d = knowledge.changes(self.repo.build(c1), self.repo.build(c2))
        self.assertEqual([x["id"] for x in d["records"]["removed"]], ["old"])
        # A selected file vanishing is an incomplete read, not a deletion of the record.
        c3 = self.repo.commit({"CONCEPT.md": None, M: manifest(removed[:1])})
        a3 = self.repo.build(c3)
        self.assertFalse(a3["complete"])
        self.assertIn("source_missing_at_commit", {x["code"] for x in a3["diagnostics"]})
        d = knowledge.changes(self.repo.build(c2), a3)
        self.assertEqual(d["records"]["removed"], [])
        self.assertEqual([x["id"] for x in d["records"]["removal_unconfirmed"]], ["questions"])
        self.assertEqual([x["id"] for x in d["records"]["unreadable_in_target"]], ["concept"])
        self.assertEqual(a3["selection"]["current_direction"]["reason"], "source_unreadable")

    def test_conflicting_or_unverified_declarations_stay_unresolved(self):
        two = [dict(r) for r in BASE_RECORDS] + [{"id": "rival", "type": "concept", "path": "OLD.md", "status": "current"}]
        self.repo.commit(base_files(records=two))
        cd = self.repo.build()["selection"]["current_direction"]
        self.assertEqual((cd["state"], cd["reason"], cd["candidates"]), ("unresolved", "conflicting_declarations", ["concept", "rival"]))
        self.repo.commit({"README.md": "# Fixture\n\nNo pointer here.\n", M: manifest(BASE_RECORDS, BASE_LINKS)})
        a = self.repo.build()
        self.assertEqual(a["selection"]["current_direction"]["reason"], "declaration_unverified")
        self.assertIn("declaration_not_found", {x["code"] for x in a["diagnostics"]})

    def test_broken_references_cycles_duplicates_and_self_approval(self):
        recs = [dict(r) for r in BASE_RECORDS] + [
            {"id": "old", "type": "concept", "path": "OLD.md", "status": "historical"},
            {"id": "d", "type": "decision", "path": "OLD.md", "status": "declared"},
            {"id": "x", "type": "concept", "path": "OLD.md", "status": "bogus"}]
        links = BASE_LINKS + [{"from": "old", "rel": "supersedes", "to": "concept"},
                              {"from": "concept", "rel": "informs", "to": "ghost"}]
        self.repo.commit(base_files(records=recs, links=links))
        a = self.repo.build()
        codes = {x["code"] for x in a["diagnostics"]}
        self.assertTrue({"duplicate_id", "dangling_link", "supersession_cycle", "superseded_but_current",
                         "confirmation_required", "invalid_status"} <= codes, codes)
        self.assertEqual(a["selection"]["current_direction"]["state"], "unresolved")
        self.assertFalse(next(x for x in a["relationships"] if x["to"] == "ghost")["resolved"])

    def test_history_unavailable(self):
        c1 = self.repo.commit({"README.md": README})
        self.repo.commit(base_files())
        a = self.repo.build()
        self.assertEqual(knowledge.changes(None, a)["state"], "history_unavailable")
        with self.assertRaises(knowledge.KnowledgeError):
            self.repo.build(c1)  # no manifest at that commit: no artifact, never an empty "nothing changed"
        with self.assertRaises(knowledge.KnowledgeError):
            self.repo.build("no-such-branch")

    def test_coordination_import_keeps_existing_ids_and_status(self):
        coord = {"schema": "observstory.coordination/v1",
                 "sessions": [{"id": "S1", "open_questions": ["Who owns M2?"]}],
                 "gates": [], "commitments": [],
                 "decisions": [{"id": "D1", "text": "Two repos.", "status": "declared", "confirmed_by": "A person",
                                "confirmed_at": "2026-10-31T10:00:00+01:00"},
                               {"id": "D2", "text": "Maybe.", "status": "proposed"}]}
        files = base_files()
        files[".observstory/coordination.json"] = json.dumps(coord, indent=2)
        files[M] = json.dumps({**json.loads(files[M]), "imports": [
            {"adapter": "observstory.coordination/v1", "path": ".observstory/coordination.json"}]})
        self.repo.commit(files)
        a = self.repo.build()
        by = {r["id"]: r for r in a["records"]}
        self.assertEqual(by["coordination:D1"]["basis"]["kind"], "coordination_confirmed")
        self.assertEqual(by["coordination:D2"]["status"], "proposed")
        self.assertEqual(by["coordination:D2"]["basis"]["kind"], "coordination_recorded")
        self.assertEqual(by["coordination:S1.Q1"]["type"], "question")
        self.assertIsNotNone(by["coordination:D1"]["location"])

    def test_human_view_and_query_agree(self):
        self.repo.commit(base_files())
        a = self.repo.build()
        page = render_knowledge(a, knowledge.changes(None, a))
        ans = knowledge.brief(a)["answer"]
        shown = re.findall(r'<article class="kr" id="r-[^"]+" data-id="([^"]+)" data-status="([^"]+)"', page)
        expected = [(r["id"], r["status"]) for r in [ans["current_direction"]["record"]] + ans["decisions"]
                    + ans["open_questions"] + ans["plans"] + ans["research"] + ans["retired"]]
        self.assertEqual(shown, expected)
        receipt = json.loads(re.search(r'id="knowledge-receipt">(.*?)</script>', page).group(1))
        self.assertEqual(receipt, knowledge.receipt(a))
        self.assertIn('data-state="history_unavailable"', page)

    def test_source_html_is_escaped_never_executed(self):
        evil = '# <img src=x onerror=alert(1)>\n\n## Open questions\n\n<script>alert("x")</script>\n'
        self.repo.commit(base_files(concept=evil))
        page = render_knowledge(self.repo.build())
        self.assertNotIn("<script>alert", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", page)
        self.assertEqual(re.findall(r"<script[^>]*>", page), ['<script type="application/json" id="knowledge-receipt">'])


if __name__ == "__main__":
    unittest.main()
