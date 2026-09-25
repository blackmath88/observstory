#!/usr/bin/env python3
"""Build the Demo Lab (issue #6).

  python3 demo/build.py            -> demo/index.html + demo/states/<state>.{html,scene.json,snapshot.json}
  python3 demo/build.py --shots    -> also docs/demo/img/demo-lab-*.png (needs Playwright)

Every state is SYNTHETIC observation data (fixtures/demo_lab.py) run through the real
derive -> scene compiler -> Project Map renderer. Nothing on these pages is hand-drawn.
"""

from __future__ import annotations

import html
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "fixtures"))

import collab_lab  # noqa: E402
import demo_lab  # noqa: E402
from observstory import config  # noqa: E402
from observstory import coordination as co  # noqa: E402
from observstory.derive import derive, parse_time  # noqa: E402
from observstory.map_compiler import compile_scene  # noqa: E402
from observstory.map_render import render_map  # noqa: E402
from observstory.validate import scene_errors, validate  # noqa: E402

HERE = pathlib.Path(__file__).parent
STATES = [  # id, tab, act, caption, hint
    ("quiet", "Quiet", "story",
     "Monday morning at Northstar. Recent work has landed and nothing is in flight.",
     "This is what calm looks like: lanes, and what changed recently."),
    ("parallel", "Parallel", "story",
     "Alice, Ben and Sofia each open a pull request, in three different areas.",
     "Parallel work is normal, so nothing asks for attention."),
    ("overlap", "Overlap", "story",
     "Sofia starts chat history on a branch, with no pull request yet. Her change and Alice's both touch store.py.",
     "Click the orange connector to see the evidence."),
    ("crowded", "Crowded", "story",
     "Sofia opens her pull request, and Ben's agent-assisted refactor rewrites store.py too. Three changes, one file.",
     "Ben's export works in the same area but no shared file, so it gets no connector."),
    ("resolved", "Resolved", "story",
     "They talk. Sofia turns to evaluating Alice's work; Ben stacks his refactor on Alice's branch.",
     "The overlap is gone. Grey arrows now show what waits on what."),
    ("calm", "Calm again", "story",
     "Alice's memory work and Ben's refactor land. The evaluation carries on by itself.",
     "Quiet again, one day later."),
    ("burst", "Agent burst", "moments",
     "Sofia's coding agent generates the settings screens: 24 commits in under an hour, one pull request.",
     "≋ marks a machine-paced stream. It stays in the background."),
    ("stale", "Stale", "moments",
     "A week later, a search spike without a pull request and a parked draft have gone quiet.",
     "Open loops show up as work to revisit, with no judgement of anyone."),
    ("other-project", "Other project", "shape",
     "A different Northstar project with its own lanes: Data, Pipeline, Model, Eval, API, Docs.",
     "Same renderer; the lanes come from the project's configuration."),
    ("kickoff", "Kickoff", "declared",
     "A 36-hour hackathon. At kickoff the team agrees gates and who does what; Alice confirms the notes.",
     "The rail shows what people declared. Diamonds are commitments; none has linked work yet."),
    ("saturday-morning", "Sat 09:30", "declared",
     "Alice's audio pipeline has landed; Ben and Sofia are in flight. The morning check-in adds a commitment for #12.",
     "Commitment states come from the repository, not from anyone updating a status."),
    ("after-core-freeze", "Sat 15:00", "declared",
     "The core API freeze was at 12:00. The core API still changed afterwards, and the evaluation set has not started.",
     "Two cues under Declared vs observed. Click the orange gate on the rail for both sides."),
    ("feature-freeze", "Sat 23:00", "declared",
     "The feature freeze has passed while the recorder UI is still open. The evening notes are proposed, not confirmed.",
     "Unconfirmed notes never reach the rail; they wait for a named person."),
]
ACTS = {"story": "One week", "moments": "Moments", "shape": "Another project", "declared": "Declared vs observed"}
SHOTS = [("overlap", "demo-lab-overlap", 1440, 900, None), ("resolved", "demo-lab-resolved", 1440, 900, None),
         ("crowded", "demo-lab-narrow", 390, 844, None), ("after-core-freeze", "demo-lab-declared", 1440, 900, None)]


def build_states() -> list[dict]:
    fixtures, hack, declared = demo_lab.build(), collab_lab.moments(), collab_lab.declarations()
    out = HERE / "states"
    out.mkdir(exist_ok=True)
    manifest = []
    for sid, tab, act, caption, hint in STATES:
        if act == "declared":  # issue #7: declarations as they stood at that moment, reconciled by the real derive
            obs, cfg = hack[sid], collab_lab.CONFIG
            now = parse_time(obs["fetched_at"])
            snap = derive(obs, config.normalise(cfg), now, coordination=co.as_of(declared, now),
                          coordination_source=co.DEFAULT_PATH)
        else:
            obs = fixtures[sid]
            cfg = demo_lab.RECSYS_CONFIG if sid == "other-project" else demo_lab.CHAT_APP_CONFIG
            snap = derive(obs, config.normalise(cfg), parse_time(obs["fetched_at"]))
        scene = compile_scene(snap)
        errors = validate(snap) + scene_errors(scene)
        if errors:
            raise SystemExit(f"{sid}: {errors[:3]}")
        (out / f"{sid}.snapshot.json").write_text(json.dumps(snap, indent=1, ensure_ascii=False))
        (out / f"{sid}.scene.json").write_text(json.dumps(scene, indent=1, ensure_ascii=False))
        when = parse_time(scene["source"]["generated_at"])
        week = "" if act in ("shape", "declared") else f', week {1 + (when - demo_lab.T0).days // 7}'
        story_time = f'Story time: {when.strftime("%A %H:%M")}{week}'
        (out / f"{sid}.html").write_text(render_map(scene, radar_href=None, data_href=sid + ".{name}.json", time_label=story_time))
        s = scene["status"]
        manifest.append({"id": sid, "tab": tab, "act": act, "caption": caption, "hint": hint,
                         "repo": scene["source"]["repository"], "when": scene["source"]["generated_at"],
                         "status": f'{s["in_flight"]} in flight · {s["overlaps"]} overlap{"s" if s["overlaps"] != 1 else ""} · '
                                   f'{s["waiting"]} waiting · {s["stale"]} stale'})
    return manifest


def shell(manifest: list[dict]) -> str:
    tabs, act = [], None
    for i, st in enumerate(manifest):
        if st["act"] != act:
            act = st["act"]
            tabs.append(f'<span class="act">{html.escape(ACTS[act])}</span>')
        tabs.append(f'<button type="button" role="tab" id="tab-{st["id"]}" aria-controls="stage" data-i="{i}">'
                    f'{html.escape(st["tab"])}</button>')
    data = json.dumps(manifest, ensure_ascii=False).replace("<", "\\u003c")
    return SHELL.replace("{{TABS}}", "".join(tabs)).replace("{{DATA}}", data).replace("{{FIRST}}", manifest[0]["id"])


SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Observstory Demo Lab</title>
<meta name="description" content="One synthetic project at different moments, rendered by the real Observstory Project Map.">
<style>
:root{--bg:#f6f5f1;--surface:#fdfcfa;--ink:#1d1d1f;--ink2:#515154;--ink3:#8a8a8e;--hair:#e4e2dc;--hair2:#d6d4cd;
--accent:#b4530a;--select:#0a66d6;--sans:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",system-ui,sans-serif;
--mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root{--bg:#161617;--surface:#1e1e20;--ink:#f2f2f4;--ink2:#b8b8bd;--ink3:#85858b;
--hair:#2e2e31;--hair2:#3a3a3e;--accent:#f09a45;--select:#4c9bff}}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.45 var(--sans);display:flex;flex-direction:column;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:underline;text-decoration-color:var(--hair2);text-underline-offset:2px}
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer}
:focus-visible{outline:2px solid var(--select);outline-offset:2px;border-radius:6px}
.bar{background:var(--surface);border-bottom:1px solid var(--hair);padding:10px 20px 10px}
.row{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.brand{font-weight:600;font-size:13px;white-space:nowrap}
.brand span{color:var(--ink3);font-weight:500}
.synthetic{font-size:11px;color:var(--ink2);border:1px solid var(--hair2);border-radius:999px;padding:1px 8px;white-space:nowrap}
.tabs{display:flex;align-items:center;gap:2px;overflow-x:auto;scrollbar-width:none;flex:1;min-width:0;padding:2px}
.tabs::-webkit-scrollbar{display:none}
.act{font-size:10.5px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);margin:0 4px 0 10px;white-space:nowrap}
.act:first-child{margin-left:0}
[role=tab]{padding:4px 10px;border-radius:7px;color:var(--ink2);white-space:nowrap}
[role=tab]:hover{background:color-mix(in srgb,var(--ink) 5%,transparent)}
[role=tab][aria-selected=true]{background:var(--ink);color:var(--surface)}
.nav{display:flex;gap:6px;margin-left:auto}
.nav button{border:1px solid var(--hair2);border-radius:7px;padding:3px 10px;color:var(--ink2);background:var(--surface)}
.nav button:disabled{opacity:.35;cursor:default}
.story{display:flex;align-items:center;gap:6px 14px;margin-top:8px}
.words{margin:0;flex:1;min-width:0}
.step{font:11px var(--mono);color:var(--ink3);white-space:nowrap}
.caption{font-size:14px;color:var(--ink);margin-right:8px}
.hint{color:var(--ink3)}
iframe{flex:1;width:100%;border:0;background:var(--bg);min-height:480px}
.foot{padding:6px 20px;border-top:1px solid var(--hair);color:var(--ink3);font-size:11.5px;background:var(--surface)}
@media (max-width:760px){.bar{padding:10px 14px}.caption{font-size:13.5px}.tabs{flex-basis:100%}
  .story{flex-wrap:wrap}.words{flex-basis:100%;order:2}.step{order:1}.nav{order:1}.foot{display:none}}
</style>
</head>
<body>
<header class="bar">
  <div class="row">
    <span class="brand">Observstory <span>Demo Lab</span></span>
    <span class="synthetic" title="northstar/chat-app, northstar/recsys and northstar/voice-notes are invented; so are Alice, Ben, Sofia and Dana">Synthetic data</span>
    <nav class="tabs" role="tablist" aria-label="Project states">{{TABS}}</nav>
  </div>
  <div class="story">
    <span class="step" id="step"></span>
    <p class="words" aria-live="polite"><span class="caption" id="caption"></span> <span class="hint" id="hint"></span></p>
    <div class="nav"><button type="button" id="prev" aria-label="Previous state">← Prev</button>
      <button type="button" id="next" aria-label="Next state">Next →</button></div>
  </div>
</header>
<iframe id="stage" title="Project Map" src="states/{{FIRST}}.html"></iframe>
<p class="foot">Every state is synthetic observation data run through the real pipeline: derive → snapshot → scene compiler → Project Map.
  Each map links to its own <code>scene.json</code> and <code>snapshot.json</code>. ← → to step through.</p>
<script type="application/json" id="states">{{DATA}}</script>
<script>
(function(){
const S = JSON.parse(document.getElementById('states').textContent);
const tabs = [...document.querySelectorAll('[role=tab]')], stage = document.getElementById('stage');
let cur = -1;
function show(i, push){
  i = Math.max(0, Math.min(S.length - 1, i)); if (i === cur) return; cur = i; const st = S[i];
  tabs.forEach((t, k) => { t.setAttribute('aria-selected', k === i); t.tabIndex = k === i ? 0 : -1; });
  tabs[i].scrollIntoView({block: 'nearest', inline: 'nearest'});
  stage.src = 'states/' + st.id + '.html';
  document.getElementById('step').textContent = (i + 1) + ' / ' + S.length;
  document.getElementById('caption').textContent = st.caption;
  document.getElementById('hint').textContent = st.hint;
  document.getElementById('prev').disabled = i === 0; document.getElementById('next').disabled = i === S.length - 1;
  document.title = 'Observstory Demo Lab · ' + st.tab;
  if (push !== false) history.replaceState(null, '', '#' + st.id);
}
tabs.forEach(t => t.addEventListener('click', () => show(+t.dataset.i)));
document.getElementById('prev').addEventListener('click', () => show(cur - 1));
document.getElementById('next').addEventListener('click', () => show(cur + 1));
document.addEventListener('keydown', e => {
  if (e.altKey || e.ctrlKey || e.metaKey) return;
  if (e.key === 'ArrowRight') { e.preventDefault(); show(cur + 1); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); show(cur - 1); }
});
function fromHash(){ const k = S.findIndex(s => '#' + s.id === location.hash); show(k < 0 ? 0 : k, false); }
window.addEventListener('hashchange', fromHash);
fromHash();
})();
</script>
</body>
</html>
"""


def main():
    manifest = build_states()
    (HERE / "index.html").write_text(shell(manifest), encoding="utf-8")
    for st in manifest:
        print(f'{st["id"]:<14} {st["status"]}')
    if "--shots" in sys.argv:
        shot = ROOT / "prototypes/project-map/shot.js"
        for sid, png, w, h, click in SHOTS:
            subprocess.run(["node", str(shot), str(HERE / "index.html") + "#" + sid, str(ROOT / "docs/demo/img" / f"{png}.png"),
                            str(w), str(h)] + ([click] if click else []), check=True)


if __name__ == "__main__":
    main()
