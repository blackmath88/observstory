"""Build the Semantic UI Playground: demo/playground.html + demo/playground/<state>.{html,scene.json,snapshot.json}.

Every state is a semantic spec (fixtures/playground.py) turned into synthetic observations and run
through the real derive -> compile_scene -> render_map. The browser only switches between these
generated pages; it holds no Observstory semantics of its own.
"""

from __future__ import annotations

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "fixtures"))

import playground as pg  # noqa: E402
from observstory import config  # noqa: E402
from observstory.derive import derive  # noqa: E402
from observstory.map_compiler import compile_scene, explain_frame  # noqa: E402
from observstory.map_render import render_map  # noqa: E402
from observstory.validate import scene_errors, validate  # noqa: E402

HERE = pathlib.Path(__file__).parent
OUT = HERE / "playground"
DEFAULT = "software.parallel.low.none"
SHOTS = [("software.overlap.high.none", "playground-software-overlap", 1440, 900),
         ("ml.parallel.high.none", "playground-ml-parallel", 1440, 900),
         ("hackathon.overlap.low.conflict", "playground-hackathon-conflict", 1440, 900),
         ("hackathon.parallel.high.freeze", "playground-narrow", 390, 844)]


def excerpt(scene: dict) -> dict:
    """The few scene facts the shell shows next to the map (read from the generated scene, not recomputed)."""
    c = scene.get("coordination")
    return {
        "lanes": [z["label"] for z in sorted(scene["zones"], key=lambda z: z["order"])],
        "status": scene["status"],
        "edges": [{"type": e["type"], "from": e["from"], "to": e["to"], "files": e["files"]} for e in scene["edges"]],
        "attention": [a["label"] for a in scene["attention"]],
        "rail": None if not c else {"next_gate": c["next_gate"], "gates": [g["label"] for g in c["gates"]],
                                    "commitments": len(c["commitments"]), "cues": [q["rule"] for q in c["cues"]]},
    }


def build_states() -> list[dict]:
    OUT.mkdir(exist_ok=True)
    manifest = []
    for spec in pg.matrix():
        sid = pg.state_id(spec)
        snap = derive(pg.observations(spec), config.normalise(pg.config(spec)), pg.NOW,
                      coordination=pg.declarations(spec), coordination_source=".observstory/coordination.json")
        scene = compile_scene(snap)
        errors = validate(snap) + scene_errors(scene)
        if errors:
            raise SystemExit(f"{sid}: {errors[:3]}")
        (OUT / f"{sid}.snapshot.json").write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n")
        (OUT / f"{sid}.scene.json").write_text(json.dumps(scene, indent=1, ensure_ascii=False) + "\n")
        (OUT / f"{sid}.html").write_text(render_map(scene, radar_href=None, data_href=sid + ".{name}.json",
                                                    time_label="Playground · synthetic, Wednesday 15:00"))
        manifest.append({"id": sid, "spec": spec, "why": explain_frame(scene), "scene": excerpt(scene)})
    return manifest


def seg(name: str, options: dict, legend: str) -> str:
    items = "".join(f'<label><input type="radio" name="{name}" value="{html.escape(k)}"><span>{html.escape(v)}</span></label>'
                    for k, v in options.items())
    return f'<fieldset class="seg" data-axis="{name}"><legend>{html.escape(legend)}</legend><div>{items}</div></fieldset>'


def rows(name: str, options: dict, legend: str, note: str) -> str:
    items = "".join(f'<label><input type="radio" name="{name}" value="{html.escape(k)}"><span>{html.escape(v)}</span></label>'
                    for k, v in options.items())
    return (f'<fieldset class="rows" data-axis="{name}"><legend>{html.escape(legend)}</legend>{items}'
            f'<p class="note" id="note-{name}">{html.escape(note)}</p></fieldset>')


def shell(manifest: list[dict]) -> str:
    controls = (seg("shape", {k: v["label"] for k, v in pg.SHAPES.items()}, "Project shape")
                + seg("volume", {k: f"{n} in flight" for k, n in pg.VOLUMES.items()}, "Work")
                + rows("relation", pg.RELATIONS, "Relation between work", "")
                + rows("collab", pg.COLLAB, "Declared collaboration", ""))
    data = json.dumps(manifest, ensure_ascii=False).replace("<", "\\u003c")
    return SHELL.replace("{{CONTROLS}}", controls).replace("{{DATA}}", data).replace("{{DEFAULT}}", DEFAULT)


SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Observstory Semantic UI Playground</title>
<meta name="description" content="Change the semantic state of a synthetic project; the real Observstory pipeline compiles the Project Map.">
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
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer;padding:0}
:focus-visible{outline:2px solid var(--select);outline-offset:2px;border-radius:6px}
.bar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:var(--surface);border-bottom:1px solid var(--hair);padding:9px 20px}
.brand{font-weight:600;white-space:nowrap}.brand span{color:var(--ink3);font-weight:500}
.claim{color:var(--ink2);flex:1;min-width:220px}
.synthetic{font-size:11px;color:var(--ink2);border:1px solid var(--hair2);border-radius:999px;padding:1px 8px;white-space:nowrap}
.bar nav{display:flex;gap:12px;font-size:12px;color:var(--ink2)}
.work{flex:1;display:flex;min-height:0}
.panel{width:272px;flex:none;background:var(--surface);border-right:1px solid var(--hair);padding:14px 16px 18px;overflow-y:auto}
.panel h2{margin:0 0 10px;font-size:10.5px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--ink3)}
fieldset{border:0;margin:0 0 14px;padding:0;min-width:0}
legend{padding:0;margin-bottom:5px;font-size:11.5px;font-weight:600;color:var(--ink2)}
input[type=radio]{position:absolute;opacity:0;pointer-events:none}
.seg div{display:flex;border:1px solid var(--hair2);border-radius:7px;overflow:hidden}
.seg label{flex:1;text-align:center;cursor:pointer}
.seg label+label{border-left:1px solid var(--hair2)}
.seg span{display:block;padding:4px 6px;color:var(--ink2);font-size:12px}
.seg input:checked+span{background:var(--ink);color:var(--surface)}
.rows label{display:flex;align-items:center;gap:8px;padding:3px 4px;border-radius:6px;cursor:pointer;color:var(--ink2)}
.rows label:hover{background:color-mix(in srgb,var(--ink) 5%,transparent)}
.rows span::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;border:1.5px solid var(--ink3);margin-right:8px;vertical-align:-1px}
.rows input:checked+span{color:var(--ink)}
.rows input:checked+span::before{border-color:var(--ink);background:radial-gradient(var(--ink) 38%,transparent 42%)}
label.off{opacity:.38;cursor:not-allowed}
input:focus-visible+span{outline:2px solid var(--select);outline-offset:1px;border-radius:5px}
.note{margin:3px 4px 0;color:var(--ink3);font-size:11px;min-height:0}
.note:empty{display:none}
.why{border-top:1px solid var(--hair);padding-top:12px;margin-top:4px}
.why ul{margin:0;padding:0 0 0 14px;color:var(--ink2);font-size:12px}
.why li{margin-bottom:4px}
.why li.changed{color:var(--ink)}
.delta{margin:8px 0 0;font:11px var(--mono);color:var(--ink3)}
.delta b{color:var(--accent);font-weight:600}
.pipe{border-top:1px solid var(--hair);padding-top:12px;margin-top:14px}
.flow{display:flex;flex-wrap:wrap;align-items:center;gap:3px 4px;font:11px var(--mono);color:var(--ink2);margin-bottom:6px}
.flow i{font-style:normal;color:var(--ink3)}
.files{font-size:12px;color:var(--ink2)}
.files code{font:11px var(--mono)}
details{margin-top:8px}
summary{cursor:pointer;color:var(--ink2);font-size:12px}
pre{margin:6px 0 0;padding:8px;background:var(--bg);border:1px solid var(--hair);border-radius:7px;font:10.5px/1.45 var(--mono);color:var(--ink2);white-space:pre-wrap;word-break:break-word;max-height:260px;overflow:auto}
.stage{flex:1;display:flex;flex-direction:column;min-width:0}
iframe{flex:1;width:100%;border:0;background:var(--bg)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
@media (max-width:760px){.bar{padding:9px 14px}.work{flex-direction:column}
  .panel{width:auto;border-right:0;border-bottom:1px solid var(--hair);padding:12px 14px}
  .ctl{display:grid;grid-template-columns:1fr 1fr;gap:0 14px}.ctl fieldset.seg{grid-column:1/-1}
  iframe{min-height:1100px}}
</style>
</head>
<body>
<header class="bar">
  <span class="brand">Observstory <span>Semantic UI Playground</span></span>
  <span class="synthetic" title="The repositories and people are invented">Synthetic data</span>
  <span class="claim">Change what the project <em>means</em>. The pipeline compiles the map; nothing is positioned by hand.</span>
  <nav><a href="index.html">Demo Lab (the story) →</a><a href="../docs/ui/semantic-ui-playground.md">How it works</a></nav>
</header>
<div class="work">
  <aside class="panel" aria-label="Semantic state">
    <h2>Semantic state</h2>
    <form class="ctl" id="ctl">{{CONTROLS}}</form>
    <section class="why" aria-live="polite">
      <h2>Why this frame?</h2>
      <ul id="why"></ul>
      <p class="delta" id="delta"></p>
    </section>
    <section class="pipe">
      <h2>Compiled by</h2>
      <div class="flow"><span>semantic state</span><i>→</i><span>observations</span><i>→</i><span>derive</span><i>→</i>
        <a id="snap" target="_blank">snapshot</a><i>→</i><a id="scene" target="_blank">scene</a><i>→</i><span>Project Map</span></div>
      <p class="files">State <code id="sid"></code>. Open the generated <a id="snap2" target="_blank">snapshot.json</a> and
        <a id="scene2" target="_blank">scene.json</a>; the map itself is <a id="page" target="_blank">a plain generated page</a>.</p>
      <details><summary>Scene excerpt</summary><pre id="excerpt"></pre></details>
    </section>
  </aside>
  <main class="stage"><iframe id="stage" title="Project Map compiled from the selected semantic state"></iframe></main>
</div>
<script type="application/json" id="states">{{DATA}}</script>
<script>
(function(){
const S = JSON.parse(document.getElementById('states').textContent);
const byId = Object.fromEntries(S.map(s => [s.id, s]));
const AXES = ['shape', 'relation', 'volume', 'collab'];
const form = document.getElementById('ctl'), stage = document.getElementById('stage');
const $ = id => document.getElementById(id);
let cur = null;
const key = sp => [sp.shape, sp.relation, sp.volume, sp.collab].join('.');
function read(){ const sp = {}; AXES.forEach(a => { const el = form.querySelector('input[name=' + a + ']:checked'); sp[a] = el && el.value; }); return sp; }
function write(sp){ AXES.forEach(a => { const el = form.querySelector('input[name=' + a + '][value="' + sp[a] + '"]'); if (el) el.checked = true; }); }
function resolve(sp, changed){
  // Keep the axis the user just changed; reset others to their calm default until a prebuilt state exists.
  if (byId[key(sp)]) return sp;
  for (const [a, v] of [['collab', 'none'], ['relation', 'parallel']]) {
    if (a === changed) continue; sp = Object.assign({}, sp, {[a]: v}); if (byId[key(sp)]) return sp;
  }
  return byId[key(sp)] ? sp : S[0].spec;
}
function availability(sp){
  // An option is off only when no prebuilt state has it for this project shape; otherwise choosing it
  // may reset another axis (resolve), and the note says which.
  AXES.forEach(a => form.querySelectorAll('input[name=' + a + ']').forEach(el => {
    const ok = a === 'shape' || S.some(s => s.spec.shape === sp.shape && s.spec[a] === el.value);
    el.disabled = !ok; el.parentElement.classList.toggle('off', !ok);
    el.parentElement.title = ok ? '' : 'Declared collaboration is prebuilt for the hackathon project';
  }));
  $('note-collab').textContent = sp.shape === 'hackathon' ? '' : 'Prebuilt for the hackathon project only.';
}
function deltaText(a, b){
  if (!a) return '';
  const out = [], sa = a.scene, sb = b.scene;
  for (const k of ['in_flight', 'areas_active', 'overlaps', 'waiting', 'stale'])
    if (sa.status[k] !== sb.status[k]) out.push(k.replace('_', ' ') + ' ' + sa.status[k] + '→<b>' + sb.status[k] + '</b>');
  if (sa.lanes.join() !== sb.lanes.join()) out.push('lanes <b>recomposed</b> (' + sb.lanes.join(' → ') + ')');
  if (!!sa.rail !== !!sb.rail) out.push('mission rail ' + (sb.rail ? 'off→<b>on</b>' : 'on→<b>off</b>'));
  if (sa.attention.length !== sb.attention.length) out.push('attention ' + sa.attention.length + '→<b>' + sb.attention.length + '</b>');
  return out.length ? 'Recompiled: ' + out.join(' · ') : 'Recompiled: same frame';
}
const LABEL = {relation: 'Relation', collab: 'Declared collaboration'};
function show(sp, changed, push){
  const asked = sp; sp = resolve(sp, changed); write(sp); availability(sp);
  const reset = ['relation', 'collab'].filter(a => a !== changed && asked[a] !== sp[a]);
  $('note-relation').textContent = reset.length ? LABEL[reset[0]] + ' reset: declared states are prebuilt with parallel or overlapping work.' : '';
  const st = byId[key(sp)], prev = cur; if (prev && prev.id === st.id) return; cur = st;
  stage.src = 'playground/' + st.id + '.html';
  const before = new Set(prev ? prev.why : []);
  $('why').replaceChildren(...st.why.map(t => { const li = document.createElement('li'); li.textContent = t; if (prev && !before.has(t)) li.className = 'changed'; return li; }));
  $('delta').innerHTML = deltaText(prev, st);
  $('sid').textContent = st.id;
  for (const [a, f] of [['snap', 'snapshot'], ['snap2', 'snapshot'], ['scene', 'scene'], ['scene2', 'scene']]) $(a).href = 'playground/' + st.id + '.' + f + '.json';
  $('page').href = 'playground/' + st.id + '.html';
  $('excerpt').textContent = JSON.stringify(st.scene, null, 1);
  document.title = 'Observstory Semantic UI Playground · ' + st.id;
  if (push !== false) history.replaceState(null, '', '#' + st.id);
}
form.addEventListener('change', e => show(read(), e.target.name));
function fromHash(){ const st = byId[location.hash.slice(1)] || byId['{{DEFAULT}}']; cur = null; show(Object.assign({}, st.spec), null, false); }
window.addEventListener('hashchange', () => { if (!cur || location.hash.slice(1) !== cur.id) fromHash(); });
fromHash();
})();
</script>
</body>
</html>
"""


def main() -> list[dict]:
    manifest = build_states()
    (HERE / "playground.html").write_text(shell(manifest), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    for st in main():
        print(st["id"])
