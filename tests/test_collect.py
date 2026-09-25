"""Collector against a fake GitHub: normalisation, PR-head exclusion, and budget degradation."""

import datetime as dt
import unittest

from observstory import config
from observstory.collect import collect
from observstory.derive import derive
from observstory.github import BudgetExhausted
from observstory.validate import validate

NOW = dt.datetime(2026, 9, 21, 12, 0, tzinfo=dt.timezone.utc)
R = "/repos/o/r"


def commit(sha, login, date, msg="change"):
    return {"sha": sha, "html_url": f"https://github.com/o/r/commit/{sha}", "author": {"login": login, "type": "User"},
            "commit": {"author": {"name": login, "date": date}, "message": msg}}


ROUTES = {
    R: {"html_url": "https://github.com/o/r", "default_branch": "main", "visibility": "public"},
    f"{R}/commits": [commit("a1", "alice", "2026-09-21T10:00:00Z", "Add memory (#7)"),
                     commit("b2", "ben", "2026-09-21T09:00:00Z")],
    f"{R}/commits/a1": {"files": [{"filename": "src/chat/memory.py"}]},
    f"{R}/commits/b2": {"files": [{"filename": "docs/x.md"}]},
    f"{R}/pulls": [
        {"number": 8, "title": "Chat store", "body": "", "state": "open", "draft": False, "merged_at": None,
         "head": {"ref": "sofia/store", "repo": {"full_name": "o/r"}}, "base": {"ref": "main"},
         "user": {"login": "sofia", "type": "User"}, "created_at": "2026-09-21T08:00:00Z",
         "updated_at": "2026-09-21T11:00:00Z", "html_url": "https://github.com/o/r/pull/8",
         "requested_reviewers": [{"login": "alice"}], "requested_teams": []},
        {"number": 7, "title": "Memory", "state": "closed", "merged_at": "2026-09-21T10:00:00Z",
         "head": {"ref": "alice/memory", "repo": {"full_name": "o/r"}}, "base": {"ref": "main"},
         "user": {"login": "alice"}, "updated_at": "2026-09-21T10:00:00Z", "html_url": "https://github.com/o/r/pull/7"},
    ],
    f"{R}/pulls/8/files": [{"filename": "src/chat/memory.py"}, {"filename": "package-lock.json"}],
    f"{R}/pulls/8/commits": [commit("c3", "sofia", "2026-09-21T11:00:00Z")],
    f"{R}/compare/main...sofia/store": {"merge_base_commit": {"sha": "b2"}},
    f"{R}/branches": [{"name": "main"}, {"name": "sofia/store"}, {"name": "alice/memory"}, {"name": "ben/spike"}],
    f"{R}/compare/main...ben/spike": {"ahead_by": 2, "files": [{"filename": "src/chat/ui.py"}],
                                      "commits": [commit("d4", "ben", "2026-09-20T12:00:00Z")]},
    f"{R}/issues": [{"number": 3, "title": "Bug", "state": "open", "html_url": "u", "labels": [{"name": "bug"}]},
                    {"number": 8, "title": "PR as issue", "state": "open", "pull_request": {}}],
}


class FakeClient:
    def __init__(self, budget=None):
        self.calls, self.remaining, self.budget, self.paths = 0, 1000, budget, []

    def get(self, path, params=None, *, essential=False):
        if not essential and self.budget is not None and self.calls >= self.budget:
            raise BudgetExhausted(path)
        self.calls += 1
        self.paths.append(path)
        return ROUTES[path]


class Collector(unittest.TestCase):
    def test_normalises_and_skips_pr_heads(self):
        obs = collect(FakeClient(), "o/r", config.normalise(None), NOW)
        self.assertEqual([b["name"] for b in obs["branches"]], ["ben/spike"])  # merged PR's branch excluded
        self.assertEqual(obs["pull_requests"][0]["requested_reviewers"], ["alice"])
        self.assertEqual(obs["meta"]["degraded"], [])
        self.assertEqual(obs["pull_requests"][0]["merge_base"], {"sha": "b2", "source": "compare"})
        snap = derive(obs, config.normalise(None), NOW)
        self.assertEqual(validate(snap), [])
        ids = {w["id"] for w in snap["work_items"]}
        self.assertEqual(ids, {"pr:8", "pr:7", "branch:ben/spike", "direct:ben"})
        commit_a1 = next(c for c in snap["commits"] if c["sha"] == "a1")
        self.assertEqual(commit_a1["work_item"], "pr:7")  # squash commit "(#7)" attributed to its PR
        pr8 = next(w for w in snap["work_items"] if w["id"] == "pr:8")
        self.assertNotIn("package-lock.json", pr8["paths"])  # ignored by default
        [ov] = [s for s in snap["signals"] if s["type"] == "overlap"]
        self.assertEqual(ov["work_items"], ["branch:ben/spike", "pr:8"])

    def test_degrades_and_records_instead_of_failing(self):
        obs = collect(FakeClient(budget=3), "o/r", config.normalise(None), NOW)
        self.assertTrue(obs["meta"]["degraded"])
        snap = derive(obs, config.normalise(None), NOW)
        self.assertEqual(validate(snap), [])
        self.assertEqual(snap["provenance"]["degraded"], obs["meta"]["degraded"])


if __name__ == "__main__":
    unittest.main()
