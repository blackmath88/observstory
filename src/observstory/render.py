"""Radar dashboard: a projection of snapshot v1. Computes nothing that isn't in the snapshot,
apart from presentation (relative times, geometry).

Design language: docs/development/ui-language.md
"""

from __future__ import annotations

import html
import json
import math

from .derive import parse_time

CONF_DASH = {"high": "", "medium": "4 3", "low": "1.5 3"}
CONF_GLYPH = {"high": "●", "medium": "◐", "low": "○"}
GROUPS = [
    ("Coordination", "Areas touched by more than one work item that is in flight or recent", ("overlap",)),
    ("Open loops", "Work that has stopped moving or is waiting on other work", ("stale", "waiting")),
    ("Change streams", "Machine-paced commit streams, folded so they read as one unit", ("burst",)),
]


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def rel(ts: str | None, now) -> str:
    t = parse_time(ts)
    if not t:
        return "—"
    hours = (now - t).total_seconds() / 3600
    if hours < 1:
        return f"{max(0, round(hours * 60))}m ago"
    if hours < 48:
        return f"{round(hours)}h ago"
    return f"{round(hours / 24)}d ago"


def slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()


def link(url, text, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{esc(url)}">{esc(text)}</a>' if url else f"<span{c}>{esc(text)}</span>"


# ---------------------------------------------------------------- radar

def radar_svg(snap: dict) -> str:
    now = parse_time(snap["generated_at"])
    window = float(snap["window"]["hours"])
    size, cx, cy, R = 620, 310, 300, 214
    r0 = 0.3 * R  # an inner band, so "just now" still has room to spread by angle

    def radius(hours: float) -> float:
        # log scale: the last few hours get most of the room, where real activity concentrates
        return r0 + (R - r0) * math.log1p(min(max(hours, 0.0), window)) / math.log1p(window)

    overlap_by_area = {s["subject"]["id"]: s for s in snap["signals"] if s["type"] == "overlap"}
    lanes = [lane for lane in snap["lanes"] if lane["areas"]]
    areas = {a["id"]: a for a in snap["areas"]}
    parts = [f'<svg class="radar" viewBox="0 0 {size} {size}" role="img" '
             f'aria-labelledby="radar-title radar-desc">'
             f'<title id="radar-title">Project radar</title>'
             f'<desc id="radar-desc">Sectors are lanes, marks are areas. Distance from centre is time since last '
             f'activity (centre is now, the edge is {int(window)} hours or more). Filled marks have work in flight; '
             f'rings mark overlap.</desc>']
    marks = [1, 6, 24, window] if window > 24 else [1, 3, 12, window]
    for h in marks:
        r = radius(h)
        parts.append(f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r:.1f}"/>')
        parts.append(f'<text class="ring-label" x="{cx + 4}" y="{cy - r + 11:.1f}">{h:g}h</text>')
    parts.append(f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r0:.1f}" stroke-dasharray="2 4"/>')
    parts.append(f'<circle class="now" cx="{cx}" cy="{cy}" r="3"/>')
    if not lanes:
        parts.append(f'<text class="empty" x="{cx}" y="{cy + 40}" text-anchor="middle">No activity in this window</text>')
    placed: list[tuple[float, float, float]] = []  # (x_left, x_right, y) of labels already drawn

    def free_y(x0: float, x1: float, y: float) -> float:
        for _ in range(8):
            if not any(a < x1 and x0 < b and abs(y - yy) < 13 for a, b, yy in placed):
                break
            y += 13
        placed.append((x0, x1, y))
        return y

    span = 2 * math.pi / max(1, len(lanes))
    for li, lane in enumerate(lanes):
        start = -math.pi / 2 + li * span
        x2, y2 = cx + (R + 8) * math.cos(start), cy + (R + 8) * math.sin(start)
        if len(lanes) > 1:
            parts.append(f'<line class="sector" x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
        mid = start + span / 2
        lx, ly = cx + (R + 26) * math.cos(mid), cy + (R + 26) * math.sin(mid)
        anchor = "middle" if abs(math.cos(mid)) < 0.3 else ("start" if math.cos(mid) > 0 else "end")
        parts.append(f'<text class="lane-label" x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="{anchor}">'
                     f'{esc(lane["label"].upper())}</text>')
        ids = sorted(lane["areas"], key=lambda a: (-len(areas[a]["in_flight"]), a))
        for ai, area_id in enumerate(ids):
            area = areas[area_id]
            angle = start + span * (ai + 1) / (len(ids) + 1)
            last = parse_time(area.get("last_activity_at"))
            hours = (now - last).total_seconds() / 3600 if last else window
            r = radius(hours)
            x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
            n = len(area["in_flight"])
            live = n > 0
            dot = 3.5 + 1.8 * min(n, 4) if live else 3
            tip = f'{area_id} · lane {lane["label"]} · {n} active work item(s) · last activity {rel(area.get("last_activity_at"), now)}'
            parts.append(f'<a href="#area-{slug(area_id)}"><g class="area{" live" if live else ""}">'
                         f'<title>{esc(tip)}</title>'
                         f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="{dot + 8:.1f}"/>')
            sig = overlap_by_area.get(area_id)
            if sig:
                parts.append(f'<circle class="overlap-ring" cx="{x:.1f}" cy="{y:.1f}" r="{dot + 5:.1f}" '
                             f'stroke-dasharray="{CONF_DASH[sig["confidence"]]}"/>')
            parts.append(f'<circle class="mark" cx="{x:.1f}" cy="{y:.1f}" r="{dot:.1f}"/>')
            if sig or n >= 2:  # label what needs attention; everything else is on hover and in the lane list
                lr = r + dot + 8
                tx, ty = cx + lr * math.cos(angle), cy + lr * math.sin(angle)
                anchor = "middle" if abs(math.cos(angle)) < 0.25 else ("start" if math.cos(angle) > 0 else "end")
                width = 6.7 * len(area_id)
                x0 = {"start": tx, "end": tx - width, "middle": tx - width / 2}[anchor]
                ty = free_y(x0, x0 + width, ty)
                parts.append(f'<text class="area-label{" hot" if sig else ""}" x="{tx:.1f}" y="{ty + 4:.1f}" '
                             f'text-anchor="{anchor}">{esc(area_id)}</text>')
            parts.append("</g></a>")
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------- panels

def signal_block(s: dict, items: dict, nested: bool = False) -> str:
    ev = []
    for e in s["evidence"]:
        if e["kind"] == "work_item":
            w = items.get(e["ref"], {})
            ev.append(f'<li><span class="k">work</span>{link(e.get("url"), e["ref"], "mono")}'
                      f'<span class="d">{esc(w.get("title", ""))} · {esc(", ".join(w.get("actors", [])))}</span></li>')
        elif e["kind"] == "file":
            ev.append(f'<li><span class="k">file</span><code>{esc(e["ref"])}</code>'
                      f'<span class="d">{esc(", ".join(e.get("work_items", [])))}</span></li>')
        else:
            ev.append(f'<li><span class="k">{esc(e["kind"])}</span>{link(e.get("url"), e["ref"], "mono")}'
                      f'<span class="d">{esc(e.get("detail", ""))}</span></li>')
    params = ", ".join(f"{k}={v}" for k, v in s["rule"]["params"].items() if v not in ([], None))
    opened = " open" if s["type"] == "overlap" and s["confidence"] != "low" and not nested else ""
    return (f'<details class="signal {esc(s["type"])}" id="sig-{slug(s["id"])}"{opened}>'
            f'<summary><span class="conf c-{s["confidence"]}" title="confidence: {s["confidence"]}">'
            f'{CONF_GLYPH[s["confidence"]]}</span><span class="sum">{esc(s["summary"])}</span>'
            f'<span class="tag">{esc(s["basis"])}</span></summary>'
            f'<ul class="evidence">{"".join(ev)}</ul>'
            f'<p class="rule">rule <code>{esc(s["rule"]["name"])}</code>'
            f'{" · " + esc(params) if params else ""} · confidence {esc(s["confidence"])}</p></details>')


def overlap_clusters(sigs: list[dict], items: dict) -> str:
    """Overlaps between the same set of work items read as one relationship across several areas.
    Dogfooding showed 9 per-area signals for one branch against one push stream (signal fatigue, R16).
    The snapshot keeps one signal per area; only the presentation groups them."""
    clusters: dict[tuple, list[dict]] = {}
    for s in sigs:
        clusters.setdefault(tuple(s["work_items"]), []).append(s)
    out = []
    for members, group in clusters.items():
        if len(group) == 1:
            out.append(signal_block(group[0], items))
            continue
        top = max(group, key=lambda s: ["low", "medium", "high"].index(s["confidence"]))
        areas = ", ".join(s["subject"]["id"] for s in group)
        inner = "".join(signal_block(s, items, nested=True) for s in group)
        out.append(f'<details class="signal overlap cluster" open><summary><span class="conf c-{top["confidence"]}">'
                   f'{CONF_GLYPH[top["confidence"]]}</span><span class="sum">{" × ".join(esc(m) for m in members)} '
                   f'overlap in {len(group)} areas</span><span class="tag">{len(group)} signals</span></summary>'
                   f'<p class="rule">{esc(areas)}</p><div class="nested">{inner}</div></details>')
    return "".join(out)


def render(snap: dict) -> str:
    now = parse_time(snap["generated_at"])
    items = {w["id"]: w for w in snap["work_items"]}
    summary, repo, prov = snap["summary"], snap["repository"], snap["provenance"]
    title = snap["config"].get("title") or "Project Observatory"

    groups = []
    for label, blurb, types in GROUPS:
        sigs = [s for s in snap["signals"] if s["type"] in types]
        if types == ("overlap",):
            body = overlap_clusters(sigs, items)
        else:
            body = "".join(signal_block(s, items) for s in sigs)
        groups.append(f'<section class="group"><h3>{label} <span class="n">{len(sigs)}</span></h3>'
                      f'<p class="blurb">{blurb}</p>{body or "<p class=quiet>Nothing here.</p>"}</section>')

    overlap_areas = {s["subject"]["id"] for s in snap["signals"] if s["type"] == "overlap"}
    areas = {a["id"]: a for a in snap["areas"]}
    lane_cards = []
    for lane in snap["lanes"]:
        chips = "".join(
            f'<li id="area-{slug(a)}" class="chip{" hot" if a in overlap_areas else ""}{" live" if areas[a]["in_flight"] else ""}">'
            f'<code>{esc(a)}</code><span>{len(areas[a]["in_flight"]) or ""}</span></li>'
            for a in sorted(lane["areas"], key=lambda a: (-len(areas[a]["in_flight"]), a))
        ) or '<li class="quiet">No activity in this window.</li>'
        lane_cards.append(f'<article class="lane"><header><h4>{esc(lane["label"])}</h4>'
                          f'<span class="n">{len(lane["in_flight"])} active</span></header>'
                          f'<p>{esc(lane.get("description", ""))}</p><ul class="chips">{chips}</ul></article>')

    rows = []
    for w in snap["work_items"]:
        if not (w["in_flight"] or w["kind"] == "direct"):
            continue
        notes = []
        if w["waiting_on"]:
            notes.append("waits on " + ", ".join(w["waiting_on"]))
        if w.get("burst"):
            notes.append(f'{w["commit_count"]} commits · burst of {w["burst"]["commits"]} in {w["burst"]["minutes"]} min')
        if w["agent_declared"]:
            notes.append("agent-assisted (declared)")
        state = w["state"] + (f' · {w["review_state"].replace("_", " ")}' if w.get("review_state") and w["review_state"] != "draft" else "")
        rows.append(f'<tr><td>{link(w["url"], w["id"], "mono")}<div class="t">{esc(w["title"])}</div></td>'
                    f'<td><span class="state s-{esc(w["state"])}">{esc(state)}</span></td>'
                    f'<td>{"".join(f"<code>{esc(a)}</code> " for a in w["areas"])}</td>'
                    f'<td class="muted">{esc(", ".join(w["actors"]))}</td>'
                    f'<td class="muted nowrap">{rel(w["last_activity_at"], now)}</td>'
                    f'<td class="muted">{esc("; ".join(notes))}</td></tr>')
    work_table = ("<table><thead><tr><th>Work item</th><th>State</th><th>Areas</th><th>Authors</th>"
                  "<th>Last activity</th><th>Notes</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
                  ) if rows else '<p class="quiet">No work in flight.</p>'

    commits = snap["commits"][:14]
    flow = "".join(f'<li>{link(c["url"], c["sha"][:7], "mono")}<span class="msg">{esc(c["message"])}</span>'
                   f'<span class="muted nowrap">{esc(", ".join(c["areas"][:3]))} · {rel(c["date"], now)}</span></li>'
                   for c in commits) or '<li class="quiet">No commits on the default branch in this window.</li>'
    if len(snap["commits"]) > 14:
        flow += f'<li class="quiet">+{len(snap["commits"]) - 14} more in snapshot.json</li>'
    issues = "".join(f'<li>{link(i["url"], "#" + str(i["number"]), "mono")}<span class="msg">{esc(i["title"])}</span></li>'
                     for i in [i for i in snap["issues"] if i["state"] == "open"][:8]) or '<li class="quiet">No open issues in view.</li>'

    degraded = ""
    if prov["degraded"]:
        degraded = '<p class="warn">Partial data: ' + esc("; ".join(prov["degraded"])) + "</p>"
    sig_counts = summary["signals"]
    raw = json.dumps(snap, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Observstory · {esc(repo["full_name"])}</title>
<style>
:root{{--bg:#f3f2ee;--panel:#fbfaf7;--ink:#1c1d1f;--muted:#66686b;--faint:#a9a8a2;--line:#dddbd3;
--mark:#2f5467;--accent:#b4530a;--accent-soft:#f6e7d8;--warn:#8a5a00}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0e1113;--panel:#14191c;--ink:#e5e3dd;
--muted:#8d9295;--faint:#4a5155;--line:#252c30;--mark:#8db5c9;--accent:#f09a45;--accent-soft:#3a2716;--warn:#e0b25a}}}}
:root[data-theme="dark"]{{--bg:#0e1113;--panel:#14191c;--ink:#e5e3dd;--muted:#8d9295;--faint:#4a5155;--line:#252c30;
--mark:#8db5c9;--accent:#f09a45;--accent-soft:#3a2716;--warn:#e0b25a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 ui-sans-serif,-apple-system,"Segoe UI",Inter,sans-serif}}
main{{max-width:1320px;margin:auto;padding:28px 24px 40px}}
a{{color:inherit;text-decoration:underline;text-decoration-color:var(--faint);text-underline-offset:2px}}
a:hover{{text-decoration-color:var(--ink)}}
code,.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px}}
.eyebrow{{font:600 11px/1 ui-monospace,Menlo,monospace;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}}
header.top{{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;border-bottom:1px solid var(--line);padding-bottom:18px}}
h1{{font-size:clamp(26px,4vw,40px);font-weight:600;letter-spacing:-.02em;margin:8px 0 4px}}
h2{{font-size:13px;font-weight:600;margin:0 0 12px;letter-spacing:.02em}}
h3{{font-size:14px;font-weight:600;margin:0}} h4{{margin:0;font-size:14px;font-weight:600}}
.meta{{text-align:right;color:var(--muted);font-size:12px;line-height:1.6}}
.readout{{display:flex;flex-wrap:wrap;gap:28px;padding:16px 0;border-bottom:1px solid var(--line);margin-bottom:22px}}
.readout div{{display:flex;flex-direction:column;gap:2px}}
.readout strong{{font:500 24px/1.1 ui-monospace,Menlo,monospace;letter-spacing:-.02em}}
.readout .hot strong{{color:var(--accent)}}
.grid{{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:28px;align-items:start}}
.radar-wrap{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}}
.radar{{width:100%;height:auto;display:block}}
.ring{{fill:none;stroke:var(--line)}} .sector{{stroke:var(--line)}} .now{{fill:var(--muted)}}
.ring-label{{fill:var(--faint);font:10px ui-monospace,Menlo,monospace}}
.lane-label{{fill:var(--muted);font:600 10px ui-monospace,Menlo,monospace;letter-spacing:.12em}}
.empty{{fill:var(--muted);font-size:12px}}
.area .mark{{fill:none;stroke:var(--faint);stroke-width:1.5}} .area.live .mark{{fill:var(--mark);stroke:var(--panel);stroke-width:2}}
.area .hit{{fill:transparent}} .area:hover .mark{{stroke:var(--ink)}}
.overlap-ring{{fill:none;stroke:var(--accent);stroke-width:2}}
.area-label{{fill:var(--muted);font:11px ui-monospace,Menlo,monospace}} .area-label.hot{{fill:var(--accent);font-weight:600}}
.legend{{display:flex;flex-wrap:wrap;gap:16px;color:var(--muted);font-size:12px;margin:10px 4px 0}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}}
.lg-live{{background:var(--mark)}} .lg-idle{{border:1.5px solid var(--faint)}} .lg-ov{{border:2px solid var(--accent)}}
.group{{margin-bottom:22px}} .group h3 .n,.lane .n{{font:12px ui-monospace,Menlo,monospace;color:var(--muted);margin-left:6px}}
.blurb{{color:var(--muted);font-size:12px;margin:2px 0 8px}}
.signal{{border-top:1px solid var(--line)}} .signal:last-child{{border-bottom:1px solid var(--line)}}
.signal summary{{display:flex;gap:10px;align-items:baseline;padding:9px 2px;cursor:pointer;list-style:none}}
.signal summary::-webkit-details-marker{{display:none}}
.signal summary:hover{{background:var(--panel)}}
.sum{{flex:1}} .overlap .sum{{font-weight:500}}
.conf{{font-size:12px;color:var(--accent);width:12px}} .stale .conf,.burst .conf,.waiting .conf{{color:var(--muted)}}
.tag{{font:11px ui-monospace,Menlo,monospace;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:0 5px}}
.evidence{{list-style:none;margin:0 0 6px 22px;padding:0}}
.evidence li{{display:grid;grid-template-columns:44px auto 1fr;gap:10px;padding:3px 0;font-size:13px;align-items:baseline}}
.evidence .k{{font:10px ui-monospace,Menlo,monospace;color:var(--faint);text-transform:uppercase;letter-spacing:.08em}}
.evidence .d{{color:var(--muted);font-size:12px}}
.rule{{margin:0 0 10px 22px;color:var(--faint);font-size:11px}}
.quiet{{color:var(--muted);font-size:13px}}
.nested{{margin-left:22px}} .nested .signal summary{{padding:6px 2px}} .nested .sum{{font-weight:400}}
section.band{{margin-top:34px}}
.lanes{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.lane{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}}
.lane header{{display:flex;justify-content:space-between;align-items:baseline}}
.lane p{{color:var(--muted);font-size:12px;margin:4px 0 10px}}
.chips{{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}}
.chip{{display:flex;gap:6px;align-items:center;border:1px solid var(--line);border-radius:5px;padding:2px 7px;color:var(--muted)}}
.chip.live{{color:var(--ink);border-color:var(--faint)}} .chip.hot{{border-color:var(--accent);background:var(--accent-soft)}}
.chip span{{font:11px ui-monospace,Menlo,monospace;color:var(--muted)}}
.chip:target{{outline:2px solid var(--accent);outline-offset:2px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;font:600 10px ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:6px 8px;border-bottom:1px solid var(--line)}}
td{{padding:8px;border-bottom:1px solid var(--line);vertical-align:top}} td .t{{color:var(--muted);font-size:12px}}
.state{{font:11px ui-monospace,Menlo,monospace}} .s-unproposed,.s-draft{{color:var(--muted)}}
.muted{{color:var(--muted)}} .nowrap{{white-space:nowrap}}
.table-wrap{{overflow-x:auto}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:28px}}
ul.flow{{list-style:none;margin:0;padding:0}}
ul.flow li{{display:flex;gap:10px;align-items:baseline;padding:6px 0;border-bottom:1px solid var(--line)}}
ul.flow .msg{{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.warn{{color:var(--warn);font-size:12px}}
footer{{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}}
@media(max-width:900px){{.grid,.two{{grid-template-columns:1fr}} header.top{{display:block}} .meta{{text-align:left;margin-top:10px}} main{{padding:18px 16px}}}}
</style>
</head>
<body>
<main>
<header class="top">
  <div><span class="eyebrow">Observstory · in-flight project state</span>
  <h1>{esc(repo["full_name"])}</h1>
  <div class="muted">{esc(title)} · last {snap["window"]["hours"]:g} hours</div></div>
  <div class="meta">generated {esc(snap["generated_at"])}<br>trigger {esc(snap.get("trigger", {}).get("event", "—"))} ·
  config {esc(snap["config"]["source"])} · lanes {esc(snap["config"].get("lanes_source", ""))}<br>
  {esc(prov.get("api_calls", 0))} API calls · collector {esc(prov["collector_version"])}</div>
</header>
{degraded}
<section class="readout" aria-label="Readout">
  <div><span class="eyebrow">In flight</span><strong>{summary["in_flight"]}</strong></div>
  <div><span class="eyebrow">Active areas</span><strong>{summary["areas_active"]}</strong></div>
  <div class="{"hot" if sig_counts["overlap"] else ""}"><span class="eyebrow">Overlaps</span><strong>{sig_counts["overlap"]}</strong></div>
  <div><span class="eyebrow">Open loops</span><strong>{sig_counts["stale"] + sig_counts["waiting"]}</strong></div>
  <div><span class="eyebrow">Commits on {esc(repo["default_branch"])}</span><strong>{summary["commits_in_window"]}</strong></div>
</section>

<div class="grid">
  <section>
    <h2 class="eyebrow">Topology</h2>
    <div class="radar-wrap">{radar_svg(snap)}
      <div class="legend"><span><i class="lg-live"></i>work in flight</span><span><i class="lg-idle"></i>recent commits only</span>
      <span><i class="lg-ov"></i>overlap (solid high · dashed medium · dotted low)</span><span>centre = now · distance = time since last activity (log scale) · labels on overlap and busy areas; hover for others</span></div>
    </div>
  </section>
  <section>
    <h2 class="eyebrow">Signals · every line opens to its evidence</h2>
    {"".join(groups)}
  </section>
</div>

<section class="band"><h2 class="eyebrow">Lanes and areas</h2><div class="lanes">{"".join(lane_cards)}</div></section>

<section class="band"><h2 class="eyebrow">Work in flight</h2><div class="table-wrap">{work_table}</div></section>

<section class="band two">
  <div><h2 class="eyebrow">Default-branch flow</h2><ul class="flow">{flow}</ul></div>
  <div><h2 class="eyebrow">Open issues</h2><ul class="flow">{issues}</ul></div>
</section>

<footer>
  <span>Observstory describes work, not people. There are no scores and no rankings. Signals are labelled derived, heuristic or declared.</span>
  <span><a href="data/snapshot.json">snapshot.json</a> · <a href="data/observations.json">observations.json</a> ·
  schema {esc(snap["schema"])}</span>
</footer>
</main>
<script type="application/json" id="observstory-snapshot">{raw}</script>
</body>
</html>"""
