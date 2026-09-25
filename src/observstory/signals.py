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


def _short(sha):
    return (sha or "")[:7]


def overlap(work_items, area_rows, thresholds, area_of, resolve_base=None, now=None):
    """S-1: an area where at least two work items changed things *in parallel*.

    Pairs, not counts (issue #2). A pair is parallel in an area when both touch it and neither
    change is already part of the other's base:
      in-flight × in-flight   parallel, unless one waits on the other (stacked or declared, E4)
      in-flight × direct      only default-branch commits made after the item diverged count;
                              commits already in its merge base are baseline
      direct × direct         never: pushes to one branch are sequential, each contains the last
    Only pairs that change at least one common file count, unless overlap_require_shared_file is false;
    work items authored only by bots do not take part (ADR-019).
    Stale work (idle > stale_hours) does not take part: it is reported by the stale signal, and in the
    precision study it made up 81% of all overlap pairs (docs/development/precision-report.md).
    """
    minimum = int(thresholds["overlap_min_work_items"])
    resolve_base = resolve_base or (lambda item: (None, "unresolved"))
    items = {w["id"]: w for w in work_items}
    bases = {w["id"]: resolve_base(w) for w in work_items if w["in_flight"]}

    def upstream(wid, seen=None):
        """Everything a work item waits on, transitively: a stack A -> B -> C explains A's shared ground
        with C too (precision study: 9 of 20 non-useful signals came from two-level stacks)."""
        seen = set() if seen is None else seen
        for t in items.get(wid, {}).get("waiting_on", []):
            if t not in seen:
                seen.add(t)
                upstream(t, seen)
        return seen

    idle_limit = float(thresholds["stale_hours"])
    require_file = bool(thresholds.get("overlap_require_shared_file", True))

    def is_stale(w):
        if now is None or not w["in_flight"] or not w["last_activity_at"]:
            return False
        return (now - _parse(w["last_activity_at"])).total_seconds() / 3600 > idle_limit
    out = []
    for area_id, row in area_rows.items():
        all_ids = sorted(set(row["in_flight"]))
        excluded_stale = [i for i in all_ids if is_stale(items[i])]
        excluded_bots = [i for i in all_ids if items[i].get("_bot_only") and i not in excluded_stale]
        ids = [i for i in all_ids if i not in excluded_stale and i not in excluded_bots]
        if len(ids) < 2:
            continue

        def touched(w):
            return {p for p in w["paths"] if area_of(p) == area_id}

        pairs, explained, baseline_pairs, sequential, base_evidence, area_only = [], set(), [], 0, [], 0
        for i, a_id in enumerate(ids):
            for b_id in ids[i + 1:]:
                a, b = items[a_id], items[b_id]
                if a["kind"] == "direct" and b["kind"] == "direct":
                    sequential += 1
                    continue
                if b_id in upstream(a_id) or a_id in upstream(b_id):
                    explained.add(a_id if b_id in upstream(a_id) else b_id)
                    continue
                if a["kind"] == "direct" or b["kind"] == "direct":
                    w, d = (b, a) if a["kind"] == "direct" else (a, b)
                    shas, status = bases[w["id"]]
                    later = [c for c in d.get("_commits", [])
                             if (shas is None or c["sha"] not in shas) and any(area_of(p) == area_id for p in c["paths"])]
                    if not later:
                        baseline_pairs.append(f"{w['id']}|{d['id']}")
                        continue
                    files = touched(w) & {p for c in later for p in c["paths"] if area_of(p) == area_id}
                    if require_file and not files:
                        area_only += 1
                        continue
                    mb = (w.get("merge_base") or {})
                    shas_txt = ", ".join(_short(c["sha"]) for c in later[:4]) + (" …" if len(later) > 4 else "")
                    if status == "unresolved":
                        detail = (f"merge base of {w['id']} is unknown, so all {len(later)} observed commit(s) on the default "
                                  f"branch are treated as parallel: {shas_txt}")
                    elif status == "before_window":
                        detail = (f"{w['id']} diverged at {_short(mb.get('sha'))} ({mb.get('source')}), before every observed "
                                  f"commit; {len(later)} later default-branch commit(s) touch this area: {shas_txt}")
                    else:
                        detail = (f"{w['id']} diverged at {_short(mb.get('sha'))} ({mb.get('source')}); {len(later)} "
                                  f"default-branch commit(s) made after that touch this area: {shas_txt}")
                    base_evidence.append({"kind": "base", "ref": f"{w['id']} × {d['id']}", "url": later[0].get("url"),
                                          "work_items": [w["id"], d["id"]], "detail": detail})
                    weak = status == "unresolved" or mb.get("source") != "compare"  # b4: first-parent can be wrong
                    pairs.append((w["id"], d["id"], files, weak))
                else:
                    files = touched(a) & touched(b)
                    if require_file and not files:
                        area_only += 1
                        continue
                    pairs.append((a_id, b_id, files, False))
        participants = sorted({x for p in pairs for x in p[:2]})
        if not pairs or len(participants) < minimum:
            continue
        members = [items[i] for i in participants]
        file_owners: dict[str, set] = {}
        for a_id, b_id, files, _ in pairs:
            for f in files:
                file_owners.setdefault(f, set()).update((a_id, b_id))
        confidence = "high" if file_owners else "medium"
        actor_sets = {tuple(w["actors"]) for w in members}
        same_author = len(actor_sets) == 1 and len(next(iter(actor_sets))) == 1
        if same_author:
            confidence = _down(confidence)
        if all(p[3] for p in pairs):
            confidence = _down(confidence)  # parallelism rests only on unknown or fallback merge bases
        evidence = [{"kind": "file", "ref": f, "url": None, "work_items": sorted(o),
                     "detail": f"changed by {len(o)} work items in parallel"} for f, o in sorted(file_owners.items())]
        evidence += base_evidence
        evidence += [_wi_evidence(w) for w in members]
        summary = f"{len(participants)} work items change {area_id} in parallel"
        if file_owners:
            summary += f"; {len(file_owners)} shared file{'s' if len(file_owners) != 1 else ''}"
        out.append({
            "id": f"overlap:{area_id}", "type": "overlap",
            "basis": "derived" if file_owners else "heuristic", "confidence": confidence,
            "subject": {"kind": "area", "id": area_id}, "summary": summary,
            "work_items": participants, "actors": sorted({a for w in members for a in w["actors"]}),
            "evidence": evidence,
            "rule": {"name": "overlap.parallel_pairs", "params": {
                "min_work_items": minimum, "same_author": same_author, "shared_files": len(file_owners),
                "parallel_pairs": [f"{a}|{b}" for a, b, _, _ in pairs],
                "baseline_pairs": baseline_pairs, "sequential_direct_pairs": sequential,
                "explained_by_waiting": sorted(explained), "excluded_stale": excluded_stale,
                "excluded_bot_only": excluded_bots, "area_only_pairs_skipped": area_only,
                "require_shared_file": require_file}},
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
