"""System Map v0: semantic architecture model -> durable Mermaid + interactive HTML.

The canonical input contains meaning, not coordinates.  Renderers own placement.
System Maps are declared/project knowledge and remain distinct from the observed
repository truth in observstory.snapshot/v1.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

SCHEMA = "observstory.system-map/v0"
STATUSES = {"observed", "established", "candidate", "questioned", "deprecated"}
BASES = {"human-declared", "repository-evidence", "research", "experiment", "inference"}


def validate_system_map(model: dict) -> list[str]:
    errors: list[str] = []
    if model.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    if not isinstance(model.get("title"), str) or not model["title"].strip():
        errors.append("title must be a non-empty string")

    nodes = model.get("nodes")
    edges = model.get("edges")
    if not isinstance(nodes, list):
        return errors + ["nodes must be an array"]
    if not isinstance(edges, list):
        return errors + ["edges must be an array"]

    ids: set[str] = set()
    for i, node in enumerate(nodes):
        prefix = f"nodes[{i}]"
        if not isinstance(node, dict):
            errors.append(f"{prefix} must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif node_id in ids:
            errors.append(f"duplicate node id: {node_id}")
        else:
            ids.add(node_id)
        for key in ("kind", "label"):
            if not isinstance(node.get(key), str) or not node[key]:
                errors.append(f"{prefix}.{key} must be a non-empty string")
        if node.get("status") is not None and node["status"] not in STATUSES:
            errors.append(f"{prefix}.status is invalid")
        if node.get("basis") is not None and node["basis"] not in BASES:
            errors.append(f"{prefix}.basis is invalid")

    for i, edge in enumerate(edges):
        prefix = f"edges[{i}]"
        if not isinstance(edge, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in ("from", "to", "kind"):
            if not isinstance(edge.get(key), str) or not edge[key]:
                errors.append(f"{prefix}.{key} must be a non-empty string")
        if edge.get("from") not in ids:
            errors.append(f"{prefix}.from references missing node {edge.get('from')!r}")
        if edge.get("to") not in ids:
            errors.append(f"{prefix}.to references missing node {edge.get('to')!r}")
        if edge.get("status") is not None and edge["status"] not in STATUSES:
            errors.append(f"{prefix}.status is invalid")
        if edge.get("basis") is not None and edge["basis"] not in BASES:
            errors.append(f"{prefix}.basis is invalid")

    group_ids = {g.get("id") for g in model.get("groups", []) if isinstance(g, dict)}
    for node in nodes:
        if isinstance(node, dict) and node.get("group") and node["group"] not in group_ids:
            errors.append(f"node {node.get('id')} references missing group {node['group']}")

    return errors


def _mermaid_id(value: str) -> str:
    return "n_" + "".join(c if c.isalnum() else "_" for c in value)


def render_mermaid(model: dict, view: str | None = None) -> str:
    errors = validate_system_map(model)
    if errors:
        raise ValueError("; ".join(errors))

    include: set[str] | None = None
    if view:
        spec = next((v for v in model.get("views", []) if v.get("id") == view), None)
        if spec is None:
            raise ValueError(f"unknown view: {view}")
        include = set(spec.get("include", []))

    nodes = [n for n in model["nodes"] if include is None or n["id"] in include]
    ids = {n["id"] for n in nodes}
    edges = [e for e in model["edges"] if e["from"] in ids and e["to"] in ids]
    groups = {g["id"]: g for g in model.get("groups", [])}

    lines = ["flowchart LR"]
    grouped: dict[str | None, list[dict]] = {}
    for node in nodes:
        grouped.setdefault(node.get("group"), []).append(node)

    for group_id, members in grouped.items():
        if group_id and group_id in groups:
            lines.append(f'  subgraph g_{_mermaid_id(group_id)}["{groups[group_id]["label"]}"]')
            indent = "    "
        else:
            indent = "  "
        for node in members:
            label = node["label"].replace('"', "'")
            status = node.get("status", "candidate")
            lines.append(f'{indent}{_mermaid_id(node["id"])}["{label}<br/><small>{status}</small>"]')
        if group_id and group_id in groups:
            lines.append("  end")

    for edge in edges:
        label = (edge.get("label") or edge["kind"]).replace('"', "'")
        lines.append(f'  {_mermaid_id(edge["from"])} -->|{label}| {_mermaid_id(edge["to"])}')
    return "\n".join(lines) + "\n"


def render_html(model: dict) -> str:
    errors = validate_system_map(model)
    if errors:
        raise ValueError("; ".join(errors))

    payload = json.dumps(model, ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(model["title"])
    purpose = html.escape(model.get("purpose", ""))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · System Map</title>
<style>
:root{{--bg:#f5f3ee;--paper:#fffefa;--ink:#171714;--muted:#77756d;--line:#d8d4ca;--accent:#8b3f2f;--soft:#ece8df;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
header{{padding:28px 34px 18px;border-bottom:1px solid var(--line);background:var(--paper)}} h1{{margin:0;font-size:24px;font-weight:650;letter-spacing:-.03em}}
header p{{margin:6px 0 0;color:var(--muted);max-width:850px}}
.toolbar{{display:flex;gap:8px;flex-wrap:wrap;padding:12px 34px;border-bottom:1px solid var(--line);background:var(--paper);position:sticky;top:0;z-index:5}}
button,select{{font:inherit;border:1px solid var(--line);background:var(--paper);padding:7px 10px;border-radius:5px;color:var(--ink)}} button.active{{background:var(--ink);color:var(--paper);border-color:var(--ink)}}
main{{display:grid;grid-template-columns:minmax(0,1fr) 300px;min-height:calc(100vh - 126px)}} #map{{padding:30px;overflow:auto;position:relative}}
#groups{{display:flex;gap:28px;align-items:flex-start;min-width:max-content}} .group{{min-width:245px;max-width:285px}}
.group h2{{font-size:12px;text-transform:uppercase;letter-spacing:.11em;color:var(--muted);font-weight:650;margin:0 0 10px;padding-bottom:7px;border-bottom:1px solid var(--line)}}
.node{{position:relative;background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:12px 13px;margin:9px 0;cursor:pointer;box-shadow:0 1px 0 rgba(0,0,0,.02)}}
.node:hover,.node.selected{{border-color:var(--ink)}} .node .kind{{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}} .node strong{{display:block;margin:3px 0 7px;font-size:15px}}
.pill{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 6px;font-size:10px;margin-right:4px;color:var(--muted)}} .questioned{{border-style:dashed}} .deprecated{{opacity:.48}} .established{{border-left:4px solid var(--ink)}} .observed{{border-left:4px solid #77756d}} .candidate{{border-left:4px solid var(--accent)}}
aside{{border-left:1px solid var(--line);background:var(--paper);padding:24px;position:sticky;top:50px;height:calc(100vh - 50px);overflow:auto}} aside h3{{margin:0 0 12px;font-size:14px}} aside .empty{{color:var(--muted)}} dl{{margin:0}} dt{{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-top:15px}} dd{{margin:3px 0 0}}
.edge-list{{margin:8px 0 0;padding:0;list-style:none}} .edge-list li{{border-top:1px solid var(--line);padding:8px 0;font-size:12px}}
.evidence a{{color:inherit}} .editor{{margin-top:18px;padding-top:15px;border-top:1px solid var(--line)}} .editor label{{display:block;font-size:11px;color:var(--muted);margin:8px 0 3px}} .editor input,.editor textarea,.editor select{{width:100%;font:inherit;border:1px solid var(--line);border-radius:4px;padding:6px;background:white}} .editor textarea{{min-height:70px;resize:vertical}}
#export{{margin-left:auto}} .hidden{{display:none!important}} .ungrouped h2{{visibility:hidden}}
@media(max-width:800px){{main{{grid-template-columns:1fr}} aside{{position:static;height:auto;border-left:0;border-top:1px solid var(--line)}} #groups{{display:block;min-width:0}} .group{{max-width:none}}}}
</style>
</head>
<body>
<header><h1>{title}</h1><p>{purpose}</p></header>
<div class="toolbar">
  <select id="view"><option value="">All views</option></select>
  <button data-filter="all" class="active">All</button>
  <button data-filter="established">Established</button>
  <button data-filter="candidate">Candidate</button>
  <button data-filter="questioned">Questioned</button>
  <button id="edit">Edit semantics</button>
  <button id="export">Export JSON</button>
</div>
<main>
  <section id="map"><div id="groups"></div></section>
  <aside id="inspector"><div class="empty">Select a component to inspect its meaning, basis, evidence and relationships.</div></aside>
</main>
<script type="application/json" id="model">{payload}</script>
<script>
const model=JSON.parse(document.getElementById('model').textContent);
let selected=null, filter='all', activeView='', editing=false;
const byId=()=>Object.fromEntries(model.nodes.map(n=>[n.id,n]));
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
function visible(n){{if(filter!=='all'&&(n.status||'candidate')!==filter)return false;if(!activeView)return true;const v=(model.views||[]).find(x=>x.id===activeView);return !v||!v.include?.length||v.include.includes(n.id)}}
function render(){{
  const groups=[...(model.groups||[])].sort((a,b)=>(a.order??99)-(b.order??99)||a.label.localeCompare(b.label));
  const known=new Set(groups.map(g=>g.id)); if(model.nodes.some(n=>!n.group||!known.has(n.group)))groups.push({{id:'__other',label:'Other',order:999}});
  document.getElementById('groups').innerHTML=groups.map(g=>{{
    const nodes=model.nodes.filter(n=>(n.group||'__other')===g.id&&visible(n));
    if(!nodes.length)return '';
    return '<section class="group '+(g.id==='__other'?'ungrouped':'')+'"><h2>'+esc(g.label)+'</h2>'+nodes.map(n=>'<article class="node '+esc(n.status||'candidate')+(n.id===selected?' selected':'')+'" data-id="'+esc(n.id)+'"><span class="kind">'+esc(n.kind)+'</span><strong>'+esc(n.label)+'</strong><span class="pill">'+esc(n.status||'candidate')+'</span><span class="pill">'+esc(n.basis||'human-declared')+'</span></article>').join('')+'</section>';
  }}).join('');
  document.querySelectorAll('.node').forEach(el=>el.onclick=()=>{{selected=el.dataset.id;render();inspect();}});
}}
function inspect(){{
 const el=document.getElementById('inspector'), n=byId()[selected]; if(!n){{el.innerHTML='<div class="empty">Select a component to inspect its meaning, basis, evidence and relationships.</div>';return}}
 const edges=model.edges.filter(e=>e.from===n.id||e.to===n.id);
 const evidence=(n.evidence||[]).map(e=>'<li><a href="'+esc(e.ref)+'">'+esc(e.label||e.ref)+'</a> <span class="pill">'+esc(e.kind||'evidence')+'</span></li>').join('');
 const edit=editing?'<div class="editor"><label>Label</label><input id="e-label" value="'+esc(n.label)+'"><label>Description</label><textarea id="e-desc">'+esc(n.description||'')+'</textarea><label>Status</label><select id="e-status">'+['observed','established','candidate','questioned','deprecated'].map(x=>'<option '+(x===(n.status||'candidate')?'selected':'')+'>'+x+'</option>').join('')+'</select><label>Basis</label><select id="e-basis">'+['human-declared','repository-evidence','research','experiment','inference'].map(x=>'<option '+(x===(n.basis||'human-declared')?'selected':'')+'>'+x+'</option>').join('')+'</select><button id="apply" style="margin-top:10px">Apply semantic edit</button></div>':'';
 el.innerHTML='<h3>'+esc(n.label)+'</h3><dl><dt>Kind</dt><dd>'+esc(n.kind)+'</dd><dt>Status</dt><dd>'+esc(n.status||'candidate')+'</dd><dt>Basis</dt><dd>'+esc(n.basis||'human-declared')+'</dd><dt>Description</dt><dd>'+esc(n.description||'—')+'</dd></dl><dt>Relationships</dt><ul class="edge-list">'+edges.map(e=>'<li>'+esc(e.from===n.id?'→ ':'← ')+esc(e.kind)+' · '+esc(e.from===n.id?(byId()[e.to]?.label||e.to):(byId()[e.from]?.label||e.from))+'</li>').join('')+'</ul><dt>Evidence</dt><ul class="edge-list evidence">'+(evidence||'<li>None linked</li>')+'</ul>'+edit;
 if(editing)document.getElementById('apply').onclick=()=>{{n.label=document.getElementById('e-label').value;n.description=document.getElementById('e-desc').value;n.status=document.getElementById('e-status').value;n.basis=document.getElementById('e-basis').value;render();inspect();}};
}}
(model.views||[]).forEach(v=>document.getElementById('view').insertAdjacentHTML('beforeend','<option value="'+esc(v.id)+'">'+esc(v.label)+'</option>'));
document.getElementById('view').onchange=e=>{{activeView=e.target.value;render()}};
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{{filter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));render()}});
document.getElementById('edit').onclick=e=>{{editing=!editing;e.target.classList.toggle('active',editing);e.target.textContent=editing?'Editing semantics':'Edit semantics';inspect()}};
document.getElementById('export').onclick=()=>{{const blob=new Blob([JSON.stringify(model,null,2)+'\n'],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='system.json';a.click();URL.revokeObjectURL(a.href)}};
render();
</script>
</body></html>
"""


def build(input_path: Path, output_dir: Path) -> None:
    model = json.loads(input_path.read_text())
    errors = validate_system_map(model)
    if errors:
        raise SystemExit("\n".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "system.mmd").write_text(render_mermaid(model))
    (output_dir / "system.html").write_text(render_html(model))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an observstory.system-map/v0 artifact")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, default=Path("architecture"))
    args = parser.parse_args()
    build(args.input, args.out)


if __name__ == "__main__":
    main()
