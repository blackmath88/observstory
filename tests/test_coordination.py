"""Collaboration state (issue #7): extraction proposes, a person declares, reconciliation compares."""

import copy
import json
import sys
import unittest

from observstory import config
from observstory import coordination as co
from observstory.derive import derive, parse_time
from observstory.validate import validate
from tests.helpers import ROOT

sys.path.insert(0, str(ROOT / "fixtures"))
import collab_lab  # noqa: E402

DIR = ROOT / "fixtures/collab-lab"
FULL = json.loads((DIR / "coordination.json").read_text())
CFG = json.loads((DIR / "voice-notes.config.json").read_text())


def moment(name, data=None):
    obs = json.loads((DIR / f"{name}.json").read_text())
    now = parse_time(obs["fetched_at"])
    snap = derive(obs, config.normalise(CFG), now, coordination=co.as_of(data or FULL, now))
    return snap, snap["coordination"]


def rules(c):
    return sorted(q["rule"] for q in c["cues"])


class Extraction(unittest.TestCase):
    def test_markers_become_proposed_items_with_their_source_line(self):
        out = co.extract(collab_lab.KICKOFF_NOTES, "S1", "2026-10-02T18:30:00Z")
        self.assertEqual([g["kind"] for g in out["gates"]], ["checkpoint", "freeze", "freeze", "submission"])
        self.assertEqual(out["gates"][1]["areas"], ["src/core/"])
        self.assertEqual(out["gates"][1]["at"], "2026-10-03T12:00:00Z")          # "Sat 12:00"
        self.assertEqual(out["gates"][0]["at"], "2026-10-03T00:00:00Z")          # "00:00" -> next occurrence
        c = out["commitments"][3]
        self.assertEqual((c["owner"], c["due"], c["links"]), ("Dana", "2026-10-03T16:00:00Z", [{"kind": "path", "ref": "evals/"}]))
        self.assertEqual(out["commitments"][0]["source"]["line"], 6)
        self.assertEqual(out["open_questions"], ["do we need speaker labels for the demo"])

    def test_chatter_is_ignored(self):
        out = co.extract("Pizza at 20:00.\nwe should probably freeze soon", "S1", "2026-10-02T18:30:00Z")
        self.assertEqual(sum(len(v) for v in out.values()), 0)

    def test_link_kinds(self):
        out = co.extract("@Ben: adapter [#12, branch:ben/x, src/t/, https://tracker.example/T-4]", "S1", "2026-10-02T18:30:00Z")
        self.assertEqual([l["kind"] for l in out["commitments"][0]["links"]], ["pr", "branch", "path", "url"])


class Confirmation(unittest.TestCase):
    def test_everything_starts_proposed(self):
        data = co.empty()
        co.propose(data, collab_lab.KICKOFF_NOTES, "Kickoff", "2026-10-02T18:30:00Z")
        items = data["gates"] + data["commitments"] + data["decisions"]
        self.assertTrue(items and all(x["status"] == "proposed" and x["confirmed_by"] is None for x in items))

    def test_confirm_needs_a_name_and_can_keep_or_drop(self):
        data = co.empty()
        sid = co.propose(data, collab_lab.KICKOFF_NOTES, "Kickoff", "2026-10-02T18:30:00Z")
        with self.assertRaises(ValueError):
            co.confirm(data, sid, by="  ", at="2026-10-02T19:00:00Z")
        co.confirm(data, sid, by="Alice", at="2026-10-02T19:00:00Z", drop={"C4"})
        self.assertNotIn("C4", [c["id"] for c in data["commitments"]])
        self.assertTrue(all(x["status"] == "declared" and x["confirmed_by"] == "Alice"
                            for x in data["gates"] + data["commitments"] + data["decisions"]))
        self.assertEqual(co.validate(data), [])

    def test_proposed_items_are_ignored(self):
        data = co.empty()
        co.propose(data, "FREEZE src/core/ at 12:00\n@Dana: evals (by 13:00) [evals/]", "Draft", "2026-10-03T09:00:00Z")
        _, c = moment("after-core-freeze", data)
        self.assertEqual((c["gates"], c["commitments"], c["cues"]), ([], [], []))
        self.assertEqual(c["proposed_pending"], 2)

    def test_declared_without_confirmer_is_invalid(self):
        bad = copy.deepcopy(FULL)
        bad["gates"][0]["confirmed_by"] = None
        self.assertTrue(any("confirmed_by" in e for e in co.validate(bad)))

    def test_fixture_file_matches_the_real_flow(self):
        self.assertEqual(collab_lab.declarations(), FULL)


class Reconciliation(unittest.TestCase):
    def test_kickoff_has_no_cues_and_the_next_gate(self):
        _, c = moment("kickoff")
        self.assertEqual(c["cues"], [])
        self.assertEqual([g["label"] for g in c["gates"] if g["next"]], ["Skeleton demo"])
        self.assertEqual({x["state"] for x in c["commitments"]}, {"not_started"})

    def test_commitment_states_follow_linked_work(self):
        _, c = moment("saturday-morning")
        states = {x["id"]: (x["state"], x["matched"]) for x in c["commitments"]}
        self.assertEqual(states["C1"], ("landed", ["pr:10"]))       # path link, merged PR
        self.assertEqual(states["C5"], ("in_progress", ["pr:12"]))  # explicit #12 link
        self.assertEqual(states["C4"], ("not_started", []))

    def test_unstarted_commitment_cue_after_half_the_time(self):
        _, c = moment("saturday-morning")
        [cue] = c["cues"]
        self.assertEqual((cue["rule"], cue["subject"]), ("commitment.unstarted", {"kind": "commitment", "id": "C4"}))

    def test_freeze_changed_after(self):
        _, c = moment("after-core-freeze")
        cue = next(q for q in c["cues"] if q["rule"] == "freeze.changed_after")
        self.assertEqual(sorted(cue["observed"]["work_items"]), ["direct:alice", "pr:12"])
        self.assertEqual(cue["confidence"], "medium")  # #12 is judged by its overall paths
        self.assertNotIn("alice", cue["summary"])      # names the change, not the person

    def test_scoped_freeze_ignores_commitments_outside_its_areas(self):
        _, c = moment("feature-freeze")
        open_work = [q["subject"]["id"] for q in c["cues"] if q["rule"] == "gate.passed_with_open_work"]
        self.assertEqual(open_work, ["C3"])  # recorder UI in web/; Dana's evals/ are outside web/, src/

    def test_a_moment_only_sees_check_ins_that_had_happened(self):
        _, c = moment("kickoff")
        self.assertEqual([s["id"] for s in c["sessions"]], ["S1"])
        self.assertEqual(c["proposed_pending"], 0)

    def test_cue_has_both_sides(self):
        for m in ("saturday-morning", "after-core-freeze", "feature-freeze"):
            for q in moment(m)[1]["cues"]:
                self.assertTrue(q["declared"] and q["declared"].get("confirmed_by"))
                self.assertIn("work_items", q["observed"])
                self.assertIn(q["subject"]["kind"], ("gate", "commitment"))

    def test_cues_never_enter_repository_signals(self):
        snap, _ = moment("after-core-freeze")
        self.assertEqual(validate(snap), [])
        self.assertTrue(all(s["type"] in ("overlap", "stale", "waiting", "burst") for s in snap["signals"]))

    def test_no_coordination_file_means_no_section(self):
        obs = json.loads((DIR / "kickoff.json").read_text())
        snap = derive(obs, config.normalise(CFG), parse_time(obs["fetched_at"]))
        self.assertIsNone(snap["coordination"])


if __name__ == "__main__":
    unittest.main()
