"""v1 signals (docs/definition/signal-specs.md).

Rule for every signal: the subject is an area or a work item, never a person.
"""

from __future__ import annotations

import datetime as dt
import re

DEPENDS = re.compile(r"\b(depends on|blocked by|requires|after|stacked on)\s+#(\d+)", re.IGNORECASE)
LEVELS = ["low", "medium", "high"]


def _down(level: str) -> str:
    return LEVELS[max(0, LEVELS.index(level) - 1)]


def _parse(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _age(hours: float) -> str:
    return f"{hours / 24:.0f}d" if hours >= 48 else f"{hours:.0f}h"


def _wi_evidence(item: dict) -> dict:
    return {"kind": "work_item", "ref": item["id"], "url": item.get("url"),
            "detail": f"{item['title']} ({item['state']})"}


def overlap(work_items, area_rows, thresholds, area_of):
    """S-1: an area touched by >= N distinct active work items."""
    minimum = int(thresholds["overlap_min_work_items"])
    items = {w["id"]: w for w in work_items}
    out = []
    for area_id, row in area_rows.items():
        ids = sorted(set(row["in_flight"]))
        # A declared or stacked dependency already explains shared ground (experiment E4).
        explained = sorted(i for i in ids if any(t in ids for t in items[i]["waiting_on"]))
        if len(ids) - len(explained) < minimum:
            continue
        members = [items[i] for i in ids]
        file_owners: dict[str, list[str]] = {}
        for w in members:
            for p in w["paths"]:
                if area_of(p) == area_id:
                    file_owners.setdefault(p, []).append(w["id"])
        shared = {p: owners for p, owners in file_owners.items() if len(owners) >= 2}
        confidence = "high" if shared else "medium"
        actor_sets = {tuple(w["actors"]) for w in members}
        same_author = len(actor_sets) == 1 and len(next(iter(actor_sets))) == 1
        if same_author:
            confidence = _down(confidence)
        if not any(w["in_flight"] for w in members):
            confidence = _down(confidence)  # all landed on the default branch: retrospective
        evidence = [{"kind": "file", "ref": p, "url": None, "work_items": sorted(o),
                     "detail": f"changed by {len(o)} work items"} for p, o in sorted(shared.items())]
        evidence += [_wi_evidence(w) for w in members]
        summary = f"{len(ids)} work items touch {area_id}"
        if shared:
            summary += f"; {len(shared)} file{'s' if len(shared) != 1 else ''} changed in more than one"
        out.append({
            "id": f"overlap:{area_id}", "type": "overlap",
            "basis": "derived" if shared else "heuristic", "confidence": confidence,
            "subject": {"kind": "area", "id": area_id}, "summary": summary,
            "work_items": ids, "actors": sorted({a for w in members for a in w["actors"]}),
            "evidence": evidence,
            "rule": {"name": "overlap.area", "params": {"min_work_items": minimum, "same_author": same_author,
                                                         "shared_files": len(shared), "explained_by_waiting": explained}},
        })
    out.sort(key=lambda s: (LEVELS.index(s["confidence"]), len(s["work_items"])), reverse=True)
    return out


def stale(work_items, now, thresholds):
    """S-2: in-flight PR or branch idle for longer than stale_hours."""
    limit = float(thresholds["stale_hours"])
    out = []
    for w in work_items:
        if not w["in_flight"] or w["kind"] not in ("pull_request", "branch"):
            continue
        last = _parse(w["last_activity_at"])
        if not last:
            continue
        idle = (now - last).total_seconds() / 3600
        if idle <= limit:
            continue
        detail = f"no activity for {_age(idle)}"
        if w["kind"] == "branch":
            detail += "; no pull request"
        out.append({
            "id": f"stale:{w['id']}", "type": "stale", "basis": "heuristic",
            "confidence": "low" if w["state"] == "draft" else "medium",
            "subject": {"kind": "work_item", "id": w["id"]},
            "summary": f"{w['id']} idle for {_age(idle)}" + (" (no pull request)" if w["kind"] == "branch" else ""),
            "work_items": [w["id"]], "actors": list(w["actors"]),
            "evidence": [{"kind": "timestamp", "ref": w["last_activity_at"], "url": w.get("url"), "detail": detail},
                         _wi_evidence(w)],
            "rule": {"name": "stale.idle", "params": {"stale_hours": limit, "idle_hours": round(idle, 1)}},
        })
    out.sort(key=lambda s: s["rule"]["params"]["idle_hours"], reverse=True)
    return out


def waiting(work_items, by_id, open_heads):
    """S-3: stacked on another open PR (derived) or declared dependency in the PR body."""
    out = []
    for w in work_items:
        if w["kind"] != "pull_request" or not w["in_flight"]:
            continue
        found: dict[str, tuple[str, dict]] = {}
        base = w.get("base")
        if base in open_heads and open_heads[base] != w["id"]:
            found[open_heads[base]] = ("derived", {"kind": "work_item", "ref": open_heads[base],
                                                    "url": by_id[open_heads[base]].get("url"),
                                                    "detail": f"base branch '{base}' is the head of {open_heads[base]}"})
        for match in DEPENDS.finditer(w.get("_body", "")):
            target = f"pr:{match.group(2)}"
            if target in by_id and by_id[target]["in_flight"] and target != w["id"] and target not in found:
                found[target] = ("declared", {"kind": "text", "ref": match.group(0), "url": w.get("url"),
                                              "detail": f"pull request body declares '{match.group(0)}'"})
        for target, (basis, ev) in sorted(found.items()):
            w["waiting_on"].append(target)
            out.append({
                "id": f"waiting:{w['id']}:{target}", "type": "waiting", "basis": basis, "confidence": "high",
                "subject": {"kind": "work_item", "id": w["id"]},
                "summary": f"{w['id']} waits on {target}",
                "work_items": [w["id"], target],
                "actors": sorted(set(w["actors"]) | set(by_id[target]["actors"])),
                "evidence": [ev, _wi_evidence(by_id[target])],
                "rule": {"name": "waiting.stacked" if basis == "derived" else "waiting.declared", "params": {}},
            })
    return out


def burst(work_items, thresholds):
    """S-4: machine-paced change stream. Folds the commit list; flags nobody."""
    k = int(thresholds["burst_min_commits"])
    window = dt.timedelta(minutes=float(thresholds["burst_window_minutes"]))
    out = []
    for w in work_items:
        if not (w["in_flight"] or w["kind"] == "direct"):
            continue  # closed or merged streams need no folding (experiment demo-t3)
        times = sorted(t for t in (_parse(c.get("date")) for c in w.get("_commits", [])) if t)
        if len(times) < k:
            continue
        best, start = 0, 0
        best_span = (times[0], times[0])
        for end in range(len(times)):
            while times[end] - times[start] > window:
                start += 1
            if end - start + 1 > best:
                best, best_span = end - start + 1, (times[start], times[end])
        if best < k:
            continue
        minutes = round((best_span[1] - best_span[0]).total_seconds() / 60)
        w["burst"] = {"commits": best, "minutes": minutes, "total_commits": len(times)}
        out.append({
            "id": f"burst:{w['id']}", "type": "burst", "basis": "heuristic",
            "confidence": "high" if w["agent_declared"] else "medium",
            "subject": {"kind": "work_item", "id": w["id"]},
            "summary": f"{w['id']}: {best} commits within {minutes} min (machine-paced stream)",
            "work_items": [w["id"]], "actors": list(w["actors"]),
            "evidence": [{"kind": "commit", "ref": f"{best} commits", "url": w.get("url"),
                          "detail": f"from {best_span[0].isoformat()} to {best_span[1].isoformat()}"
                                    + ("; agent trailer declared" if w["agent_declared"] else "")}],
            "rule": {"name": "burst.rate", "params": {"min_commits": k, "window_minutes": thresholds["burst_window_minutes"]}},
        })
    return out
