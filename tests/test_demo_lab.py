"""Demo Lab (issue #6): synthetic states through the real pipeline tell one coherent story."""

import json
import re
import sys
import unittest

from observstory import config
from observstory.derive import derive, parse_time
from observstory.map_compiler import compile_scene
from observstory.validate import scene_errors, validate
from tests.helpers import ROOT

sys.path.insert(0, str(ROOT / "fixtures"))
import demo_lab  # noqa: E402

STORY = ["quiet", "parallel", "overlap", "crowded", "resolved", "calm"]
# state: (in flight, overlaps, waiting, stale, bursts)
EXPECTED = {
    "quiet": (0, 0, 0, 0, 0), "parallel": (3, 0, 0, 0, 0), "overlap": (3, 1, 0, 0, 0),
    "crowded": (5, 3, 0, 0, 0), "resolved": (4, 0, 2, 0, 0), "calm": (2, 0, 0, 0, 0),
    "burst": (3, 0, 0, 0, 1), "stale": (3, 0, 0, 2, 0), "other-project": (4, 1, 1, 0, 0),
}


def state(sid):
    obs = json.loads((ROOT / "fixtures/demo-lab" / f"{sid}.json").read_text())
    cfg = demo_lab.RECSYS_CONFIG if sid == "other-project" else demo_lab.CHAT_APP_CONFIG
    snap = derive(obs, config.normalise(cfg), parse_time(obs["fetched_at"]))
    return obs, snap, compile_scene(snap)


class DemoLab(unittest.TestCase):
    def test_stored_fixtures_match_the_generator(self):
        for sid, obs in demo_lab.build().items():
            with self.subTest(state=sid):
                self.assertEqual(json.loads((ROOT / "fixtures/demo-lab" / f"{sid}.json").read_text()), obs)

    def test_every_state_goes_through_the_real_pipeline_cleanly(self):
        for sid in EXPECTED:
            with self.subTest(state=sid):
                _, snap, scene = state(sid)
                self.assertEqual(validate(snap) + scene_errors(scene), [])
                self.assertTrue(snap["provenance"]["source"].startswith("synthetic"))

    def test_each_state_shows_what_its_caption_promises(self):
        for sid, (in_flight, overlaps, waiting, stale, bursts) in EXPECTED.items():
            with self.subTest(state=sid):
                _, snap, scene = state(sid)
                kinds = [s["type"] for s in snap["signals"]]
                self.assertEqual((scene["status"]["in_flight"], scene["status"]["overlaps"], kinds.count("waiting"),
                                  kinds.count("stale"), kinds.count("burst")), (in_flight, overlaps, waiting, stale, bursts))

    def test_the_story_is_one_project_over_time(self):
        times = []
        for sid in STORY:
            obs, _, _ = state(sid)
            self.assertEqual(obs["repository"]["full_name"], "northstar/chat-app")
            times.append(obs["fetched_at"])
        self.assertEqual(times, sorted(times))
        # the same work keeps the same number across states
        titles = {sid: {p["number"]: p["title"] for p in state(sid)[0]["pull_requests"]} for sid in STORY}
        self.assertEqual({titles[s][41] for s in STORY[1:]}, {"Conversation memory"})

    def test_quiet_and_parallel_ask_for_nothing(self):
        for sid in ("quiet", "parallel", "calm"):
            self.assertEqual(state(sid)[2]["attention"], [])

    def test_overlap_is_visible_before_a_pull_request_exists(self):
        _, _, scene = state("overlap")
        [edge] = scene["edges"]
        self.assertIn("branch:sofia/chat-history", (edge["from"], edge["to"]))
        self.assertEqual(edge["files"], ["src/conversation/store.py"])

    def test_crowded_area_without_a_shared_file_gets_no_connector(self):
        _, _, scene = state("crowded")
        in_edges = {x for e in scene["edges"] for x in (e["from"], e["to"])}
        self.assertEqual(in_edges, {"pr:41", "pr:43", "pr:46"})
        group = next(g for g in scene["groups"] if g["path"] == "src/conversation")
        self.assertIn("pr:47", group["nodes"])  # same card, no connector

    def test_resolution_replaces_overlap_with_waiting(self):
        _, snap, scene = state("resolved")
        self.assertEqual([e["type"] for e in scene["edges"]], ["waiting", "waiting"])
        bases = {s["work_items"][0]: s["basis"] for s in snap["signals"] if s["type"] == "waiting"}
        self.assertEqual(bases, {"pr:44": "declared", "pr:46": "derived"})
        overlap_rule = [s for s in snap["signals"] if s["type"] == "overlap"]
        self.assertEqual(overlap_rule, [])  # the stack explains #46's shared ground with #41

    def test_custom_lanes_recompose_the_map(self):
        _, _, scene = state("other-project")
        self.assertEqual([z["label"] for z in scene["zones"]], ["Data", "Pipeline", "Model", "Eval", "API", "Docs"])

    def test_synthetic_data_links_nowhere(self):
        for sid in EXPECTED:
            obs, _, _ = state(sid)
            self.assertNotIn("http", json.dumps(obs))


class BuiltDemo(unittest.TestCase):
    def test_pages_are_static_and_offline(self):
        pages = [ROOT / "demo/index.html"] + sorted((ROOT / "demo/states").glob("*.html"))
        self.assertEqual(len(pages), 1 + len(EXPECTED))
        for page in pages:
            text = page.read_text()
            with self.subTest(page=page.name):
                self.assertIsNone(re.search(r"<script[^>]+src=|<link[^>]+href=\"https?:|fetch\(|XMLHttpRequest", text))

    def test_shell_lists_every_state_and_says_it_is_synthetic(self):
        text = (ROOT / "demo/index.html").read_text()
        for sid in EXPECTED:
            self.assertIn(f'id="tab-{sid}"', text)
        self.assertIn("Synthetic data", text)


if __name__ == "__main__":
    unittest.main()
