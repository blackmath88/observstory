"""Signal experiments (docs/development/experiment-results.md). Each test is one falsifiable claim."""

import unittest

from tests.helpers import of_type, snapshot


class OverlapExperiments(unittest.TestCase):
    def test_two_contributors_same_subsystem(self):
        """E1: a PR and an unproposed branch in src/conversation give an overlap before either merges."""
        snap = snapshot("e1-same-subsystem")
        [sig] = of_type(snap, "overlap")
        self.assertEqual(sig["subject"], {"kind": "area", "id": "src/conversation"})
        self.assertEqual(sig["work_items"], ["branch:sofia/convo-rewrite", "pr:14"])
        self.assertEqual(sig["confidence"], "high")
        self.assertEqual(sig["basis"], "derived")
        files = [e["ref"] for e in sig["evidence"] if e["kind"] == "file"]
        self.assertEqual(files, ["src/conversation/store.py"])
        self.assertTrue(all(e.get("url") for e in sig["evidence"] if e["kind"] == "work_item"))

    def test_parallel_non_overlapping(self):
        """E2: three items in three areas give no overlap signal."""
        snap = snapshot("e2-parallel")
        self.assertEqual(of_type(snap, "overlap"), [])
        self.assertEqual(snap["summary"]["areas_active"], 4)  # src/billing, src/search, docs, README.md

    def test_without_container_awareness_parallel_work_falsely_overlaps(self):
        """E2 control: collapsing src/* into one area creates a false area-only overlap. Two safeguards
        prevent it: container-aware areas (ADR-012) and, by default, the shared-file requirement (ADR-019)."""
        area_mode = {"containers": [], "signals": {"overlap_require_shared_file": False}}
        self.assertEqual([s["subject"]["id"] for s in of_type(snapshot("e2-parallel", area_mode), "overlap")], ["src"])
        self.assertEqual(of_type(snapshot("e2-parallel", {"containers": []}), "overlap"), [])

    def test_area_only_overlap_needs_opt_in(self):
        """Precision study: area-only pairs were useful in 4 of 39 labelled cases."""
        snap = snapshot("e1-same-subsystem")
        [sig] = of_type(snap, "overlap")
        self.assertTrue(sig["rule"]["params"]["require_shared_file"])
        self.assertTrue(all(e["kind"] != "file" or e["ref"] == "src/conversation/store.py" for e in sig["evidence"]))

    def test_bot_only_work_does_not_take_part(self):
        from tests.helpers import observations
        from observstory import config, derive
        obs = observations("e1-same-subsystem")
        for c in obs["pull_requests"][0]["commits"]:
            c["author"] = {"login": "renovate[bot]", "type": "Bot"}
        obs["pull_requests"][0]["author"] = {"login": "renovate[bot]", "type": "Bot"}
        snap = derive.derive(obs, config.normalise(None), derive.parse_time(obs["fetched_at"]))
        self.assertEqual(of_type(snap, "overlap"), [])

    def test_direct_pushes_are_sequential_not_parallel(self):
        """E6, revised by issue #2: pushes to one branch are sequential; each contains the last. No overlap."""
        snap = snapshot("e6-direct-pushes")
        self.assertEqual(of_type(snap, "overlap"), [])
        area = next(a for a in snap["areas"] if a["id"] == "app/game")
        self.assertEqual(area["in_flight"], ["direct:alice", "direct:sofia"])  # activity is still visible

    def test_stacked_prs_are_not_overlap(self):
        """E4 finding: a stacked PR shares ground with its base by design; do not flag it."""
        snap = snapshot("e4-waiting")
        self.assertEqual(of_type(snap, "overlap"), [])

    def test_stale_work_does_not_take_part_in_overlap(self):
        """Precision study: 81% of overlap pairs on real repos involved work idle > stale_hours."""
        snap = snapshot("p1-stale-excluded")
        self.assertEqual(of_type(snap, "overlap"), [])
        self.assertEqual([s["subject"]["id"] for s in of_type(snap, "stale")], ["branch:ben/old-parser"])
        revived = snapshot("p1-stale-excluded", {"signals": {"stale_hours": 400}})
        [sig] = of_type(revived, "overlap")
        self.assertEqual(sig["rule"]["params"]["excluded_stale"], [])

    def test_stack_explains_shared_ground_transitively(self):
        """Precision study: #62 -> #61 -> #60 is one stack; only ben's unrelated PR #63 is parallel to it."""
        snap = snapshot("p2-transitive-stack")
        [sig] = of_type(snap, "overlap")
        pairs = sig["rule"]["params"]["parallel_pairs"]
        self.assertTrue(all("pr:63" in p for p in pairs))
        self.assertEqual(sorted(sig["rule"]["params"]["explained_by_waiting"]), ["pr:61", "pr:62"])
        self.assertEqual(len(of_type(snap, "waiting")), 2)

    def test_threshold_is_configurable_and_echoed(self):
        snap = snapshot("e1-same-subsystem", {"signals": {"overlap_min_work_items": 3}})
        self.assertEqual(of_type(snap, "overlap"), [])
        self.assertEqual(snap["config"]["signals"]["overlap_min_work_items"], 3)


class StaleExperiments(unittest.TestCase):
    def test_stale_branch_without_pr(self):
        """E3: a branch idle for 6 days with no PR is stale and says so."""
        snap = snapshot("e3-stale")
        by_subject = {s["subject"]["id"]: s for s in of_type(snap, "stale")}
        self.assertIn("branch:old-spike", by_subject)
        self.assertIn("no pull request", by_subject["branch:old-spike"]["summary"])
        self.assertEqual(by_subject["pr:9"]["confidence"], "low")  # drafts are often parked on purpose

    def test_recent_work_not_stale(self):
        snap = snapshot("e3-stale")
        self.assertNotIn("pr:10", {s["subject"]["id"] for s in of_type(snap, "stale")})


class WaitingExperiments(unittest.TestCase):
    def test_pr_waiting_on_stacked_base(self):
        """E4: #21's base is #20's head branch."""
        sigs = {s["id"]: s for s in of_type(snapshot("e4-waiting"), "waiting")}
        self.assertEqual(sigs["waiting:pr:21:pr:20"]["basis"], "derived")

    def test_pr_waiting_declared_in_body(self):
        """E4: #22 says 'Depends on #20'."""
        snap = snapshot("e4-waiting")
        sigs = {s["id"]: s for s in of_type(snap, "waiting")}
        self.assertEqual(sigs["waiting:pr:22:pr:20"]["basis"], "declared")
        pr22 = next(w for w in snap["work_items"] if w["id"] == "pr:22")
        self.assertEqual(pr22["waiting_on"], ["pr:20"])


class BurstExperiments(unittest.TestCase):
    def test_agent_rapid_commit_burst(self):
        """E5: 24 commits in ~40 min with an agent trailer give a burst on the work item, high confidence."""
        snap = snapshot("e5-burst")
        [sig] = of_type(snap, "burst")
        self.assertEqual(sig["subject"], {"kind": "work_item", "id": "pr:30"})
        self.assertEqual(sig["confidence"], "high")
        pr30 = next(w for w in snap["work_items"] if w["id"] == "pr:30")
        self.assertTrue(pr30["agent_declared"])
        self.assertGreaterEqual(pr30["burst"]["commits"], 8)

    def test_human_paced_commits_no_burst(self):
        snap = snapshot("e5-burst")
        self.assertNotIn("pr:31", {s["subject"]["id"] for s in of_type(snap, "burst")})

    def test_closed_work_is_not_folded(self):
        """demo-t3 finding: closed PR #43 no longer produces a burst signal."""
        self.assertEqual(of_type(snapshot("demo-t3"), "burst"), [])


class DemoScenario(unittest.TestCase):
    def test_overlap_emerges_and_resolves(self):
        counts = [len(of_type(snapshot(f"demo-t{i}"), "overlap")) for i in range(4)]
        self.assertEqual(counts, [0, 1, 1, 0])

    def test_resolution_is_a_declared_dependency(self):
        [sig] = of_type(snapshot("demo-t3"), "waiting")
        self.assertEqual(sig["work_items"], ["pr:44", "pr:41"])


if __name__ == "__main__":
    unittest.main()
