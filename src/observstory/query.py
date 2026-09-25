"""Agent surface: questions answered from the same snapshot the dashboard renders (ADR-010).

Every answer has the same envelope:
  {"query", "args", "as_of", "repository", "answer", "signals", "evidence_note"}
The MCP tool contract (docs/demo/agent-contract.md) maps 1:1 onto these functions.
"""

from __future__ import annotations

from .derive import parse_time

NOTE = ("Derived from GitHub metadata. 'basis' says whether a signal is derived, heuristic or declared; "
        "follow evidence URLs before acting. Observstory describes work, not people.")


def _envelope(snapshot, name, args, answer, signals=()):
    return {
        "query": name, "args": args, "as_of": snapshot["generated_at"],
        "repository": snapshot["repository"]["full_name"],
        "answer": answer, "signals": list(signals), "evidence_note": NOTE,
    }


def _touches(path_or_area: str, candidate: str) -> bool:
    a, b = path_or_area.rstrip("/"), candidate.rstrip("/")
    return a == b or b.startswith(a + "/") or a.startswith(b + "/")


def _brief(w):
    return {k: w.get(k) for k in ("id", "kind", "title", "url", "state", "actors", "last_activity_at",
                                  "review_state", "waiting_on", "areas")}


def _signals_for(snapshot, work_ids=(), areas=()):
    work_ids, areas = set(work_ids), set(areas)
    return [s for s in snapshot["signals"]
            if set(s["work_items"]) & work_ids or (s["subject"]["kind"] == "area" and s["subject"]["id"] in areas)]


def changes_since(snapshot, since: str):
    """What changed since my last run?"""
    t = parse_time(since)
    commits = [c for c in snapshot["commits"] if c["date"] and parse_time(c["date"]) > t]
    items = [_brief(w) for w in snapshot["work_items"]
             if w["last_activity_at"] and parse_time(w["last_activity_at"]) > t]
    ids = [w["id"] for w in items]
    return _envelope(snapshot, "changes_since", {"since": since}, {
        "work_items": items,
        "commits_on_default_branch": [{k: c[k] for k in ("sha", "url", "message", "date", "areas", "work_item")}
                                      for c in commits],
        "areas_touched": sorted({a for w in items for a in w["areas"]} | {a for c in commits for a in c["areas"]}),
    }, _signals_for(snapshot, ids))


def work_near(snapshot, paths: list[str]):
    """Who and what is active around these paths? Also answers 'what overlaps my proposed task?'."""
    items = [w for w in snapshot["work_items"]
             if (w["in_flight"] or w["kind"] == "direct")
             and any(_touches(p, q) for p in paths for q in w["paths"] + w["areas"])]
    areas = [a for a in snapshot["areas"] if any(_touches(p, a["id"]) for p in paths)]
    shared_files = sorted({q for w in items for q in w["paths"] if q in paths})
    return _envelope(snapshot, "work_near", {"paths": paths}, {
        "in_flight": [_brief(w) for w in items],
        "areas": [{k: a[k] for k in ("id", "lane", "in_flight", "recent_commits")} for a in areas],
        "authors_of_active_work": sorted({x for w in items for x in w["actors"]}),
        "exact_file_matches": shared_files,
        "coordination_needed": bool(items),
    }, _signals_for(snapshot, [w["id"] for w in items], [a["id"] for a in areas]))


def overlaps(snapshot, path: str | None = None):
    sigs = [s for s in snapshot["signals"] if s["type"] == "overlap"
            and (path is None or _touches(path, s["subject"]["id"]))]
    return _envelope(snapshot, "overlaps", {"path": path}, {"count": len(sigs)}, sigs)


def open_loops(snapshot):
    """Stale work, branches without PRs, work waiting on other work, PRs with no reviewer."""
    sigs = [s for s in snapshot["signals"] if s["type"] in ("stale", "waiting")]
    no_reviewer = [_brief(w) for w in snapshot["work_items"] if w.get("review_state") == "no_reviewer"]
    unproposed = [_brief(w) for w in snapshot["work_items"] if w["state"] == "unproposed"]
    return _envelope(snapshot, "open_loops", {}, {
        "stale": [s["subject"]["id"] for s in sigs if s["type"] == "stale"],
        "waiting": [{"work_item": s["work_items"][0], "waits_on": s["work_items"][1], "basis": s["basis"]}
                    for s in sigs if s["type"] == "waiting"],
        "open_prs_without_reviewer": no_reviewer,
        "branches_without_pr": unproposed,
    }, sigs)


def handoff(snapshot):
    """What is ready for handoff? Uses only the author's declared review state."""
    groups = {"review_requested": [], "no_reviewer": [], "draft": []}
    for w in snapshot["work_items"]:
        if w.get("review_state") in groups:
            groups[w["review_state"]].append(_brief(w))
    return _envelope(snapshot, "handoff", {}, {
        "ready_for_review": groups["review_requested"],
        "open_without_reviewer": groups["no_reviewer"],
        "draft": groups["draft"],
        "note": "Readiness is the author's declaration (draft flag, requested reviewers), not an inference.",
    })


def coordination(snapshot):
    """What did the team declare, and how does the repository compare? Declared items only (ADR-029, ADR-030)."""
    c = snapshot.get("coordination")
    if not c:
        return _envelope(snapshot, "coordination", {}, {
            "declared": False, "note": "No .observstory/coordination.json: nothing has been declared."})
    return _envelope(snapshot, "coordination", {}, {
        "declared": True, "next_gate": next((g for g in c["gates"] if g.get("next")), None),
        "gates": c["gates"], "commitments": c["commitments"], "decisions": c["decisions"], "cues": c["cues"],
        "proposed_pending": c["proposed_pending"],
        "note": "Declared means confirmed by a named person. Commitment states come from repository evidence; "
                "cues compare the two and say nothing about people.",
    })


QUERIES = {
    "changes-since": changes_since,
    "work-near": work_near,
    "overlaps": overlaps,
    "open-loops": open_loops,
    "handoff": handoff,
    "coordination": coordination,
}
