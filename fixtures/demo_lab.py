#!/usr/bin/env python3
"""Demo Lab fixtures (issue #6): one fictional project at different moments of its life.

Everything here is SYNTHETIC. `northstar/chat-app` and `northstar/recsys` are invented
repositories; Alice, Ben and Sofia are invented people. Each state is an observation bundle
(observstory.observations/v1) that goes through the real derive -> scene compiler -> Project Map.

  python3 fixtures/demo_lab.py      -> fixtures/demo-lab/<state>.json
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib

OUT = pathlib.Path(__file__).parent / "demo-lab"
T0 = dt.datetime(2026, 9, 14, 0, 0, tzinfo=dt.timezone.utc)   # Monday 00:00, week one; at(day, hour) is clock time
AGENT = "\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

CHAT_APP_CONFIG = {
    "title": "Northstar chat (synthetic demo)",
    "lanes": [
        {"id": "intent", "label": "Intent", "description": "Why and what: docs and decisions",
         "paths": ["README", "docs/", "DECISIONS"]},
        {"id": "core", "label": "Core", "description": "Conversation and search engine", "paths": ["src/"]},
        {"id": "interface", "label": "Interface", "description": "What people see", "paths": ["web/"]},
        {"id": "verify", "label": "Verify", "description": "Tests and evaluations", "paths": ["tests/", "evals/"]},
        {"id": "ship", "label": "Ship", "description": "Build and deploy", "paths": [".github/", "deploy/"]},
    ],
}
RECSYS_CONFIG = {
    "title": "Northstar recommendations (synthetic demo)",
    "lanes": [
        {"id": "data", "label": "Data", "description": "Sources and datasets", "paths": ["data/"]},
        {"id": "pipeline", "label": "Pipeline", "description": "Ingestion and features", "paths": ["pipeline/"]},
        {"id": "model", "label": "Model", "description": "Training and architecture", "paths": ["model/"]},
        {"id": "eval", "label": "Eval", "description": "Benchmarks", "paths": ["eval/"]},
        {"id": "api", "label": "API", "description": "Serving", "paths": ["api/"]},
        {"id": "docs", "label": "Docs", "description": "Explaining it", "paths": ["docs/", "README.md"]},
    ],
}


def at(day: float, hour: float = 0) -> dt.datetime:
    return T0 + dt.timedelta(days=day, hours=hour)


def iso(t: dt.datetime) -> str:
    return t.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha(label: str) -> str:
    return hashlib.sha1(label.encode()).hexdigest()


def who(name: str) -> dict:
    return {"login": name.lower(), "name": name, "type": "User"}


class Repo:
    """A tiny fictional repository: a linear main branch plus pull requests and branches."""

    def __init__(self, full_name: str):
        # No URLs: the repositories are invented, and a real account might own the name.
        self.full_name, self.url = full_name, None
        self.main: list[dict] = []          # oldest first
        self.prs: dict[int, dict] = {}
        self.branches: dict[str, dict] = {}

    def push(self, when, author, paths, msg):
        parent = self.main[-1]["sha"] if self.main else sha(self.full_name + ":root")
        c = {"sha": sha(f"{self.full_name}:{msg}:{when}"), "url": None, "date": iso(when), "author": who(author),
             "message": msg, "paths": list(paths), "parents": [parent]}
        self.main.append(c)
        return c["sha"]

    def head(self, before):
        older = [c for c in self.main if c["date"] <= iso(before)]
        return older[-1]["sha"] if older else sha(self.full_name + ":root")

    def commits(self, author, times, msg, trailer=""):
        return [{"sha": sha(f"{author}:{msg}:{t}:{i}"), "date": iso(t), "author": who(author),
                 "message": f"{msg} ({i + 1}){trailer}", "parents": []} for i, t in enumerate(times)]

    def open_pr(self, number, title, author, paths, times, *, head=None, base="main", body="", reviewers=(),
                draft=False, created=None, trailer=""):
        created = created or times[0]
        self.prs[number] = {
            "number": number, "title": title, "body": body, "state": "open", "draft": draft, "merged": False,
            "head": head or f"{author.lower()}/pr-{number}", "base": base, "author": who(author),
            "created_at": iso(created), "updated_at": iso(times[-1]), "url": None,
            "requested_reviewers": list(reviewers), "paths": list(paths),
            "commits": self.commits(author, times, title, trailer),
            "merge_base": {"sha": self.head(created), "source": "compare"},
        }
        return self.prs[number]

    def close_pr(self, number, when, merged):
        pr = self.prs[number]
        pr.update(state="closed", merged=merged, draft=False, updated_at=iso(when))
        if merged:  # squash-merge onto main; the commit is attributed to the PR by its "(#N)" suffix
            self.push(when, pr["author"]["name"], pr["paths"], f"{pr['title']} (#{number})")

    def branch(self, name, author, paths, times):
        self.branches[name] = {"name": name, "url": None, "ahead_by": len(times),
                               "paths": list(paths), "commits": self.commits(author, times, name.split("/")[-1]),
                               "merge_base": {"sha": self.head(times[0]), "source": "compare"}}

    def observe(self, now, note):
        """The observation bundle the collector would have produced at `now`."""
        window = dt.timedelta(hours=48)
        prs = [dict(p) for p in self.prs.values() if p["created_at"] <= iso(now)]
        for p in prs:
            p["commits"] = [c for c in p["commits"] if c["date"] <= iso(now)]
        heads = {p["head"] for p in prs if p["state"] == "open"}
        return {
            "schema": "observstory.observations/v1", "note": note, "synthetic": True, "fetched_at": iso(now),
            "repository": {"full_name": self.full_name, "url": self.url, "default_branch": "main",
                           "visibility": "public", "description": "Synthetic demo repository"},
            "window": {"hours": 48},
            "trigger": {"event": "demo-lab"},
            "commits": [c for c in reversed(self.main) if now - window <= dt.datetime.fromisoformat(c["date"][:-1] + "+00:00") <= now],
            "pull_requests": prs,
            "branches": [dict(b) for n, b in self.branches.items() if n not in heads and b["commits"][0]["date"] <= iso(now)],
            "issues": [],
            "meta": {"source": "synthetic (Demo Lab)", "api_calls": 0, "rate_limit_remaining": None, "degraded": []},
        }


def hours(start: dt.datetime, *offsets: float) -> list[dt.datetime]:
    return [start + dt.timedelta(hours=h) for h in offsets]


def chat_app_story() -> dict[str, dict]:
    """Northstar chat over about a week: the main story (quiet → calm), an agent burst, then open loops."""
    r, states = Repo("northstar/chat-app"), {}

    # history before the story starts
    r.push(at(-2, 10), "Alice", ["docs/architecture.md"], "Describe conversation storage")
    r.push(at(-1, 15), "Ben", [".github/workflows/ci.yml"], "Cache dependencies in CI")
    r.push(at(-1, 18), "Sofia", ["web/chat/Thread.tsx"], "Tighten thread spacing")
    states["quiet"] = r.observe(at(0, 8), "The project exists; recent work has landed; nothing is in flight.")

    # 1. healthy parallel work: three people, three different areas
    r.open_pr(41, "Conversation memory", "Alice", ["src/conversation/memory.py", "src/conversation/store.py"],
              hours(at(0, 9), 0, 3, 6), head="alice/conversation-memory")
    r.open_pr(42, "Search index", "Ben", ["src/search/index.py", "src/search/query.py"], hours(at(0, 10), 0, 5),
              head="ben/search-index")
    r.open_pr(45, "Search relevance evals", "Sofia", ["evals/search/run.py", "evals/search/cases.json"],
              hours(at(0, 11), 0, 4))
    states["parallel"] = r.observe(at(0, 17), "Three people, three areas.")

    # 2. overlap emerges: Sofia's evals land; she starts chat history on a branch, no PR yet
    r.close_pr(45, at(0, 20), merged=True)
    r.branch("sofia/chat-history", "Sofia", ["src/conversation/history.py", "src/conversation/store.py"],
             hours(at(1, 8), 0, 1, 2))
    r.prs[41]["commits"] += r.commits("Alice", hours(at(1, 9), 0), "Conversation memory: eviction")
    r.prs[41]["updated_at"] = iso(at(1, 9))
    states["overlap"] = r.observe(at(1, 11), "Sofia starts chat history on a branch.")

    # 3. crowded: Sofia opens her PR; an agent-assisted refactor also touches store.py; Ben adds export
    r.branches.pop("sofia/chat-history")
    r.open_pr(43, "Chat history persistence", "Sofia", ["src/conversation/history.py", "src/conversation/store.py"],
              hours(at(1, 8), 0, 1, 2, 5), head="sofia/chat-history", created=at(1, 13))
    r.open_pr(46, "Store serialization refactor", "Ben", ["src/conversation/store.py", "src/conversation/serialize.py"],
              hours(at(1, 12), 0, 0.2, 0.4, 2), head="ben/store-serialization", trailer=AGENT)
    r.open_pr(47, "Conversation export", "Ben", ["src/conversation/export.py"], hours(at(1, 14), 0),
              head="ben/export")
    states["crowded"] = r.observe(at(1, 16), "Three open changes rewrite store.py.")

    # 4. resolved: they talk. Sofia closes #43 and writes the evaluation for Alice's memory instead;
    #    Ben rebases his refactor on top of Alice's branch
    r.close_pr(43, at(2, 10), merged=False)
    r.close_pr(42, at(2, 11), merged=True)
    r.prs[41].update(requested_reviewers=["ben"], updated_at=iso(at(2, 12)))
    r.open_pr(44, "Evaluation harness for conversation memory", "Sofia",
              ["evals/conversation/test_memory.py", "evals/conversation/cases.json"],
              hours(at(2, 11), 0, 2), body="Replaces #43. Evaluates Alice's memory API.\n\nDepends on #41.")
    r.prs[46].update(base="alice/conversation-memory", updated_at=iso(at(2, 13)))
    states["resolved"] = r.observe(at(2, 14), "Sofia moves to evaluation; Ben stacks his refactor on Alice's work.")

    # 5. calm again: #41 and #46 land; the evaluation continues on its own
    r.close_pr(41, at(3, 10), merged=True)
    r.close_pr(46, at(3, 15), merged=True)
    r.close_pr(47, at(3, 16), merged=True)
    r.prs[44].update(body="Evaluates the memory API.", updated_at=iso(at(4, 9)),
                     requested_reviewers=["alice"])
    r.open_pr(48, "Composer keyboard shortcuts", "Alice", ["web/chat/Composer.tsx"], hours(at(4, 8), 0, 1))
    states["calm"] = r.observe(at(4, 10), "Work landed; the evaluation continues; nothing overlaps.")

    # an agent-assisted change the same afternoon
    burst = [at(4, 13) + dt.timedelta(minutes=2 * i) for i in range(24)]
    r.open_pr(50, "Generate settings screens", "Sofia", ["web/settings/Profile.tsx", "web/settings/Privacy.tsx",
              "web/settings/Notifications.tsx"], burst, head="sofia/settings-screens", trailer=AGENT)
    states["burst"] = r.observe(at(4, 14), "An agent-assisted change: 24 commits in under an hour.")

    # the following week: open loops
    r.close_pr(44, at(5, 12), merged=True)
    r.close_pr(50, at(5, 15), merged=True)
    r.branch("ben/search-v2-spike", "Ben", ["src/search/ranker.py"], hours(at(1, 16), 0, 1))
    r.open_pr(40, "Streaming responses", "Alice", ["src/conversation/stream.py", "web/chat/Thread.tsx"],
              hours(at(2, 9), 0, 3), draft=True, head="alice/streaming")
    r.prs[48]["commits"] += r.commits("Alice", hours(at(7, 9), 0), "Composer shortcuts: review fixes")
    r.prs[48]["updated_at"] = iso(at(7, 9))
    states["stale"] = r.observe(at(7, 11), "An old branch without a PR and a parked draft.")

    return states


def recsys_story() -> dict:
    r = Repo("northstar/recsys")
    r.push(at(-1, 12), "Ben", ["README.md"], "Explain the offline metrics")
    r.open_pr(80, "Tokenizer v2 features", "Alice", ["pipeline/features/tokenize.py", "model/embed.py"],
              hours(at(1, 8), 0, 4))
    r.open_pr(81, "Embedding dim 1024", "Ben", ["model/embed.py", "model/config.yaml"], hours(at(1, 9), 0, 2))
    r.open_pr(82, "Multilingual eval set", "Sofia", ["eval/multilingual/run.py"], hours(at(1, 11), 0),
              body="Depends on #81 for the new embedding size.")
    r.open_pr(83, "Batch scoring endpoint", "Alice", ["api/batch.py"], hours(at(1, 12), 0))
    return r.observe(at(1, 14), "A different project: the lanes come from its own configuration.")


def build() -> dict[str, dict]:
    states = chat_app_story()
    states["other-project"] = recsys_story()
    return states


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, obs in build().items():
        (OUT / f"{name}.json").write_text(json.dumps(obs, indent=1) + "\n", encoding="utf-8")
        print("wrote", name)
    (OUT / "chat-app.config.json").write_text(json.dumps(CHAT_APP_CONFIG, indent=2) + "\n")
    (OUT / "recsys.config.json").write_text(json.dumps(RECSYS_CONFIG, indent=2) + "\n")
