"""Pure derivation: observations + config + now -> snapshot v1.

No network, no clock reads. Same input gives the same output (ADR-006).
"""

from __future__ import annotations

import datetime as dt
import fnmatch
import re
from collections import defaultdict

from . import SNAPSHOT_SCHEMA, VERSION
from . import signals as sig

AGENT_TRAILER = re.compile(
    r"^(co-authored-by|generated-by|assisted-by|agent):.*"
    r"(claude|copilot|codex|cursor|devin|gemini|aider|jules|agent|\[bot\])",
    re.IGNORECASE | re.MULTILINE,
)
PR_REF_IN_COMMIT = re.compile(r"(?:\(#(\d+)\)\s*$|^Merge pull request #(\d+))", re.MULTILINE)


# ---------------------------------------------------------------- time

def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def latest(*values: str | None) -> str | None:
    present = [v for v in values if v]
    return max(present, key=lambda v: parse_time(v)) if present else None


# ---------------------------------------------------------------- paths

def _pattern_matches(path: str, pattern: str) -> bool:
    """Anchored matching. v0 used substring matching, so 'test/' matched 'latest/x'."""
    if any(ch in pattern for ch in "*?["):
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path.rsplit("/", 1)[-1], pattern)
    if pattern.endswith("/"):
        return path.startswith(pattern) or path == pattern[:-1]
    return path.startswith(pattern)


def is_ignored(path: str, ignore: list[str]) -> bool:
    name = path.rsplit("/", 1)[-1]
    for pattern in ignore:
        if pattern.startswith("/"):
            if _pattern_matches(path, pattern[1:]):
                return True
        elif pattern.endswith("/"):
            if path.startswith(pattern) or f"/{pattern}" in f"/{path}":
                return True
        elif _pattern_matches(path, pattern) or name == pattern:
            return True
    return False


def area_of(path: str, depth: int, containers: list[str]) -> str:
    segments = path.split("/")
    if len(segments) == 1:
        return path  # root files are their own area
    d = depth + (1 if segments[0] in containers else 0)
    return "/".join(segments[: min(d, len(segments) - 1)])


def lane_of(area: str, is_dir: bool, lanes: list[dict]) -> str:
    probe = area + "/" if is_dir else area
    for lane in lanes:
        for pattern in lane.get("paths", []):
            if _pattern_matches(probe, pattern):
                return lane["id"]
    return "other"


# ---------------------------------------------------------------- actors

def actor_id(author: dict | None) -> str:
    if not author:
        return "unknown"
    return author.get("login") or author.get("name") or "unknown"


def actor_record(author: dict | None) -> dict:
    login = (author or {}).get("login")
    kind = "bot" if ((author or {}).get("type") == "Bot" or (login or "").endswith("[bot]")) else "human"
    return {"id": actor_id(author), "kind": kind, "linked": bool(login)}


def agent_declared(messages: list[str]) -> bool:
    return any(AGENT_TRAILER.search(m or "") for m in messages)


# ---------------------------------------------------------------- baseline (issue #2)

def baseline_resolver(obs: dict):
    """Which observed default-branch commits are already in a work item's base?

    Answered from the commit graph (merge-base SHA + parent links), not from timestamps.
    Returns f(item) -> (set of baseline SHAs | None, status) where status is one of
      resolved        merge base is an observed commit; baseline = its observed ancestors
      before_window   merge base predates every observed commit; nothing observed is baseline
      unresolved      merge base unknown, or outside a truncated commit list
    """
    parents = {c["sha"]: c.get("parents", []) for c in obs.get("commits", [])}
    truncated = bool(obs.get("meta", {}).get("commits_truncated"))

    def resolve(item):
        mb = (item.get("merge_base") or {}).get("sha")
        if not mb:
            return None, "unresolved"
        if mb in parents:
            seen, stack = set(), [mb]
            while stack:
                sha = stack.pop()
                if sha in seen or sha not in parents:
                    continue
                seen.add(sha)
                stack.extend(parents[sha])
            return seen, "resolved"
        return (None, "unresolved") if truncated else (set(), "before_window")

    return resolve


# ---------------------------------------------------------------- derivation

def derive(obs: dict, cfg: dict, now: dt.datetime) -> dict:
    repo = obs["repository"]
    default_branch = repo.get("default_branch") or "main"
    window_hours = obs.get("window", {}).get("hours", cfg["window_hours"])
    since_dt = now - dt.timedelta(hours=window_hours)
    since = iso(since_dt)
    ignore, depth, containers = cfg["ignore"], int(cfg["area_depth"]), cfg["containers"]

    def keep(paths):
        return sorted({p for p in paths or [] if not is_ignored(p, ignore)})

    area_is_dir: dict[str, bool] = {}

    def areas_for(paths):
        out = set()
        for p in paths:
            a = area_of(p, depth, containers)
            area_is_dir[a] = a != p
            out.add(a)
        return sorted(out)

    actors: dict[str, dict] = {}

    def note_actor(author):
        rec = actor_record(author)
        actors.setdefault(rec["id"], {**rec, "work_items": set()})
        return rec["id"]

    work_items: list[dict] = []
    by_id: dict[str, dict] = {}

    # Pull requests ---------------------------------------------------------
    open_heads: dict[str, str] = {}
    for pr in obs.get("pull_requests", []):
        wid = f"pr:{pr['number']}"
        if pr.get("state") == "open":
            state = "draft" if pr.get("draft") else "open"
        else:
            state = "merged" if pr.get("merged") else "closed"
        in_flight = state in ("open", "draft")
        if not in_flight and (parse_time(pr.get("updated_at")) or since_dt) < since_dt:
            continue
        commits = pr.get("commits", [])
        authors = {note_actor(pr.get("author"))} | {note_actor(c.get("author")) for c in commits}
        paths = keep(pr.get("paths"))
        last = latest(pr.get("updated_at"), *[c.get("date") for c in commits])
        review_state = None
        if in_flight:
            review_state = "draft" if pr.get("draft") else ("review_requested" if pr.get("requested_reviewers") else "no_reviewer")
            if pr.get("head"):
                open_heads[pr["head"]] = wid
        item = {
            "id": wid, "kind": "pull_request", "number": pr["number"], "title": pr.get("title", ""),
            "url": pr.get("url"), "state": state, "in_flight": in_flight,
            "head": pr.get("head"), "base": pr.get("base"), "actors": sorted(authors),
            "created_at": pr.get("created_at"), "last_activity_at": last,
            "paths": paths, "areas": areas_for(paths), "lanes": [], "commit_count": len(commits),
            "review_state": review_state, "waiting_on": [],
            "agent_declared": agent_declared([c.get("message", "") for c in commits] + [pr.get("body") or ""]),
            "burst": None, "merge_base": pr.get("merge_base"), "_body": pr.get("body") or "", "_commits": commits,
        }
        work_items.append(item)
        by_id[wid] = item

    # Unproposed branches -----------------------------------------------------
    for br in obs.get("branches", []):
        if br.get("name") in (default_branch,) or br.get("name") in open_heads:
            continue
        if int(br.get("ahead_by", 0)) <= 0:
            continue
        wid = f"branch:{br['name']}"
        commits = br.get("commits", [])
        paths = keep(br.get("paths"))
        item = {
            "id": wid, "kind": "branch", "number": None, "title": br["name"], "url": br.get("url"),
            "state": "unproposed", "in_flight": True, "head": br["name"], "base": default_branch,
            "actors": sorted({note_actor(c.get("author")) for c in commits}),
            "created_at": None, "last_activity_at": latest(*[c.get("date") for c in commits]),
            "paths": paths, "areas": areas_for(paths), "lanes": [], "commit_count": len(commits),
            "review_state": None, "waiting_on": [],
            "agent_declared": agent_declared([c.get("message", "") for c in commits]),
            "burst": None, "merge_base": br.get("merge_base"), "_body": "", "_commits": commits,
        }
        work_items.append(item)
        by_id[wid] = item

    # Default-branch commits: attribute to merged PRs, otherwise to per-author direct streams
    commit_rows = []
    direct: dict[str, list[dict]] = defaultdict(list)
    for c in obs.get("commits", []):
        when = parse_time(c.get("date"))
        if when and when < since_dt:
            continue
        aid = note_actor(c.get("author"))
        paths = keep(c.get("paths"))
        message = c.get("message", "")
        match = PR_REF_IN_COMMIT.search(message.splitlines()[0] if message else "")
        pr_ref = f"pr:{match.group(1) or match.group(2)}" if match else None
        if pr_ref not in by_id:
            direct[aid].append(dict(c, paths=paths))
        commit_rows.append({
            "sha": c["sha"], "url": c.get("url"), "message": (message.splitlines() or [""])[0],
            "date": c.get("date"), "actor": aid, "paths": paths, "areas": areas_for(paths),
            "work_item": pr_ref if pr_ref in by_id else f"direct:{aid}",
        })

    for aid, commits in sorted(direct.items()):
        paths = sorted({p for c in commits for p in c["paths"]})
        if not paths:
            continue
        wid = f"direct:{aid}"
        item = {
            "id": wid, "kind": "direct", "number": None,
            "title": f"Direct pushes to {default_branch}", "url": commits[0].get("url"),
            "state": "pushed", "in_flight": False, "head": default_branch, "base": None,
            "actors": [aid], "created_at": None,
            "last_activity_at": latest(*[c.get("date") for c in commits]),
            "paths": paths, "areas": areas_for(paths), "lanes": [], "commit_count": len(commits),
            "review_state": None, "waiting_on": [],
            "agent_declared": agent_declared([c.get("message", "") for c in commits]),
            "burst": None, "merge_base": None, "_body": "", "_commits": commits,
        }
        work_items.append(item)
        by_id[wid] = item

    # Areas and lanes ------------------------------------------------------------
    lanes_cfg = cfg["lanes"]
    area_lane = {a: lane_of(a, area_is_dir.get(a, True), lanes_cfg) for a in area_is_dir}
    for item in work_items:
        item["lanes"] = sorted({area_lane[a] for a in item["areas"]})
        for aid in item["actors"]:
            actors[aid]["work_items"].add(item["id"])

    area_rows = {}
    for a in sorted(area_is_dir):
        area_rows[a] = {"id": a, "lane": area_lane[a], "in_flight": [], "files": set(),
                        "recent_commits": 0, "actors": set(), "last_activity_at": None}
    for item in work_items:
        active = item["in_flight"] or item["kind"] == "direct"
        for a in item["areas"]:
            if active:
                area_rows[a]["in_flight"].append(item["id"])
                area_rows[a]["actors"].update(item["actors"])
            area_rows[a]["last_activity_at"] = latest(area_rows[a]["last_activity_at"], item["last_activity_at"])
        if active:
            for p in item["paths"]:
                area_rows[area_of(p, depth, containers)]["files"].add(p)
    for c in commit_rows:
        for a in c["areas"]:
            area_rows[a]["recent_commits"] += 1
            area_rows[a]["last_activity_at"] = latest(area_rows[a]["last_activity_at"], c["date"])
            area_rows[a]["actors"].add(c["actor"])

    # Signals ----------------------------------------------------------------------
    thresholds = cfg["signals"]
    signals = []
    waits = sig.waiting(work_items, by_id, open_heads)  # first: overlap uses waiting_on
    signals += sig.overlap(work_items, area_rows, thresholds, lambda p: area_of(p, depth, containers),
                           baseline_resolver(obs))
    signals += sig.stale(work_items, now, thresholds)
    signals += waits
    signals += sig.burst(work_items, thresholds)

    # Assemble ---------------------------------------------------------------------
    lanes = []
    for lane in lanes_cfg + [{"id": "other", "label": "Other", "description": "Paths no lane claims", "source": "fallback"}]:
        areas_in = [a for a, l in area_lane.items() if l == lane["id"]]
        if lane["id"] == "other" and not areas_in:
            continue
        lanes.append({
            "id": lane["id"], "label": lane.get("label", lane["id"].title()),
            "description": lane.get("description", ""), "source": lane.get("source", "config"),
            "areas": sorted(areas_in),
            "in_flight": sorted({w for a in areas_in for w in area_rows[a]["in_flight"]}),
            "recent_commits": sum(1 for c in commit_rows if any(area_lane[a] == lane["id"] for a in c["areas"])),
        })

    for item in work_items:
        item.pop("_body", None)
        item.pop("_commits", None)

    areas_out = []
    for a, row in area_rows.items():
        areas_out.append({**row, "in_flight": sorted(row["in_flight"]), "files": sorted(row["files"]),
                          "actors": sorted(row["actors"])})

    summary_signals = {t: 0 for t in ("overlap", "stale", "waiting", "burst")}
    for s in signals:
        summary_signals[s["type"]] += 1

    issues = [i for i in obs.get("issues", [])]
    issue_rows = [{"number": i["number"], "title": i.get("title", ""), "state": i.get("state", ""),
                   "url": i.get("url"), "labels": i.get("labels", []), "updated_at": i.get("updated_at")}
                  for i in issues]

    meta = obs.get("meta", {})
    return {
        "schema": SNAPSHOT_SCHEMA,
        "generated_at": iso(now),
        "trigger": obs.get("trigger", {}),
        "repository": {k: repo.get(k) for k in ("full_name", "url", "default_branch", "visibility", "description")},
        "window": {"hours": window_hours, "since": since},
        "config": {"source": cfg["source"], "lanes_source": cfg["lanes_source"], "title": cfg["title"],
                   "signals": thresholds, "ignore": ignore, "containers": containers, "area_depth": depth},
        "summary": {
            "in_flight": sum(1 for w in work_items if w["in_flight"]),
            "areas_active": sum(1 for r in areas_out if r["in_flight"]),
            "commits_in_window": len(commit_rows),
            "open_issues": sum(1 for i in issue_rows if i["state"] == "open"),
            "signals": summary_signals,
        },
        "lanes": lanes,
        "areas": areas_out,
        "work_items": sorted(sorted(work_items, key=lambda w: w["last_activity_at"] or "", reverse=True),
                             key=lambda w: not w["in_flight"]),
        "commits": sorted(commit_rows, key=lambda c: c["date"] or "", reverse=True),
        "issues": issue_rows,
        "actors": [{**a, "work_items": sorted(a["work_items"])} for _, a in sorted(actors.items())],
        "signals": signals,
        "provenance": {
            "source": meta.get("source", "GitHub REST API"),
            "collector": "blackmath88/observstory",
            "collector_version": VERSION,
            "observations_fetched_at": obs.get("fetched_at"),
            "api_calls": meta.get("api_calls", 0),
            "rate_limit_remaining": meta.get("rate_limit_remaining"),
            "degraded": list(meta.get("degraded", [])),
        },
    }
