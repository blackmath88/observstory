import unittest

from observstory import query
from tests.helpers import snapshot


class AgentQueries(unittest.TestCase):
    def test_work_near_proposed_task(self):
        ans = query.work_near(snapshot("demo-t2"), ["src/conversation/store.py"])
        ids = {w["id"] for w in ans["answer"]["in_flight"]}
        self.assertEqual(ids, {"pr:41", "pr:43"})
        self.assertTrue(ans["answer"]["coordination_needed"])
        self.assertEqual(ans["answer"]["exact_file_matches"], ["src/conversation/store.py"])
        self.assertTrue(any(s["type"] == "overlap" for s in ans["signals"]))

    def test_work_near_quiet_area(self):
        ans = query.work_near(snapshot("demo-t2"), ["src/billing"])
        self.assertFalse(ans["answer"]["coordination_needed"])

    def test_changes_since(self):
        snap = snapshot("demo-t3")
        ans = query.changes_since(snap, "2026-09-22T12:00:00Z")
        self.assertIn("pr:44", {w["id"] for w in ans["answer"]["work_items"]})

    def test_open_loops_and_handoff(self):
        snap = snapshot("demo-t3")
        loops = query.open_loops(snap)["answer"]
        self.assertEqual(loops["waiting"], [{"work_item": "pr:44", "waits_on": "pr:41", "basis": "declared"}])
        hand = query.handoff(snap)["answer"]
        self.assertEqual([w["id"] for w in hand["ready_for_review"]], ["pr:41"])

    def test_envelope_is_uniform(self):
        snap = snapshot("e1-same-subsystem")
        for name, fn in query.QUERIES.items():
            args = {"changes-since": ("2026-01-01T00:00:00Z",), "work-near": (["src"],)}.get(name, ())
            ans = fn(snap, *args)
            self.assertEqual(set(ans), {"query", "args", "as_of", "repository", "answer", "signals", "evidence_note"})


if __name__ == "__main__":
    unittest.main()
