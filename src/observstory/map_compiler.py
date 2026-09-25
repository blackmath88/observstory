"""Project Map compiler: snapshot v1 -> scene v1 (docs/ui/scene-grammar.md).

The compiler decides *what* the map shows and how it is grouped; the renderer only decides
*where* things land on screen. Pure and deterministic: no clock, no network, same snapshot in,
same scene out.

Grammar (kept deliberately small):
  zone   a lane, in configured order
  group  an area inside a zone that has something to show
  node   a work item, placed once, in its primary area
  edge   a relationship between two nodes (overlap, waiting)
plus `attention` (ordered references to the things that deserve a conversation) and `details`
(the evidence payload the inspector reveals on demand).
"""

from __future__ import annotations

from .derive import parse_time

SCENE_SCHEMA = "observstory.scene/v1"
LEVELS = {"low": 0, "medium": 1, "high": 2}


def _in_area(path: str, area: str) -> bool:
    return path == area or path.startswith(area + "/")


def _age_hours(ts: str | None, now) -> float | None:
    t = parse_time(ts)
    return None if t is None else round(max(0.0, (now - t).total_seconds() / 3600), 1)


def _ref(w: dict) -> str:
    if w["kind"] == "pull_request":
        return f"#{w['number']}"
    if w["kind"] == "branch":
        return w["head"] or w["id"].split(":", 1)[1]
    return "landed on " + (w.get("head") or "default branch")


def primary_area(w: dict, lane_order: dict, area_lane: dict) -> str | None:
    """The area where the item changes the most files; ties go to the earlier lane, then the path."""
    if not w["areas"]:
        return None
    counts = {a: sum(1 for p in w["paths"] if _in_area(p, a)) for a in w["areas"]}
    return min(w["areas"], key=lambda a: (-counts[a], lane_order.get(area_lane.get(a), 99), a))


def compile_scene(snap: dict) -> dict:
    now = parse_time(snap["generated_at"])
    lanes = snap["lanes"]
    lane_order = {lane["id"]: i for i, lane in enumerate(lanes)}
    areas = {a["id"]: a for a in snap["areas"]}
    area_lane = {a["id"]: a["lane"] for a in snap["areas"]}
    items = {w["id"]: w for w in snap["work_items"]}
    signals = snap["signals"]
    stale_ids = {s["subject"]["id"] for s in signals if s["type"] == "stale"}
    waiting_ids = {s["work_items"][0] for s in signals if s["type"] == "waiting"}
    burst_ids = {s["subject"]["id"] for s in signals if s["type"] == "burst"}

    # --- edges ------------------------------------------------------------------------------
    edges: dict[str, dict] = {}
    for s in signals:
        if s["type"] == "overlap":
            files_by_pair: dict[tuple, set] = {}
            for e in s["evidence"]:
                if e["kind"] == "file":
                    owners = sorted(e.get("work_items", []))
                    for i, a in enumerate(owners):
                        for b in owners[i + 1:]:
                            files_by_pair.setdefault((a, b), set()).add(e["ref"])
            for pair in s["rule"]["params"].get("parallel_pairs", []):
                a, b = sorted(pair.split("|"))
                eid = f"overlap:{a}|{b}"
                edge = edges.setdefault(eid, {
                    "id": eid, "type": "overlap", "from": a, "to": b, "directed": False,
                    "basis": s["basis"], "confidence": s["confidence"], "attention": True,
                    "areas": [], "files": [], "signals": []})
                edge["areas"].append(s["subject"]["id"])
                edge["signals"].append(s["id"])
                edge["files"] = sorted(set(edge["files"]) | files_by_pair.get((a, b), set()))
                if LEVELS[s["confidence"]] > LEVELS[edge["confidence"]]:
                    edge["confidence"] = s["confidence"]
                if s["basis"] == "derived":
                    edge["basis"] = "derived"
        elif s["type"] == "waiting":
            waiter, blocker = s["work_items"]
            eid = f"waiting:{waiter}>{blocker}"
            edges[eid] = {"id": eid, "type": "waiting", "from": waiter, "to": blocker, "directed": True,
                          "basis": s["basis"], "confidence": s["confidence"], "attention": True,
                          "areas": [], "files": [], "signals": [s["id"]]}
    edge_list = sorted(edges.values(), key=lambda e: (e["type"] != "overlap", -LEVELS[e["confidence"]], e["id"]))

    # --- nodes: in-flight work, plus landed work only where it takes part in a relationship ---
    in_edge = {x for e in edge_list for x in (e["from"], e["to"])}
    shown = [w for w in snap["work_items"] if w["in_flight"] or w["id"] in in_edge]
    nodes = []
    for w in shown:
        if w["kind"] == "direct":
            areas_here = [a for e in edge_list if w["id"] in (e["from"], e["to"]) for a in e["areas"]]
            group_area = sorted(areas_here, key=lambda a: (lane_order.get(area_lane.get(a), 99), a))[0]
        else:
            group_area = primary_area(w, lane_order, area_lane)
        if group_area is None:
            continue
        status = ("landed" if w["kind"] == "direct" else "stale" if w["id"] in stale_ids
                  else "draft" if w["state"] == "draft" else "in_flight")
        nodes.append({
            "id": w["id"], "kind": w["kind"], "group": f"area:{group_area}", "zone": area_lane[group_area],
            "ref": _ref(w), "label": w["title"], "url": w["url"], "status": status,
            "review_state": w.get("review_state"), "actors": w["actors"],
            "last_activity_at": w["last_activity_at"], "age_hours": _age_hours(w["last_activity_at"], now),
            "also_touches": [a for a in w["areas"] if a != group_area],
            "flags": sorted(f for f, on in (("waiting", w["id"] in waiting_ids), ("burst", w["id"] in burst_ids),
                                            ("agent", w["agent_declared"]),
                                            ("unproposed", w["state"] == "unproposed")) if on),
            "attention": w["id"] in in_edge or w["id"] in stale_ids,
        })
    # recency order inside a group: most recent first, stale and landed work recedes to the end
    rank = {"in_flight": 0, "draft": 1, "landed": 2, "stale": 3}
    nodes.sort(key=lambda n: (n["group"], rank[n["status"]], n["age_hours"] if n["age_hours"] is not None else 1e9, n["id"]))

    # --- groups: every area touched by a shown node; the node itself is drawn once ------------
    attention_areas = {a for e in edge_list if e["type"] == "overlap" for a in e["areas"]}
    by_group: dict[str, list] = {}
    touching: dict[str, set] = {}
    for n in nodes:
        by_group.setdefault(n["group"], []).append(n["id"])
        w = items[n["id"]]
        touched = ([a for e in edge_list if n["id"] in (e["from"], e["to"]) for a in e["areas"]]
                   if w["kind"] == "direct" else w["areas"])
        for a in touched:
            touching.setdefault(f"area:{a}", set()).add(n["id"])
    for gid in touching:
        by_group.setdefault(gid, [])
    groups = []
    for gid, node_ids in by_group.items():
        area = areas[gid[5:]]
        placed_elsewhere = sorted(touching.get(gid, set()) - set(node_ids))
        groups.append({
            "id": gid, "zone": area["lane"], "path": area["id"], "label": area["id"].rsplit("/", 1)[-1],
            "parent": area["id"].rsplit("/", 1)[0] if "/" in area["id"] else "",
            "attention": area["id"] in attention_areas, "nodes": node_ids, "also_active": placed_elsewhere,
            "recent_commits": area["recent_commits"], "last_activity_at": area["last_activity_at"],
            "age_hours": _age_hours(area["last_activity_at"], now),
        })
    groups.sort(key=lambda g: (lane_order.get(g["zone"], 99), not g["attention"], -len(g["nodes"]),
                               -len(g["also_active"]), g["age_hours"] if g["age_hours"] is not None else 1e9, g["path"]))

    # --- zones --------------------------------------------------------------------------------
    zones = []
    for i, lane in enumerate(lanes):
        gids = [g["id"] for g in groups if g["zone"] == lane["id"]]
        quiet_areas = sorted(a for a in lane["areas"] if f"area:{a}" not in by_group and areas[a]["recent_commits"])
        zones.append({
            "id": lane["id"], "label": lane["label"], "description": lane.get("description", ""), "order": i,
            "state": "active" if gids else "quiet", "groups": gids,
            "in_flight": len({w for g in groups if g["zone"] == lane["id"] for w in g["nodes"] + g["also_active"]
                              if items[w]["in_flight"]}),
            "attention": any(g["attention"] for g in groups if g["zone"] == lane["id"]),
            "recently_changed": quiet_areas[:6], "recently_changed_more": max(0, len(quiet_areas) - 6),
        })

    # --- attention: what deserves a conversation, most important first ------------------------
    attention = []
    for e in edge_list:
        if e["type"] == "overlap":
            where = ", ".join(e["areas"][:2]) + (f" +{len(e['areas']) - 2}" if len(e["areas"]) > 2 else "")
            attention.append({"kind": "overlap", "target": e["id"], "confidence": e["confidence"], "basis": e["basis"],
                              "label": f"{_ref(items[e['from']])} and {_ref(items[e['to']])} change {where} in parallel"})
    for e in edge_list:
        if e["type"] == "waiting":
            attention.append({"kind": "waiting", "target": e["id"], "confidence": e["confidence"], "basis": e["basis"],
                              "label": f"{_ref(items[e['from']])} waits on {_ref(items[e['to']])}"})
    for s in sorted((s for s in signals if s["type"] == "stale"), key=lambda s: -s["rule"]["params"]["idle_hours"]):
        w = items[s["subject"]["id"]]
        attention.append({"kind": "stale", "target": w["id"], "confidence": s["confidence"], "basis": s["basis"],
                          "label": f"{_ref(w)} idle for {s['summary'].split(' idle for ')[-1]}"})

    # --- details: the inspector's evidence payload, revealed on demand ------------------------
    shown_ids = {n["id"] for n in nodes}
    details = {
        "signals": {s["id"]: {k: s[k] for k in ("type", "summary", "basis", "confidence", "evidence", "rule", "work_items")}
                    for s in signals if set(s["work_items"]) & shown_ids},
        "work_items": {w["id"]: {"paths": w["paths"][:40], "paths_total": len(w["paths"]), "areas": w["areas"],
                                 "state": w["state"], "burst": w.get("burst"), "merge_base": w.get("merge_base"),
                                 "commit_count": w["commit_count"], "waiting_on": w["waiting_on"]}
                       for w in snap["work_items"] if w["id"] in shown_ids},
        "areas": {g["path"]: {"files": areas[g["path"]]["files"][:40], "actors": areas[g["path"]]["actors"],
                              "recent_commits": areas[g["path"]]["recent_commits"]} for g in groups},
    }

    coordination = compile_coordination(snap.get("coordination"))
    if coordination:
        for q in coordination["cues"]:
            attention.append({"kind": "declared", "target": q["subject"]["id"], "confidence": q["confidence"],
                              "basis": "declared", "label": q["summary"]})

    summary = snap["summary"]["signals"]
    return {
        "schema": SCENE_SCHEMA,
        "source": {"snapshot_schema": snap["schema"], "generated_at": snap["generated_at"],
                   "repository": snap["repository"]["full_name"], "repository_url": snap["repository"].get("url"),
                   "default_branch": snap["repository"]["default_branch"], "window_hours": snap["window"]["hours"],
                   "title": snap["config"].get("title"), "lanes_source": snap["config"].get("lanes_source"),
                   "degraded": snap["provenance"]["degraded"]},
        "status": {"in_flight": snap["summary"]["in_flight"], "overlaps": sum(1 for e in edge_list if e["type"] == "overlap"),
                   "waiting": summary["waiting"], "stale": summary["stale"],
                   "areas_active": snap["summary"]["areas_active"]},
        "zones": zones, "groups": groups, "nodes": nodes, "edges": edge_list,
        "attention": attention, "details": details,
        "coordination": coordination,
    }


def compile_coordination(c: dict | None) -> dict | None:
    """The mission rail: declared gates, check-ins and commitment due times, with their observed state.
    Declared items stay out of the lane cards (principle: declared intent is not observed reality)."""
    if not c:
        return None
    now = parse_time(c["now"])
    times = [now] + [parse_time(x["at"]) for x in c["sessions"] + c["gates"]] \
        + [parse_time(x["due"]) for x in c["commitments"] if x.get("due")]
    start, end = min(times), max(times)
    end = end + (end - start) * 0.03  # a little room after the last marker
    nxt = next((g for g in c["gates"] if g["next"]), None)
    cue_of = {q["subject"]["id"]: q["id"] for q in c["cues"]}
    return {
        "source": c["source"], "now": c["now"],
        "span": [start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")],
        "next_gate": nxt["id"] if nxt else None,
        "hours_to_next": round((parse_time(nxt["at"]) - now).total_seconds() / 3600, 1) if nxt else None,
        "proposed_pending": c["proposed_pending"],
        "sessions": [{k: x.get(k) for k in ("id", "kind", "label", "at", "open_questions")} for x in c["sessions"]],
        "gates": [dict({k: g.get(k) for k in ("id", "kind", "label", "at", "areas", "passed", "next", "confirmed_by")},
                       session=g.get("source", {}).get("session"), cue=cue_of.get(g["id"])) for g in c["gates"]],
        "commitments": [dict({k: x.get(k) for k in ("id", "text", "owner", "due", "state", "matched", "links", "confirmed_by")},
                             session=x.get("source", {}).get("session"), cue=cue_of.get(x["id"])) for x in c["commitments"]],
        "decisions": [dict({k: x.get(k) for k in ("id", "text", "areas", "changed_after", "confirmed_by")},
                           session=x.get("source", {}).get("session")) for x in c["decisions"]],
        "cues": c["cues"],
    }
