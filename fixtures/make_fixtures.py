#!/usr/bin/env python3
"""Generate observation-bundle fixtures (observstory.observations/v1).

Fixtures are *observations* (normalised GitHub facts), not snapshots, so tests exercise the
real derivation. Run: python3 fixtures/make_fixtures.py
The repository `example/chat-app` is fictional; URLs are illustrative.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib

OUT = pathlib.Path(__file__).parent / "observations"
REPO = "example/chat-app"
BASE = f"https://github.com/{REPO}"
NOW = dt.datetime(2026, 9, 21, 12, 0, tzinfo=dt.timezone.utc)
AGENT_TRAILER = "\n\nCo-Authored-By: Claude <noreply@anthropic.com>"


def t(hours_ago: float, now=NOW) -> str:
    return (now - dt.timedelta(hours=hours_ago)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def who(login):
    return {"login": login, "name": login.title(), "type": "Bot" if login.endswith("[bot]") else "User"}


_sha = [0]


def sha():
    _sha[0] += 1
    return f"{_sha[0]:07x}" + "0" * 33


def commits(login, hours_ago_list, msg="work", trailer="", now=NOW):
    return [{"sha": sha(), "date": t(h, now), "author": who(login), "message": f"{msg} {i}{trailer}"}
            for i, h in enumerate(hours_ago_list)]


def pr(number, title, login, paths, cs, *, state="open", draft=False, merged=False, head=None, base="main",
       body="", reviewers=None, updated=None, created=None, now=NOW):
    last = updated if updated is not None else min((h for h in [0.5]), default=0.5)
    return {
        "number": number, "title": title, "body": body, "state": state, "draft": draft, "merged": merged,
        "head": head or f"{login}/pr-{number}", "base": base, "author": who(login),
        "created_at": t(created if created is not None else 30, now), "updated_at": t(last, now),
        "url": f"{BASE}/pull/{number}", "requested_reviewers": reviewers or [], "paths": paths, "commits": cs,
    }


def branch(name, paths, cs, ahead=None):
    return {"name": name, "url": f"{BASE}/tree/{name}", "ahead_by": ahead if ahead is not None else len(cs),
            "paths": paths, "commits": cs}


def bundle(name, *, prs=(), branches=(), direct=(), issues=(), now=NOW, note=""):
    return {
        "schema": "observstory.observations/v1",
        "note": note,
        "fetched_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "repository": {"full_name": REPO, "url": BASE, "default_branch": "main", "visibility": "public",
                       "description": "Fictional fixture repository"},
        "window": {"hours": 48},
        "trigger": {"event": "fixture", "run_id": name, "sha": ""},
        "commits": list(direct), "pull_requests": list(prs), "branches": list(branches), "issues": list(issues),
        "meta": {"source": "fixture", "api_calls": 0, "rate_limit_remaining": None, "degraded": []},
    }


def direct_commit(login, hours_ago, paths, msg="direct change", now=NOW):
    return {"sha": sha(), "url": f"{BASE}/commit/{_sha[0]:07x}", "date": t(hours_ago, now), "author": who(login),
            "message": msg, "paths": paths}


FIXTURES = {}

# E1: two contributors touching the same subsystem --------------------------------
FIXTURES["e1-same-subsystem"] = bundle(
    "e1", note="alice's PR and sofia's unproposed branch both change src/conversation (store.py shared)",
    prs=[pr(14, "Conversation memory", "alice", ["src/conversation/store.py", "src/conversation/ui.tsx"],
            commits("alice", [20, 6, 2]), updated=2)],
    branches=[branch("sofia/convo-rewrite", ["src/conversation/store.py", "src/conversation/prompt.py"],
                     commits("sofia", [5, 3, 1]))],
)

# E2: parallel, non-overlapping work --------------------------------------------------
FIXTURES["e2-parallel"] = bundle(
    "e2", note="three work items in three different areas; no overlap expected",
    prs=[pr(15, "Billing webhooks", "alice", ["src/billing/webhook.py", "src/billing/models.py"],
            commits("alice", [10, 4]), updated=4)],
    branches=[branch("sofia/search", ["src/search/index.py"], commits("sofia", [3, 1]))],
    direct=[direct_commit("ben", 6, ["docs/setup.md"]), direct_commit("ben", 5, ["README.md"])],
)

# E3: stale branch / inactive work ---------------------------------------------------
FIXTURES["e3-stale"] = bundle(
    "e3", note="old-spike branch idle 6d with no PR; draft PR #9 idle 5d; PR #10 active",
    prs=[pr(9, "Experimental parser", "ben", ["src/parser/core.py"], commits("ben", [130, 120]),
            draft=True, updated=120, created=140),
         pr(10, "Fix login redirect", "alice", ["src/auth/redirect.py"], commits("alice", [3]), updated=3,
            reviewers=["ben"])],
    branches=[branch("old-spike", ["src/graph/spike.py"], commits("sofia", [150, 144]))],
)

# E4: PR waiting on another change --------------------------------------------------
FIXTURES["e4-waiting"] = bundle(
    "e4", note="#21 is stacked on #20's branch; #22 declares 'Depends on #20'",
    prs=[pr(20, "API v2 routes", "alice", ["src/api/routes.py"], commits("alice", [8, 4]), head="alice/api-v2",
            updated=4, reviewers=["sofia"]),
         pr(21, "API v2 pagination", "alice", ["src/api/paginate.py"], commits("alice", [3]), head="alice/api-v2-page",
            base="alice/api-v2", updated=3),
         pr(22, "Client SDK for v2", "sofia", ["clients/sdk.ts"], commits("sofia", [2]), updated=2,
            body="Adds the SDK.\n\nDepends on #20 for the new routes.")],
)

# E5: agent-generated rapid commit activity -----------------------------------------
agent_times = [2 - i * (40 / 60 / 23) for i in range(24)]  # 24 commits across 40 minutes
FIXTURES["e5-burst"] = bundle(
    "e5", note="PR #30: 24 commits in ~40 min with agent trailer; PR #31: 5 human-paced commits over 2 days",
    prs=[pr(30, "Generate settings screens", "sofia", ["src/settings/screen.tsx"],
            commits("sofia", agent_times, "step", AGENT_TRAILER), updated=1.3),
         pr(31, "Tidy logging", "ben", ["src/logging/setup.py"], commits("ben", [40, 30, 20, 10, 2]), updated=2)],
)

# E6: zero-config repo with only root files and direct pushes (hackathon-style) ----------
FIXTURES["e6-direct-pushes"] = bundle(
    "e6", note="two people push straight to main in the same area; no PRs, no branches",
    direct=[direct_commit("alice", 20, ["app/game/loop.js"]), direct_commit("sofia", 8, ["app/game/loop.js", "app/game/input.js"]),
            direct_commit("ben", 4, ["pitch.md"])],
)

# Issue #2: base-aware overlap -------------------------------------------------------
# main history (newest last): m1 -> m2 -> m3 ; each is a direct push by alice.


def main_commit(sha, parent, hours_ago, paths, msg="direct change", login="alice"):
    return {"sha": sha, "url": f"{BASE}/commit/{sha}", "date": t(hours_ago), "author": who(login),
            "message": msg, "paths": paths, "parents": [parent] if parent else []}


MAIN = [main_commit("m3" + "0" * 38, "m2" + "0" * 38, 6, ["README.md"], "Tighten README intro"),
        main_commit("m2" + "0" * 38, "m1" + "0" * 38, 20, ["docs/guide.md"], "Guide"),
        main_commit("m1" + "0" * 38, "m0" + "0" * 38, 30, ["README.md"], "README first draft")]
M = {k: k + "0" * 38 for k in ("m0", "m1", "m2", "m3")}


def bob_branch(merge_base, source="compare", paths=("README.md",)):
    return {**branch("bob/readme", list(paths), commits("bob", [3, 2])),
            "merge_base": {"sha": merge_base, "source": source} if merge_base else None}


FIXTURES["b1-baseline"] = bundle(
    "b1", note="bob branched from m3; every README change on main is already in his base -> no overlap",
    branches=[bob_branch(M["m3"])], direct=MAIN)
FIXTURES["b2-after-divergence"] = bundle(
    "b2", note="bob branched from m2; m3 changed README after divergence -> overlap citing m3 only (m1 is baseline)",
    branches=[bob_branch(M["m2"])], direct=MAIN)
FIXTURES["b3-rebased"] = bundle(
    "b3", note="same as b2 after bob rebased onto m3 -> the merge base moves, overlap disappears",
    branches=[bob_branch(M["m3"])], direct=MAIN)
FIXTURES["b4-merged-main-in"] = bundle(
    "b4", note="bob's first commit sits on m1 but he later merged main into his branch; compare reports merge base m3",
    branches=[bob_branch(M["m3"])], direct=MAIN)
FIXTURES["b4-merged-main-in-first-parent"] = bundle(
    "b4fp", note="as b4, but the budget fallback (first-commit parent = m1) is used -> overlap, labelled first_parent",
    branches=[bob_branch(M["m1"], "first_parent")], direct=MAIN)
FIXTURES["b5-squash-merged"] = bundle(
    "b5", note="PR #12 was squash-merged as m4; bob branched afterwards. The squash commit belongs to pr:12, not a direct push",
    prs=[pr(12, "README restructure", "carol", ["README.md"], [], state="closed", merged=True, updated=4)],
    branches=[bob_branch("m4" + "0" * 38)],
    direct=[main_commit("m4" + "0" * 38, M["m3"], 4, ["README.md"], "README restructure (#12)", "carol")] + MAIN)
FIXTURES["b6-base-before-window"] = bundle(
    "b6", note="bob's merge base (m0) predates every observed commit -> all README pushes on main are after divergence",
    branches=[bob_branch(M["m0"])], direct=MAIN)
_b7 = bundle("b7", note="merge base unknown and the commit list was truncated -> treated as parallel, lower confidence",
             branches=[bob_branch("zz" + "0" * 38)], direct=MAIN)
_b7["meta"]["commits_truncated"] = True
FIXTURES["b7-base-unresolved"] = _b7

# Precision study: stale work does not take part in overlap ------------------------------
FIXTURES["p1-stale-excluded"] = bundle(
    "p1", note="an active PR and a branch idle for 10 days both change src/parser/core.py -> stale signal, no overlap",
    prs=[pr(50, "Parser speedup", "alice", ["src/parser/core.py"], commits("alice", [5, 2]), updated=2)],
    branches=[branch("ben/old-parser", ["src/parser/core.py"], commits("ben", [260, 240]))],
)

FIXTURES["p2-transitive-stack"] = bundle(
    "p2", note="#62 is stacked on #61, which is stacked on #60; all three touch src/lock/export.py -> waiting, no overlap",
    prs=[pr(60, "Offline lock parsing", "konsti", ["src/lock/export.py"], commits("konsti", [9]), head="k/offline", updated=9),
         pr(61, "Export locks from build", "konsti", ["src/lock/export.py"], commits("konsti", [6]), head="k/export",
            base="k/offline", updated=6),
         pr(62, "Install tools from locks", "konsti", ["src/lock/export.py"], commits("konsti", [3]), head="k/tools",
            base="k/export", updated=3),
         pr(63, "Lock export docs fix", "ben", ["src/lock/export.py"], commits("ben", [2]), updated=2)],
)

# Demo scenario: four moments in one project ----------------------------------------
D0 = dt.datetime(2026, 9, 21, 9, 0, tzinfo=dt.timezone.utc)
moments = {
    "demo-t0": D0,
    "demo-t1": D0 + dt.timedelta(hours=6),
    "demo-t2": D0 + dt.timedelta(hours=25),
    "demo-t3": D0 + dt.timedelta(hours=31),
}


def demo(stage, now):
    def ago(at):  # absolute scenario hour -> hours before `now`
        return (now - (D0 + dt.timedelta(hours=at))).total_seconds() / 3600

    alice_pr = pr(41, "Conversation memory", "alice", ["src/conversation/store.py", "src/conversation/memory.py"],
                  commits("alice", [ago(-4), ago(-1), ago(min(5, stage * 5))], "memory", now=now),
                  updated=ago(min(5, stage * 5)), created=ago(-4), reviewers=["ben"] if stage >= 2 else [], now=now)
    ben_pr = pr(42, "Search index", "ben", ["src/search/index.py", "src/search/query.py"],
                commits("ben", [ago(-3), ago(0)], "search", now=now), updated=ago(0), created=ago(-3), now=now)
    prs, branches = [alice_pr, ben_pr], []
    burst_at = [ago(4 + i * 0.03) for i in range(12)]  # sofia's agent: 12 commits in ~20 min
    sofia_cs = commits("sofia", burst_at, "history", AGENT_TRAILER, now=now)
    sofia_paths = ["src/conversation/history.py", "src/conversation/store.py"]
    if stage == 1:
        branches.append(branch("sofia/chat-history", sofia_paths, sofia_cs))
    if stage == 2:
        prs.append(pr(43, "Chat history persistence", "sofia", sofia_paths, sofia_cs, head="sofia/chat-history",
                      updated=ago(24.5), created=ago(24.5), now=now))
    if stage == 3:
        prs.append(pr(43, "Chat history persistence", "sofia", sofia_paths, sofia_cs, head="sofia/chat-history",
                      state="closed", updated=ago(30), created=ago(24.5), now=now))
        prs.append(pr(44, "Evaluation harness for conversation memory", "sofia",
                      ["evals/conversation/test_memory.py", "evals/conversation/cases.json"],
                      commits("sofia", [ago(29), ago(30.5)], "evals", now=now), updated=ago(30.5), created=ago(29),
                      body="Moves my chat-history work into evaluation of #41.\n\nDepends on #41.", now=now))
    return bundle(f"demo-t{stage}", prs=prs, branches=branches, now=now,
                  note=["Two contributors working normally", "sofia's agent starts changing src/conversation",
                        "sofia opens a PR; the overlap is visible before either merges",
                        "Resolution: sofia moves to evaluation work that depends on #41"][stage])


_sha[0] = 0x100000  # fixed start so fixtures added above never renumber the demo's SHAs
for stage, (name, when) in enumerate(moments.items()):
    FIXTURES[name] = demo(stage, when)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in FIXTURES.items():
        (OUT / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("wrote", name)
