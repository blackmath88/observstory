import unittest

from observstory import config
from observstory.derive import area_of, is_ignored, lane_of
from tests.helpers import snapshot

CONTAINERS = config.DEFAULT_CONTAINERS


class Paths(unittest.TestCase):
    def test_area_container_aware(self):
        self.assertEqual(area_of("src/conversation/store.py", 1, CONTAINERS), "src/conversation")
        self.assertEqual(area_of("docs/setup.md", 1, CONTAINERS), "docs")
        self.assertEqual(area_of("README.md", 1, CONTAINERS), "README.md")
        self.assertEqual(area_of("src/main.py", 1, CONTAINERS), "src")

    def test_lane_matching_is_anchored_not_substring(self):
        """v0 bug: 'test/' matched 'latest/x' via substring."""
        lanes = [{"id": "verify", "paths": ["test/"]}]
        self.assertEqual(lane_of("latest", True, lanes), "other")
        self.assertEqual(lane_of("test", True, lanes), "verify")

    def test_prefix_file_patterns(self):
        lanes = [{"id": "contract", "paths": ["observstory.config"]}]
        self.assertEqual(lane_of("observstory.config.json", False, lanes), "contract")

    def test_ignore_list(self):
        ignore = config.DEFAULT_IGNORE
        self.assertTrue(is_ignored("package-lock.json", ignore))
        self.assertTrue(is_ignored("web/package-lock.json", ignore))
        self.assertTrue(is_ignored("dist/app.js", ignore))
        self.assertTrue(is_ignored("web/dist/app.js", ignore))
        self.assertTrue(is_ignored("static/app.min.js", ignore))
        self.assertFalse(is_ignored("src/distance.py", ignore))
        self.assertTrue(is_ignored("packages/astro/CHANGELOG.md", ignore))
        self.assertTrue(is_ignored(".changeset/olive-queens-enjoy.md", ignore))
        self.assertTrue(is_ignored("packages/tldraw/api-report.api.md", ignore))

    def test_anchored_ignore_does_not_hide_nested_dirs(self):
        """Dogfood finding: the output dir 'observstory/' was hiding src/observstory/."""
        ignore = config.DEFAULT_IGNORE
        self.assertTrue(is_ignored("observstory/index.html", ignore))
        self.assertFalse(is_ignored("src/observstory/cli.py", ignore))


class Config(unittest.TestCase):
    def test_zero_config_produces_areas_and_signals(self):
        snap = snapshot("e1-same-subsystem")
        self.assertEqual(snap["config"]["source"], "default")
        self.assertTrue(snap["areas"])
        self.assertTrue(snap["signals"])
        self.assertIn("build", {lane["id"] for lane in snap["lanes"]})

    def test_rejects_bad_config(self):
        with self.assertRaises(config.ConfigError):
            config.normalise({"lanes": [{"label": "no id"}]})
        with self.assertRaises(config.ConfigError):
            config.normalise({"signals": {"stale_hours": -1}})
        with self.assertRaises(config.ConfigError):
            config.normalise({"signals": {"made_up": 1}})
        with self.assertRaises(config.ConfigError):
            config.normalise({"signals": {"overlap_require_shared_file": 1}})
        with self.assertRaises(config.ConfigError):
            config.normalise({"signals": {"stale_hours": True}})

    def test_custom_lanes(self):
        snap = snapshot("e1-same-subsystem", {"lanes": [{"id": "chat", "label": "Chat", "paths": ["src/conversation/"]}]})
        lanes = {lane["id"]: lane for lane in snap["lanes"]}
        self.assertEqual(lanes["chat"]["areas"], ["src/conversation"])


class Derivation(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(snapshot("demo-t2"), snapshot("demo-t2"))

    def test_merged_pr_commits_attributed_to_pr_not_direct(self):
        from observstory import derive
        from tests.helpers import observations
        obs = observations("e2-parallel")
        obs["pull_requests"].append({"number": 5, "title": "x", "state": "closed", "merged": True, "draft": False,
                                     "head": "a/x", "base": "main", "author": {"login": "ben"},
                                     "updated_at": obs["fetched_at"], "url": "u", "paths": ["lib/x.py"], "commits": []})
        obs["commits"].append({"sha": "f" * 40, "date": obs["fetched_at"], "author": {"login": "ben"},
                               "message": "Add x (#5)", "paths": ["lib/x.py"]})
        snap = derive.derive(obs, config.normalise(None), derive.parse_time(obs["fetched_at"]))
        commit = next(c for c in snap["commits"] if c["sha"] == "f" * 40)
        self.assertEqual(commit["work_item"], "pr:5")
        direct = next(w for w in snap["work_items"] if w["id"] == "direct:ben")
        self.assertNotIn("lib/x.py", direct["paths"])


if __name__ == "__main__":
    unittest.main()
