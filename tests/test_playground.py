"""Semantic UI Playground: semantic specs -> real pipeline -> the map shows what the controls promise."""

import json
import re
import sys
import unittest

from observstory import config
from observstory.derive import derive
from observstory.map_compiler import compile_scene, explain_frame
from observstory.validate import scene_errors, validate
from tests.helpers import ROOT

sys.path.insert(0, str(ROOT / "fixtures"))
import playground as pg  # noqa: E402

OUT = ROOT / "demo/playground"
_cache = {}


def run(sid):
    if sid not in _cache:
        spec = dict(zip(("shape", "relation", "volume", "collab"), sid.split(".")))
        snap = derive(pg.observations(spec), config.normalise(pg.config(spec)), pg.NOW,
                      coordination=pg.declarations(spec), coordination_source=".observstory/coordination.json")
        _cache[sid] = (snap, compile_scene(snap))
    return _cache[sid]


class Matrix(unittest.TestCase):
    def test_matrix_is_small_and_unique(self):
        ids = [pg.state_id(s) for s in pg.matrix()]
        self.assertEqual(len(ids), 42)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(all(s["collab"] == "none" for s in pg.matrix() if s["shape"] != "hackathon"))

    def test_every_state_is_valid(self):
        for spec in pg.matrix():
            with self.subTest(state=pg.state_id(spec)):
                snap, scene = run(pg.state_id(spec))
                self.assertEqual(validate(snap) + scene_errors(scene), [])
                self.assertEqual(scene["status"]["in_flight"], pg.VOLUMES[spec["volume"]])

    def test_shape_recomposes_the_lanes(self):
        lanes = {shape: [z["label"] for z in sorted(run(f"{shape}.parallel.high.none")[1]["zones"], key=lambda z: z["order"])]
                 for shape in pg.SHAPES}
        self.assertEqual(lanes["software"], ["Intent", "Build", "Verify", "Ship"])
        self.assertEqual(lanes["ml"], ["Data", "Pipeline", "Model", "Eval", "API", "Docs"])
        self.assertEqual(lanes["hackathon"], ["Intent", "Core", "Interface", "Verify"])

    def test_relations_change_the_compiled_structure(self):
        for shape in pg.SHAPES:
            for vol in pg.VOLUMES:
                with self.subTest(shape=shape, volume=vol):
                    get = lambda rel: run(f"{shape}.{rel}.{vol}.none")[1]  # noqa: E731
                    self.assertEqual(get("parallel")["edges"], [])
                    self.assertEqual(get("parallel")["attention"], [])
                    [ov] = get("overlap")["edges"]
                    self.assertEqual((ov["type"], {ov["from"], ov["to"]}), ("overlap", {"pr:10", "pr:11"}))
                    [wt] = get("waiting")["edges"]
                    self.assertEqual((wt["type"], wt["from"], wt["to"]), ("waiting", "pr:11", "pr:10"))
                    node = lambda rel: next(n for n in get(rel)["nodes"] if n["id"] == "pr:11")  # noqa: E731
                    self.assertEqual(node("stale")["status"], "stale")
                    self.assertIn("burst", node("burst")["flags"])

    def test_the_rail_appears_only_when_something_is_declared(self):
        for spec in pg.matrix():
            with self.subTest(state=pg.state_id(spec)):
                self.assertEqual(run(pg.state_id(spec))[1].get("coordination") is not None, spec["collab"] != "none")

    def test_collaboration_variants_mean_what_they_say(self):
        rules = lambda sid: sorted(q["rule"] for q in run(sid)[0]["coordination"]["cues"])  # noqa: E731
        self.assertEqual(rules("hackathon.parallel.high.freeze"), [])
        nxt = run("hackathon.parallel.high.freeze")[1]["coordination"]
        self.assertEqual(next(g["kind"] for g in run("hackathon.parallel.high.freeze")[0]["coordination"]["gates"]
                              if g["id"] == nxt["next_gate"]), "freeze")
        self.assertEqual(rules("hackathon.parallel.low.conflict"), ["freeze.changed_after"])
        self.assertEqual(rules("hackathon.parallel.low.commitment"), ["commitment.unstarted"])   # no evals work at 2 in flight
        self.assertEqual(rules("hackathon.parallel.high.commitment"), [])                       # the evals PR exists at 6


class WhyThisFrame(unittest.TestCase):
    def test_explanations_follow_the_scene(self):
        why = lambda sid: " ".join(explain_frame(run(sid)[1]))  # noqa: E731
        self.assertIn("Data → Pipeline → Model → Eval → API → Docs", why("ml.parallel.low.none"))
        self.assertIn("nothing asks for attention", why("software.parallel.low.none"))
        self.assertIn("both change src/auth/session.py in parallel", why("software.overlap.low.none"))
        self.assertIn("#11 waits on #10", why("software.waiting.low.none"))
        self.assertIn("gone quiet", why("software.stale.low.none"))
        self.assertIn("machine-paced", why("software.burst.low.none"))
        self.assertIn("no mission rail", why("hackathon.overlap.low.none"))
        self.assertIn("changed afterwards", why("hackathon.overlap.low.conflict"))

    def test_explanations_name_work_not_people(self):
        for spec in pg.matrix():
            text = " ".join(explain_frame(run(pg.state_id(spec))[1]))
            self.assertIsNone(re.search(r"\b(" + "|".join(pg.PEOPLE) + r")\b", text, re.I), pg.state_id(spec))


class BuiltPlayground(unittest.TestCase):
    def manifest(self):
        text = (ROOT / "demo/playground.html").read_text()
        return text, json.loads(re.search(r'<script type="application/json" id="states">(.*?)</script>', text, re.S).group(1))

    def test_every_state_is_generated_and_current(self):
        _, manifest = self.manifest()
        self.assertEqual([m["id"] for m in manifest], [pg.state_id(s) for s in pg.matrix()])
        for m in manifest:
            with self.subTest(state=m["id"]):
                stored = json.loads((OUT / f'{m["id"]}.scene.json').read_text())
                self.assertEqual(stored, json.loads(json.dumps(run(m["id"])[1])))   # rebuild after engine changes
                self.assertEqual(m["why"], explain_frame(stored))
                self.assertTrue((OUT / f'{m["id"]}.snapshot.json').exists() and (OUT / f'{m["id"]}.html').exists())

    def test_shell_is_static_offline_and_has_no_layout_controls(self):
        text, _ = self.manifest()
        self.assertIsNone(re.search(r"<script[^>]+src=|fetch\(|XMLHttpRequest", text))
        for axis in ('name="shape"', 'name="relation"', 'name="volume"', 'name="collab"'):
            self.assertIn(axis, text)
        self.assertIsNone(re.search(r'type="(range|color|number)"', text))
        self.assertIn('href="index.html"', text)
        self.assertIn('href="playground.html"', (ROOT / "demo/index.html").read_text())

    def test_synthetic_data_links_nowhere(self):
        for spec in pg.matrix():
            self.assertNotIn("http", json.dumps(pg.observations(spec)))


if __name__ == "__main__":
    unittest.main()
