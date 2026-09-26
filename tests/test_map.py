"""Project Map (issue #3): the scene compiler is tested apart from the renderer."""

import json
import pathlib
import re
import unittest

from observstory.map_compiler import compile_scene
from observstory.map_render import render_map
from observstory.validate import scene_errors
from tests.helpers import ROOT, snapshot

ML = json.loads((ROOT / "fixtures/configs/ml-project.json").read_text())


def scene(name, cfg=None):
    sc = compile_scene(snapshot(name, cfg))
    assert scene_errors(sc) == [], scene_errors(sc)
    return sc


def zone(sc, zid):
    return next(z for z in sc["zones"] if z["id"] == zid)


class Compiler(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(compile_scene(snapshot("demo-t2")), compile_scene(snapshot("demo-t2")))

    def test_every_fixture_compiles_to_a_valid_scene(self):
        for path in sorted((ROOT / "fixtures/observations").glob("*.json")):
            with self.subTest(fixture=path.stem):
                self.assertEqual(scene_errors(compile_scene(snapshot(path.stem))), [])

    def test_1_quiet_project(self):
        sc = scene("m1-empty")
        self.assertTrue(all(z["state"] == "quiet" for z in sc["zones"]))
        self.assertEqual((sc["nodes"], sc["edges"], sc["attention"]), ([], [], []))

    def test_1b_landed_work_without_relationships_is_not_drawn(self):
        """e6: only pushes to main, no in-flight work: the map stays quiet but lists what changed."""
        sc = scene("e6-direct-pushes")
        self.assertEqual(sc["nodes"], [])
        self.assertIn("app/game", zone(sc, "build")["recently_changed"])

    def test_2_two_active_areas_in_different_lanes(self):
        sc = scene("demo-t3")
        self.assertEqual({z["id"] for z in sc["zones"] if z["state"] == "active"}, {"build", "verify"})

    def test_3_high_confidence_overlap(self):
        sc = scene("demo-t2")
        [edge] = sc["edges"]
        self.assertEqual((edge["type"], edge["confidence"], edge["files"]), ("overlap", "high", ["src/conversation/store.py"]))
        group = next(g for g in sc["groups"] if g["path"] == "src/conversation")
        self.assertTrue(group["attention"])
        self.assertEqual(sc["attention"][0]["target"], edge["id"])

    def test_4_waiting_dependency_is_directed(self):
        [edge] = scene("demo-t3")["edges"]
        self.assertEqual((edge["type"], edge["from"], edge["to"], edge["directed"]), ("waiting", "pr:44", "pr:41", True))

    def test_5_multiple_overlaps_in_one_area(self):
        sc = scene("m2-crowded-area")
        overlaps = [e for e in sc["edges"] if e["type"] == "overlap"]
        self.assertEqual(len(overlaps), 3)
        self.assertTrue(all(e["areas"] == ["src/editor"] for e in overlaps))
        group = next(g for g in sc["groups"] if g["path"] == "src/editor")
        self.assertEqual(sorted(group["nodes"]), ["pr:70", "pr:71", "pr:72"])

    def test_6_custom_lanes_recompose_the_map(self):
        sc = scene("m3-ml-project", ML)
        self.assertEqual([z["label"] for z in sc["zones"]], ["Data", "Pipeline", "Model", "Eval", "API", "Docs"])
        self.assertEqual(zone(sc, "data")["state"], "quiet")
        # #80 changes pipeline and model; drawn once, where it changes the most files (tie -> earlier lane)
        n80 = next(n for n in sc["nodes"] if n["id"] == "pr:80")
        self.assertEqual((n80["zone"], n80["also_touches"]), ("pipeline", ["model"]))
        kinds = sorted(e["type"] for e in sc["edges"])
        self.assertEqual(kinds, ["overlap", "waiting"])

    def test_7_empty_lanes_are_quiet(self):
        sc = scene("demo-t2")
        self.assertEqual([z["id"] for z in sc["zones"] if z["state"] == "quiet"], ["intent", "verify", "ship"])

    def test_8_long_labels_survive_intact(self):
        sc = scene("m4-long-labels")
        self.assertTrue(any(len(n["label"]) > 150 for n in sc["nodes"]))
        deep = "packages/compiler/src/incremental/cache/invalidation/content_hash_strategy.ts"
        self.assertEqual([g["path"] for g in sc["groups"]], ["packages/compiler"])  # grouped by area, not by file
        self.assertIn(deep, sc["details"]["work_items"]["pr:90"]["paths"])       # full path kept for the inspector
        branch = next(n for n in sc["nodes"] if n["kind"] == "branch")
        self.assertTrue(branch["label"].startswith("experiments/very-long-branch-name"))

    def test_10_self_observation(self):
        snap = json.loads((ROOT / "docs/demo/self/data/snapshot.json").read_text())
        sc = compile_scene(snap)
        self.assertEqual(scene_errors(sc), [])
        self.assertEqual([z["label"] for z in sc["zones"]][:5], ["Model", "Engine", "Evidence", "Integration", "Contract"])
        [node] = sc["nodes"]  # one branch, drawn once, referenced in every other area it touches
        self.assertEqual(sum(node["id"] in g["also_active"] for g in sc["groups"]), len(node["also_touches"]))

    def test_node_drawn_once_in_primary_area(self):
        sc = scene("demo-t2")
        placed = [n for g in sc["groups"] for n in g["nodes"]]
        self.assertEqual(len(placed), len(set(placed)))

    def test_stale_work_recedes_but_is_attention(self):
        sc = scene("e3-stale")
        stale = [n for n in sc["nodes"] if n["status"] == "stale"]
        self.assertEqual({n["id"] for n in stale}, {"branch:old-spike", "pr:9"})
        self.assertEqual([a["kind"] for a in sc["attention"]], ["stale", "stale"])


class Renderer(unittest.TestCase):
    def test_nodes_groups_and_zones_are_focusable_buttons(self):
        page = render_map(scene("demo-t2"))
        for nid in ("pr:41", "pr:42", "pr:43"):
            self.assertIn(f'data-kind="node" data-id="{nid}"', page)
        self.assertIn('data-kind="group" data-id="area:src/conversation"', page)
        self.assertEqual(page.count('<article class="zone'), 4)

    def test_text_is_escaped_and_embedded_json_cannot_close_the_script(self):
        snap = snapshot("demo-t2")
        next(w for w in snap["work_items"] if w["id"] == "pr:43")["title"] = '</script><img src=x onerror=alert(1)>'
        page = render_map(compile_scene(snap))
        self.assertNotIn("<img src=x", page)
        self.assertEqual(page.count("</script>"), 2)  # the scene JSON block and the inline script

    def test_quiet_zones_render_compactly(self):
        page = render_map(scene("m1-empty"))
        self.assertEqual(page.count('class="zone quiet'), 4)
        self.assertIn("Nothing needs a conversation right now.", page)

    def test_crowded_areas_collapse(self):
        snap = snapshot("m2-crowded-area")
        page = render_map(compile_scene(snap))
        self.assertNotIn('class="more"', page)  # 3 nodes fit
        many = json.loads(json.dumps(snap))
        base = next(w for w in many["work_items"] if w["id"] == "pr:70")
        for i in range(6):
            many["work_items"].append(dict(base, id=f"pr:{100 + i}", number=100 + i))
        self.assertIn('<details class="more"><summary>4 more</summary>', render_map(compile_scene(many)))

    def test_narrow_layout_and_reduced_motion_rules_exist(self):
        page = render_map(scene("demo-t2"))
        self.assertIn("@media (max-width:760px)", page)
        self.assertIn("prefers-reduced-motion", page)

    def test_dense_maps_keep_connectors_readable(self):
        page = render_map(compile_scene(snapshot("e1-same-subsystem")))
        self.assertIn("const HUB = 3", page)                        # busy cards get a count, lines on selection
        self.assertIn("details:not([open])", page)                  # collapsed cards anchor on their summary
        self.assertIn("dataset.bundle", page)                       # lines to collapsed work are bundled

    def test_designed_states_are_below_the_hub_threshold(self):
        # the rule only changes busy real repositories: every synthetic scene draws exactly what it did before
        import json
        from tests.helpers import ROOT
        for path in list((ROOT / "demo/states").glob("*.scene.json")) + list((ROOT / "demo/playground").glob("[!r]*.scene.json")):
            scene, degree = json.loads(path.read_text()), {}
            for e in scene["edges"]:
                for end in (e["from"], e["to"]):
                    degree[end] = degree.get(end, 0) + 1
            self.assertLessEqual(max(degree.values(), default=0), 3, path.name)

    def test_no_person_metrics_on_the_page(self):
        page = render_map(scene("m2-crowded-area")).lower()
        for word in ("leaderboard", "productivity", "score", "velocity"):
            self.assertIsNone(re.search(rf"\b{word}\b", page))


if __name__ == "__main__":
    unittest.main()
