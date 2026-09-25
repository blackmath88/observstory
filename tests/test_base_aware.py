"""Issue #2: overlap is base-aware. Changes already in a work item's merge base are baseline, not
parallel work. Decided from merge-base SHAs and parent links, never from timestamps alone."""

import unittest

from tests.helpers import of_type, snapshot


def overlap(name):
    sigs = of_type(snapshot(name), "overlap")
    return sigs[0] if sigs else None


def base_details(sig):
    return [e["detail"] for e in sig["evidence"] if e["kind"] == "base"]


class BaseAwareOverlap(unittest.TestCase):
    def test_main_change_before_branch_base_is_baseline(self):
        """Case 1: bob branched from m3; every README push is in his base."""
        self.assertIsNone(overlap("b1-baseline"))

    def test_main_change_after_divergence_is_overlap(self):
        """Case 2: m3 landed after bob diverged at m2."""
        sig = overlap("b2-after-divergence")
        self.assertEqual(sig["work_items"], ["branch:bob/readme", "direct:alice"])
        self.assertEqual(sig["confidence"], "high")
        [detail] = base_details(sig)
        self.assertIn("diverged at m200000 (compare)", detail)

    def test_mixed_same_file_cites_only_post_divergence_commits(self):
        """Case 3: README changed at m1 (baseline) and at m3 (after divergence); only m3 is evidence."""
        [detail] = base_details(overlap("b2-after-divergence"))
        self.assertIn("m300000", detail)
        self.assertNotIn("m100000", detail)

    def test_rebase_moves_the_base(self):
        """Case 4a: after rebasing onto m3 the overlap disappears."""
        self.assertIsNotNone(overlap("b2-after-divergence"))
        self.assertIsNone(overlap("b3-rebased"))

    def test_merging_main_into_branch_uses_compare_merge_base(self):
        """Case 4b: compare knows about the merge of main into the branch."""
        self.assertIsNone(overlap("b4-merged-main-in"))

    def test_first_parent_fallback_is_labelled_and_down_weighted(self):
        """Case 4b under budget fallback: first-commit parent (m1) over-reports; the evidence says so."""
        sig = overlap("b4-merged-main-in-first-parent")
        self.assertEqual(sig["confidence"], "medium")
        self.assertIn("(first_parent)", base_details(sig)[0])

    def test_squash_merged_pr_is_not_a_direct_push(self):
        """Case 4c: the squash commit belongs to pr:12 (merged), and it is in bob's base anyway."""
        snap = snapshot("b5-squash-merged")
        self.assertIsNone(overlap("b5-squash-merged"))
        commit = next(c for c in snap["commits"] if c["sha"].startswith("m4"))
        self.assertEqual(commit["work_item"], "pr:12")

    def test_base_before_window_means_everything_observed_is_later(self):
        sig = overlap("b6-base-before-window")
        self.assertIn("before every observed commit", base_details(sig)[0])

    def test_unknown_base_is_parallel_but_says_why(self):
        sig = overlap("b7-base-unresolved")
        self.assertEqual(sig["confidence"], "medium")
        self.assertIn("merge base of branch:bob/readme is unknown", base_details(sig)[0])

    def test_in_flight_pairs_unaffected(self):
        """Two unmerged work items are parallel by construction (E1 still holds)."""
        sig = overlap("e1-same-subsystem")
        self.assertEqual(sig["rule"]["params"]["parallel_pairs"], ["branch:sofia/convo-rewrite|pr:14"])


if __name__ == "__main__":
    unittest.main()
