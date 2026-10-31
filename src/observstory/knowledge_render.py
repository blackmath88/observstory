"""Project Knowledge view: knowledge artifact (+ optional changes) -> one static HTML page.

Built from knowledge.brief(), the same answer agents get, so the page and the query cannot disagree.
Every source string is escaped and the page has no script: embedded HTML in a document stays text.
Styling reuses the Project Map's tokens (map_render.CSS); nothing here interprets documents.
"""

from __future__ import annotations

import json

from . import knowledge
from .map_render import CSS as MAP_CSS
from .map_render import esc

BASIS_WORD = {
    "source_declared": "declared in source",
    "manifest_classification": "manifest classification",
    "manifest_declared": "declared by manifest",
    "coordination_confirmed": "confirmed in coordination.json",
    "coordination_recorded": "recorded in coordination.json",
}
REASON_WORD = {
    "no_current_declaration": "no record is declared current",
    "conflicting_declarations": "more than one record is declared current",
    "declaration_unverified": "the current declaration was not found in a source file",
    "superseded_but_current": "the declared current record is superseded by another",
    "supersession_cycle": "supersession links form a cycle",
    "source_unreadable": "the declared current source could not be read",
}


def _link(href, text):
    return f'<a href="{esc(href)}">{esc(text)}</a>' if href else esc(text)


def _where(r):
    loc = r.get("location") or {}
    lines = (f":{loc['start_line']}" + (f"–{loc['end_line']}" if loc.get("end_line") != loc.get("start_line") else "")
             if loc.get("start_line") else "")
    return _link(r.get("url"), f"{r.get('path')}{lines}")


def _basis(b):
    decl = "".join(
        f'<li>{_link(d["url"], d["path"] + (":" + str(d["line"]) if d["line"] else ""))} '
        f'<q>{esc(d["quote"])}</q>{"" if d["found"] else " <span class=\"warn\">not found at this commit</span>"}</li>'
        for d in b["declarations"])
    return (f'<div class="basis"><span class="bk b-{esc(b["kind"])}">{esc(BASIS_WORD.get(b["kind"], b["kind"]))}</span>'
            + (f"<ul>{decl}</ul>" if decl else "") + "</div>")


def _record(r):
    excerpt = ""
    if r.get("excerpt"):
        excerpt = f'<details class="ex"><summary>source excerpt</summary><pre>{esc(r["excerpt"])}</pre></details>'
    extra = f'<p class="muted">confirmed_by (recorded claim): {esc(r["confirmed_by"])}</p>' if r.get("confirmed_by") else ""
    note = f'<p class="muted">{esc(r["note"])}</p>' if r.get("note") else ""
    blob = f' · <span class="mono muted" title="Git blob">{esc((r.get("blob") or "")[:10])}</span>' if r.get("blob") else ""
    return (f'<article class="kr" id="r-{esc(r["id"])}" data-id="{esc(r["id"])}" data-status="{esc(r["status"])}">'
            f'<header><span class="st s-{esc(r["status"])}">{esc(r["status"])}</span>'
            f'<span class="mono rid">{esc(r["id"])}</span></header>'
            f'<p class="kt">{esc(r.get("title") or r.get("path"))}</p>'
            f'<p class="src">{_where(r)}{blob}</p>{_basis(r["basis"])}{extra}{note}{excerpt}</article>')


def _section(title, items, empty, sid):
    body = "".join(_record(r) for r in items) or f'<p class="muted">{esc(empty)}</p>'
    return f'<section class="ks" id="{sid}"><h2 class="sh">{esc(title)} <span>{len(items)}</span></h2>{body}</section>'


def _changes(diff):
    if diff is None:
        return ('<section class="ks" id="changes"><h2 class="sh">Changes</h2>'
                '<p class="muted">No comparison was requested for this build.</p></section>')
    if diff["state"] != "compared":
        return (f'<section class="ks" id="changes" data-state="{esc(diff["state"])}"><h2 class="sh">Changes</h2>'
                f'<p><b>{esc(diff["state"])}</b>: {esc(diff.get("reason"))}</p>'
                f'<p class="muted">{esc(diff.get("evidence_note", ""))}</p></section>')
    b, rec = diff["base"], diff["records"]
    rows = []
    for key, label in (("added", "added"), ("removed", "removed"), ("removal_unconfirmed", "missing, removal unconfirmed"),
                       ("status_changed", "status changed"), ("content_changed", "content changed"),
                       ("unreadable_in_target", "unreadable now")):
        for x in rec[key]:
            detail = f' {esc(x["from"])} → {esc(x["to"])}' if key == "status_changed" else ""
            rows.append(f'<li data-change="{key}"><span class="st">{esc(label)}</span> '
                        f'<a class="mono" href="#r-{esc(x["id"])}">{esc(x["id"])}</a>{detail}</li>')
    rel = diff["relationships"]
    rows += [f'<li data-change="rel_added"><span class="st">link added</span> {esc(" ".join(e))}</li>' for e in rel["added"]]
    rows += [f'<li data-change="rel_removed"><span class="st">link removed</span> {esc(" ".join(e))}</li>' for e in rel["removed"]]
    sel = diff["selection"]
    sel_line = (f'<p><b>Current direction changed</b>: {esc(sel["from"]["record"] or sel["from"]["reason"])} → '
                f'{esc(sel["to"]["record"] or sel["to"]["reason"])}</p>' if sel["changed"] else "")
    return (f'<section class="ks" id="changes" data-state="compared"><h2 class="sh">Changes <span>{len(rows)}</span></h2>'
            f'<p class="muted">Since {esc(b["requested_ref"])} = <span class="mono">{esc(b["resolved_commit"][:12])}</span> '
            f'({esc(b["snapshot_id"])}{"" if b["complete"] else ", incomplete"}). {rec["unchanged"]} record(s) unchanged. '
            f'Ancestry is not inferred.</p>{sel_line}<ul class="chg">{"".join(rows) or "<li class=muted>No record changes.</li>"}</ul></section>')


def render_knowledge(a: dict, diff: dict | None = None, map_href: str | None = None, data_href: str = "data/knowledge.json") -> str:
    ans = knowledge.brief(a)["answer"]
    s = knowledge.receipt(a)
    cd = ans["current_direction"]
    if cd["state"] == "selected":
        current = (f'<div class="current" data-state="selected">{_record(cd["record"])}</div>')
    else:
        cands = ", ".join(cd["candidates"]) or "none"
        current = (f'<div class="current unresolved" data-state="unresolved" data-reason="{esc(cd["reason"])}">'
                   f'<p><b>Unresolved</b>: {esc(REASON_WORD.get(cd["reason"], cd["reason"]))}. Candidates: '
                   f'<span class="mono">{esc(cands)}</span>. The producer does not choose by date or order.</p></div>')
    diags = "".join(f'<li class="d-{esc(d["severity"])}"><b>{esc(d["severity"])}</b> <span class="mono">{esc(d["code"])}</span> '
                    f'{esc(d["subject"])}: {esc(d["message"])}</li>' for d in a["diagnostics"])
    sources = "".join(f'<tr><td class="mono">{_link(f"https://github.com/{s["repository"]}/blob/{s["resolved_commit"]}/{x["path"]}" if s["repository"] != "local/unknown" else None, x["path"])}</td>'
                      f'<td class="mono">{esc((x["blob"] or "—")[:10])}</td><td>{esc(x["status"])}</td></tr>' for x in a["sources"])
    rels = "".join(f'<li><a class="mono" href="#r-{esc(x["from"])}">{esc(x["from"])}</a> <b>{esc(x["rel"])}</b> '
                   f'<a class="mono" href="#r-{esc(x["to"])}">{esc(x["to"])}</a>'
                   f'{"" if x["resolved"] else " <span class=warn>dangling</span>"} · '
                   f'<span class="bk b-{esc(x["basis"]["kind"])}">{esc(BASIS_WORD.get(x["basis"]["kind"], x["basis"]["kind"]))}</span></li>'
                   for x in ans["relationships"])
    incomplete = "" if a["complete"] else (f'<p class="degraded">Incomplete: {esc(", ".join(a["completeness"]["failed"]) or "see diagnostics")} '
                                           f'could not be read. Missing sources are not treated as deleted.</p>')
    back = f'<a href="{esc(map_href)}">Project Map</a> · ' if map_href else ""
    repo = s["repository"]
    repo_link = _link(f"https://github.com/{repo}" if repo != "local/unknown" else None, repo)
    commit_link = _link(f"https://github.com/{repo}/tree/{s['resolved_commit']}" if repo != "local/unknown" else None,
                        s["resolved_commit"][:12])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Knowledge · {esc(repo)}</title>
<style>{MAP_CSS}{CSS}</style>
</head>
<body>
<header class="top">
  <div class="id"><span class="mark">Observstory · Project Knowledge</span><h1>{esc(ans["title"])}</h1>
    <span class="sub">{repo_link} · {esc(s["requested_ref"])} = <span class="mono">{commit_link}</span></span></div>
  <p class="status"><b class="{"" if s["complete"] else "hot"}">{"complete" if s["complete"] else "incomplete"}</b> ·
    <span class="mono">{esc(s["snapshot_id"])}</span>
    <span class="fresh">generated {esc(s["generated_at"])} · upstream not checked</span></p>
</header>
{incomplete}
<main class="klayout">
  <div class="kmain">
    <section class="ks" id="current"><h2 class="sh">Current direction</h2>{current}</section>
    {_section("Declared decisions", ans["decisions"], "No decisions are declared.", "decisions")}
    {_section("Open questions", ans["open_questions"], "No open questions are declared.", "questions")}
    {_section("Plans", ans["plans"], "No current plan is declared.", "plans")}
    {_section("Research and evidence", ans["research"], "No research is selected.", "research")}
    {_section("Retired: superseded and historical", ans["retired"], "Nothing is marked superseded or historical.", "retired")}
  </div>
  <aside class="side">
    {_changes(diff)}
    <section class="ks" id="freshness"><h2 class="sh">Freshness and basis</h2>
      <p>Every file was read as a Git object of <span class="mono">{esc(s["resolved_commit"][:12])}</span>
      (requested <span class="mono">{esc(s["requested_ref"])}</span>). Generation time is not proof of a recent fetch:
      {esc(s["upstream_check"])}.</p>
      <p class="muted">Policy {esc(s["selection_policy"])} · producer {esc(s["producer_version"])} ·
      audience {esc(a["source"]["audience"])}. {esc(knowledge.NOTE)}</p></section>
    <section class="ks" id="diagnostics"><h2 class="sh">Diagnostics <span>{len(a["diagnostics"])}</span></h2>
      <ul class="diag">{diags or '<li class="muted">None.</li>'}</ul></section>
    <section class="ks" id="relationships"><h2 class="sh">Explicit relationships <span>{len(ans["relationships"])}</span></h2>
      <ul class="rels">{rels or '<li class="muted">None declared.</li>'}</ul></section>
    <section class="ks" id="sources"><h2 class="sh">Sources read <span>{len(a["sources"])}</span></h2>
      <table class="srct"><thead><tr><th>path</th><th>blob</th><th>read</th></tr></thead><tbody>{sources}</tbody></table></section>
    <p class="foot">{back}<a href="{esc(data_href)}">knowledge.json</a></p>
    <p class="foot muted">Orientation, not authority: statuses are declarations, not approvals.</p>
  </aside>
</main>
<script type="application/json" id="knowledge-receipt">{json.dumps(s).replace("<", "\\u003c")}</script>
</body>
</html>"""


CSS = r"""
.klayout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:28px;padding:22px 28px 40px;align-items:start}
.kmain{min-width:0;display:flex;flex-direction:column;gap:22px}
.ks{margin:0 0 18px}
.sh{margin:0 0 8px;font-size:11.5px;font-weight:650;letter-spacing:.09em;text-transform:uppercase;color:var(--ink2)}
.sh span{font:500 10.5px var(--mono);color:var(--ink3);margin-left:4px}
.kr{background:var(--surface);border:1px solid var(--hair);border-radius:10px;padding:10px 12px;margin:0 0 8px}
.kr header{display:flex;gap:8px;align-items:baseline}
.rid{color:var(--ink3)}
.kt{margin:4px 0 2px;font-weight:600}
.src{margin:0;color:var(--ink2);font-size:12px}
.st{display:inline-block;font:600 10.5px var(--mono);padding:1px 6px;border-radius:4px;background:var(--t2);color:var(--ink2)}
.s-current,.s-declared,.s-open{background:var(--accent-t);color:var(--accent)}
.s-superseded,.s-historical{text-decoration:line-through;color:var(--ink3)}
.current .kr{border-color:var(--accent);border-width:2px}
.current.unresolved{border:2px dashed var(--accent);border-radius:10px;padding:10px 12px;background:var(--surface)}
.basis{margin-top:6px;font-size:12px;color:var(--ink2)}
.basis ul{margin:4px 0 0;padding-left:16px}
.basis q{color:var(--ink)}
.bk{font:600 10px var(--sans);letter-spacing:.04em;text-transform:uppercase;color:var(--ink3)}
.b-source_declared,.b-coordination_confirmed{color:var(--accent)}
.warn{color:var(--accent);font-weight:600}
.ex summary{cursor:pointer;color:var(--ink3);font-size:12px;margin-top:6px}
.ex pre{white-space:pre-wrap;font:12px/1.45 var(--mono);background:var(--bg);border:1px solid var(--hair);border-radius:6px;padding:8px;max-height:320px;overflow:auto}
.chg,.diag,.rels{margin:0;padding-left:16px;font-size:12px}
.chg li,.diag li,.rels li{margin:3px 0}
.d-error b{color:var(--accent)}
.srct{width:100%;border-collapse:collapse;font-size:11.5px}
.srct td,.srct th{border-bottom:1px solid var(--hair);padding:3px 4px;text-align:left;vertical-align:top;word-break:break-all}
.srct th{color:var(--ink3);font-weight:600}
@media (max-width:900px){.klayout{grid-template-columns:1fr;padding:16px}}
"""
