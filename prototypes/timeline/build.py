#!/usr/bin/env python3
"""Direction 2 prototype: Project Timeline / Playback.

Derives a snapshot for each moment of the demo scenario and renders how areas and signals
change over time. Also writes timeline.json (the diff between consecutive snapshots),
which is what a persisted history would give a hosted service.

  python3 prototypes/timeline/build.py
"""

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from observstory import config  # noqa: E402
from observstory.derive import derive, parse_time  # noqa: E402

HERE = pathlib.Path(__file__).parent
MOMENTS = ["demo-t0", "demo-t1", "demo-t2", "demo-t3"]


def load(name):
    obs = json.loads((ROOT / "fixtures/observations" / f"{name}.json").read_text())
    return obs["note"], derive(obs, config.normalise(None), parse_time(obs["fetched_at"]))


def diff(prev, cur):
    events = []
    p_items = {w["id"]: w for w in prev["work_items"]} if prev else {}
    c_items = {w["id"]: w for w in cur["work_items"]}
    promoted = {}  # branch:x -> pr:N when a PR is opened from a previously unproposed branch
    for wid, w in c_items.items():
        if w["kind"] == "pull_request" and f"branch:{w['head']}" in p_items and f"branch:{w['head']}" not in c_items:
            promoted[f"branch:{w['head']}"] = wid
    for old, new in promoted.items():
        events.append({"kind": "work_promoted", "ref": new, "text": f"{old} opened as {new}"})
    for wid, w in c_items.items():
        if wid in promoted.values():
            continue
        if wid not in p_items and (w["in_flight"] or w["kind"] == "direct"):
            events.append({"kind": "work_started", "ref": wid, "text": f"{wid} appears ({w['state']}): {w['title']}"})
        elif wid in p_items and p_items[wid]["state"] != w["state"]:
            events.append({"kind": "work_state", "ref": wid, "text": f"{wid}: {p_items[wid]['state']} → {w['state']}"})
    for wid, w in p_items.items():
        if wid not in c_items and w["in_flight"] and wid not in promoted:
            events.append({"kind": "work_gone", "ref": wid, "text": f"{wid} no longer in flight"})
    p_sig = {s["id"]: s for s in prev["signals"]} if prev else {}
    c_sig = {s["id"]: s for s in cur["signals"]}
    for sid in c_sig.keys() - p_sig.keys():
        events.append({"kind": "signal_appeared", "ref": sid, "text": f"{c_sig[sid]['type']} appeared: {c_sig[sid]['summary']}"})
    for sid in p_sig.keys() - c_sig.keys():
        events.append({"kind": "signal_resolved", "ref": sid, "text": f"{p_sig[sid]['type']} resolved: {p_sig[sid]['summary']}"})
    return events


def main():
    frames, prev = [], None
    for name in MOMENTS:
        note, snap = load(name)
        frames.append({"moment": name, "at": snap["generated_at"], "note": note,
                       "areas": {a["id"]: len(a["in_flight"]) for a in snap["areas"]},
                       "overlaps": sorted(s["subject"]["id"] for s in snap["signals"] if s["type"] == "overlap"),
                       "events": diff(prev, snap)})
        prev = snap
    (HERE / "timeline.json").write_text(json.dumps(frames, indent=2) + "\n")

    areas = sorted({a for f in frames for a in f["areas"]})
    head = "".join(f'<th><span class="t">{html.escape(f["at"][5:16].replace("T", " "))}</span>'
                   f'<span class="n">{html.escape(f["note"])}</span></th>' for f in frames)
    rows = []
    for a in areas:
        cells = []
        for f in frames:
            n = f["areas"].get(a, 0)
            hot = a in f["overlaps"]
            dots = "".join('<i class="d"></i>' for _ in range(n)) or '<i class="e"></i>'
            cells.append(f'<td class="{"hot" if hot else ""}">{dots}{" <b>overlap</b>" if hot else ""}</td>')
        rows.append(f"<tr><th class='a'><code>{html.escape(a)}</code></th>{''.join(cells)}</tr>")
    logs = "".join(f'<li><span class="t">{html.escape(f["at"][5:16].replace("T", " "))}</span><ul>'
                   + "".join(f'<li class="{e["kind"]}">{html.escape(e["text"])}</li>' for e in f["events"])
                   + "</ul></li>" for f in frames)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Observstory timeline</title>
<style>
:root{{--bg:#f3f2ee;--ink:#1c1d1f;--muted:#66686b;--line:#dddbd3;--mark:#2f5467;--accent:#b4530a;--soft:#f6e7d8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0e1113;--ink:#e5e3dd;--muted:#8d9295;--line:#252c30;--mark:#8db5c9;--accent:#f09a45;--soft:#3a2716}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 ui-sans-serif,-apple-system,sans-serif}}
main{{max-width:1100px;margin:auto;padding:28px 16px}}
.eyebrow{{font:600 11px ui-monospace,Menlo,monospace;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}}
h1{{font-weight:600;letter-spacing:-.02em;margin:6px 0 20px}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%}}
th,td{{border-bottom:1px solid var(--line);padding:10px;text-align:left;vertical-align:top}}
thead th{{font-weight:400}} .t{{display:block;font:12px ui-monospace,Menlo,monospace;color:var(--muted)}}
.n{{display:block;font-size:12px;max-width:220px}} code{{font:12px ui-monospace,Menlo,monospace}}
.d{{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--mark);margin-right:4px}}
.e{{display:inline-block;width:10px;height:1px;background:var(--line);vertical-align:middle}}
td.hot{{background:var(--soft)}} td.hot b{{color:var(--accent);font:600 11px ui-monospace,Menlo,monospace}}
ol{{list-style:none;padding:0}} ol>li{{margin:14px 0}} ol ul{{margin:4px 0 0;padding-left:18px;color:var(--muted)}}
.signal_appeared{{color:var(--accent)}} .signal_resolved{{color:var(--ink)}}
</style></head><body><main>
<span class="eyebrow">Observstory · direction 2 · timeline / playback (prototype)</span>
<h1>How the project's in-flight state changed</h1>
<p class="t">Rows are areas. Each dot is one work item in flight. The shaded cell is an overlap signal. Built from fixtures/observations/demo-t0…t3.</p>
<div class="wrap"><table><thead><tr><th></th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2 class="eyebrow" style="margin-top:32px">State transitions</h2><ol>{logs}</ol>
</main></body></html>"""
    (HERE / "index.html").write_text(page)
    print("wrote prototypes/timeline/index.html and timeline.json")


if __name__ == "__main__":
    main()
