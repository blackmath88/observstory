/* Observatory — Project Memory. Presents a precomputed observstory.memory-ui/v1 bundle.
   All state reduction happens in Python (observstory.memory); this file only shows and compares those states.
   Every piece of source text is inserted with textContent; links are limited to https://github.com/. */
(function () {
  "use strict";
  const root = document.getElementById("app");
  const LIVE = root.dataset.live === "1";
  const API = root.dataset.api || "api/";
  let B = JSON.parse(document.getElementById("bundle").textContent);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const S = { tab: "now", sel: null, snap: null, known: "", cmpFrom: null, cmpTo: null, rp: null, playing: null,
              speed: 1, follow: true, packet: null, lastFocus: null };

  // ------------------------------------------------------------ helpers
  function el(tag, attrs, ...kids) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? "" : v);
    }
    for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false) n.append(k instanceof Node ? k : document.createTextNode(String(k)));
    return n;
  }
  const svgNS = "http://www.w3.org/2000/svg";
  function sv(tag, attrs, ...kids) {
    const n = document.createElementNS(svgNS, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "text") n.textContent = v; else if (k.startsWith("on")) n.addEventListener(k.slice(2), v); else n.setAttribute(k, v);
    }
    kids.flat().forEach(k => k && n.append(k));
    return n;
  }
  function safeUrl(u) { return typeof u === "string" && /^https:\/\/github\.com\/[^\s<>"']+$/.test(u) ? u : null; }
  function link(u, text) { const s = safeUrl(u); return s ? el("a", { href: s, target: "_blank", rel: "noopener noreferrer", text: text || "source" }) : el("span", { class: "faint", text: "no link" }); }
  const short = s => (s || "").slice(0, 12);
  function when(t) { if (!t) return "unknown"; const d = new Date(t); return isNaN(d) ? t : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); }
  const chip = (s, extra) => el("span", { class: "chip " + String(s).replace(/[^a-z_]/gi, ""), text: extra || s });
  const V = id => B.versions[id];
  function recTitle(rid, frame) {
    const e = frame && frame.records[rid]; const v = e && V(e[0]);
    if (v) return v.title || rid;
    const any = Object.values(B.versions).find(x => x.record === rid); return any ? (any.title || rid) : rid;
  }
  function frameNow() { return B.now ? B.now.frame : { records: {}, relations: [], direction: null, proposals: {} }; }
  function snapLabel(s) { return `#${s.position} ${short(s.commit)} · ${when(s.source_time)}${s.changed === false ? "" : " · changed"}`; }

  // ------------------------------------------------------------ routing
  const TABS = [["now", "Now"], ["history", "History"], ["graph", "Graph"], ["context", "Context"]];
  function readHash() {
    const h = location.hash.replace(/^#\/?/, "");
    const [tab, q] = h.split("?");
    S.tab = TABS.some(t => t[0] === tab) ? tab : "now";
    const p = new URLSearchParams(q || "");
    S.sel = p.get("sel");
    if (p.get("snap")) S.snap = p.get("snap");
  }
  function writeHash() {
    const p = new URLSearchParams();
    if (S.sel) p.set("sel", S.sel);
    if (S.tab === "history" && S.snap) p.set("snap", S.snap);
    const h = "#/" + S.tab + (p.toString() ? "?" + p : "");
    if (location.hash !== h) history.replaceState(null, "", h);
  }
  function go(tab) { S.tab = tab; writeHash(); render(); document.getElementById("main").focus({ preventScroll: true }); }
  function select(kind, id) {
    S.lastFocus = document.activeElement;
    S.sel = kind + ":" + id; writeHash(); render();
    const ins = document.getElementById("inspector");
    ins.classList.add("open");
    const h = ins.querySelector("h2"); if (h) { h.tabIndex = -1; h.focus({ preventScroll: window.innerWidth > 900 }); }
  }
  function closeInspector() {
    S.sel = null; writeHash(); render();
    if (S.lastFocus && document.body.contains(S.lastFocus)) S.lastFocus.focus();
  }
  function rowBtn(kind, id, kids) {
    const pressed = S.sel === kind + ":" + id;
    return el("button", { class: "row", type: "button", "aria-pressed": pressed ? "true" : "false", onclick: () => select(kind, id) }, kids);
  }

  // ------------------------------------------------------------ header & status
  function needsHuman() {
    const ps = B.now ? Object.values(B.now.proposals) : [];
    return ps.some(p => ["unreviewed", "needs_changes"].includes(p.status.state)) || ps.some(p => p.status.stale_evidence.length);
  }
  function header() {
    const lit = needsHuman();
    const ing = (B.status && B.status.ingestion) || { state: "not_reported" };
    const idx = (B.status && B.status.indexing) || { state: "not_reported" };
    const c = B.now && B.now.cutoff;
    const markTpl = document.getElementById(lit ? "mark-lit" : "mark");
    const mark = el("span", { class: "mark", role: "img", "aria-label": lit ? "Observatory, window lit: something needs a human review" : "Observatory, window dark: nothing awaits review" });
    mark.append(markTpl.content.cloneNode(true));
    const m = mark.querySelector("svg"); if (m) { m.setAttribute("width", "40"); m.setAttribute("height", "40"); m.setAttribute("aria-hidden", "true"); }
    return el("header", { class: "top" }, mark,
      el("div", {}, el("h1", { text: "Observatory — Project Memory" }), el("div", { class: "repo mono", text: `${B.repository} · ${B.requested_ref || ""}` })),
      el("div", { class: "fresh", role: "status", "aria-live": "polite" },
        el("span", { class: "pill" + (c ? " ok" : " warn"), text: c ? `recorded through #${c.position ?? (B.head && B.head.position)} · ${short(c.commit)}` : "nothing recorded" }),
        el("span", { class: "pill" + (["current", "regenerated"].includes(ing.state) ? "" : " warn"), title: ing.detail || "", text: `ingestion: ${ing.state}${ing.at ? " · " + when(ing.at) : ""}` }),
        el("span", { class: "pill" + (idx.state === "current" ? "" : " warn"), title: idx.reason || "", text: `semantic index: ${idx.state}` }),
        lit ? el("span", { class: "pill warn", text: "review needed" }) : null,
        LIVE ? el("button", { class: "btn", type: "button", onclick: refresh, text: "Reload data" }) : el("span", { class: "pill", text: "static export" })));
  }
  function tabs() {
    return el("nav", { class: "tabs", "aria-label": "Views" }, TABS.map(([k, label]) =>
      el("a", { href: "#/" + k, "aria-current": S.tab === k ? "page" : null, onclick: e => { e.preventDefault(); go(k); } }, label)));
  }

  // ------------------------------------------------------------ NOW
  const GROUPS = [["decision", "Decisions"], ["plan", "Plans"], ["question", "Open questions"], ["research", "Research"], ["module", "Modules"], ["concept", "Concepts"]];
  function recordRow(rid, entry) {
    const v = V(entry[0]);
    return el("li", {}, rowBtn("record", rid, [el("span", { class: "title", text: v.title || rid }), chip(v.status),
      entry[1] !== "current" ? chip("unavailable", "source unavailable") : null, el("span", { class: "faint mono", text: v.path + (v.section ? " § " + v.section : "") })]));
  }
  function viewNow() {
    if (!B.now) return el("div", { class: "empty", text: "Nothing has been recorded for this repository yet. History before the first manifest is unavailable, not empty." });
    const f = B.now.frame, d = f.direction || { state: "unresolved" };
    const dv = d.record && f.records[d.record] && V(f.records[d.record][0]);
    const out = [];
    out.push(el("section", { class: "panel" }, el("h2", {}, "Current direction"), el("div", { class: "body" },
      dv ? el("div", { class: "direction" }, el("div", { class: "t", text: dv.title }), el("div", {}, chip(dv.status), " ", el("span", { class: "faint", text: `${d.reason} · basis ${dv.basis.kind} · version ${dv.version_id}` })),
        el("div", {}, el("button", { class: "btn", type: "button", onclick: () => select("record", d.record), text: "Inspect evidence" }), " ", link(dv.url, "Open source at its commit")))
        : el("div", { class: "note warn", text: `Direction ${d.state}: ${d.reason || "no single current concept is declared"}` }))));
    const groups = el("div", { class: "grid2" });
    const hist = [];
    for (const [type, label] of GROUPS) {
      const ids = Object.keys(f.records).filter(r => V(f.records[r][0]).type === type);
      const live = ids.filter(r => !["superseded", "historical"].includes(V(f.records[r][0]).status) && r !== d.record);
      ids.filter(r => !live.includes(r) && r !== d.record).forEach(r => hist.push(r));
      if (!live.length) continue;
      groups.append(el("section", { class: "panel" }, el("h2", {}, label, el("span", { class: "faint", text: String(live.length) })), el("ul", { class: "rows" }, live.map(r => recordRow(r, f.records[r])))));
    }
    out.push(groups);
    const props = Object.entries(B.now.proposals);
    out.push(el("section", { class: "panel" }, el("h2", {}, "Proposals and findings", el("span", { class: "faint", text: String(props.length) })),
      props.length ? el("ul", { class: "rows" }, props.map(([pid, p]) => el("li", {}, rowBtn("proposal", pid, [el("span", { class: "title", text: p.proposal.title }),
        chip(p.status.state), p.status.stale_evidence.length ? chip("stale", "base stale") : null,
        el("span", { class: "faint", text: `${p.proposal.kind} · ${p.proposal.author.name} (${p.proposal.author.kind})` })]))))
        : el("div", { class: "empty", text: "No proposals recorded. Findings come back as .observstory/proposals/*.json through a pull request; only a human review record accepts one." })));
    if (hist.length) out.push(el("section", { class: "panel" }, el("details", {}, el("summary", { class: "row", text: `Historical and superseded (${hist.length}) — kept, not current` }),
      el("ul", { class: "rows" }, hist.map(r => recordRow(r, f.records[r]))))));
    const cb = B.now.coverage_boundaries || [];
    out.push(el("section", { class: "panel" }, el("h2", {}, "Coverage and freshness"), el("div", { class: "body" },
      el("dl", { class: "kv" },
        el("dt", { text: "Snapshot" }), el("dd", { class: "mono", text: B.now.cutoff.snapshot_id }),
        el("dt", { text: "Commit" }), el("dd", {}, el("span", { class: "mono", text: B.now.cutoff.commit }), " ", el("span", { class: "faint", text: when(B.now.cutoff.source_time) })),
        el("dt", { text: "Complete" }), el("dd", { text: B.head && B.head.complete ? "yes — every selected source was read" : "no — some selected sources could not be read; nothing was removed because of it" }),
        el("dt", { text: "Ingestion" }), el("dd", { text: JSON.stringify(B.status.ingestion) }),
        el("dt", { text: "Semantic index" }), el("dd", { text: JSON.stringify(B.status.indexing) }),
        el("dt", { text: "History starts" }), el("dd", { text: cb.length ? `commit ${short(cb[0].commit)}: ${cb[0].note}` : "unknown" }),
        el("dt", { text: "Data host" }), el("dd", { text: (B.host && (B.host.kind + " — " + B.host.note)) || "unknown" })))));
    return out;
  }

  // ------------------------------------------------------------ HISTORY
  function snapById(id) { return B.snapshots.find(s => s.snapshot_id === id); }
  function diffFrames(a, b) {
    const out = [];
    for (const [rid, e] of Object.entries(b.records)) {
      const o = a.records[rid];
      if (!o) out.push(["added", rid, null, e[0]]);
      else if (o[0] !== e[0]) out.push([V(o[0]).status !== V(e[0]).status ? "status" : "revised", rid, o[0], e[0]]);
      else if (o[1] !== e[1]) out.push([e[1], rid, o[0], e[0]]);
    }
    for (const rid of Object.keys(a.records)) if (!b.records[rid]) out.push(["no longer selected", rid, a.records[rid][0], null]);
    const ar = new Set(a.relations), br = new Set(b.relations);
    for (const l of br) if (!ar.has(l)) out.push(["link added", l]);
    for (const l of ar) if (!br.has(l)) out.push(["link ended", l]);
    return out;
  }
  function relText(lid) { const r = B.relation_versions[lid]; return r ? `${r.from} ${r.rel} ${r.to}` : lid; }
  function diffList(changes) {
    if (!changes.length) return el("div", { class: "empty", text: "No recorded knowledge differences between these points." });
    return el("ul", { class: "rows" }, changes.map(([k, id, from, to]) => el("li", {}, k.startsWith("link") ?
      el("div", { class: "row" }, el("span", { class: k === "link added" ? "diff-add" : "diff-del", text: k }), el("span", { class: "title mono", text: relText(id) })) :
      rowBtn("record", id, [el("span", { class: k === "added" ? "diff-add" : k === "no longer selected" ? "diff-del" : "", text: k }), el("span", { class: "title", text: recTitle(id, { records: { [id]: [to || from] } }) }),
        from && to && V(from).status !== V(to).status ? el("span", { class: "faint", text: `${V(from).status} → ${V(to).status}` }) : null]))));
  }
  function viewHistory() {
    const snaps = B.snapshots;
    if (!snaps.length) return el("div", { class: "empty", text: "No snapshots recorded." });
    if (!S.snap || !snapById(S.snap)) S.snap = snaps[snaps.length - 1].snapshot_id;
    const knownTimes = Object.keys(B.known_at_frames || {});
    const frame = S.known ? B.known_at_frames[S.known] : B.snapshot_frames[S.snap];
    const cur = S.known ? null : snapById(S.snap);
    const opts = (sel) => snaps.slice().reverse().map(s => el("option", { value: s.snapshot_id, selected: s.snapshot_id === sel ? true : null, text: snapLabel(s) }));
    const controls = el("div", { class: "controls" },
      el("label", {}, "Repository revision", el("select", { onchange: e => { S.snap = e.target.value; S.known = ""; writeHash(); render(); } }, opts(S.snap))),
      el("label", {}, "System as known at", el("select", { onchange: e => { S.known = e.target.value; render(); } },
        el("option", { value: "", text: "— use revision —" }), knownTimes.map(t => el("option", { value: t, selected: S.known === t ? true : null, text: when(t) + " (recorded)" })))));
    const recs = Object.entries(frame.records).sort((a, b) => V(a[1][0]).type.localeCompare(V(b[1][0]).type) || a[0].localeCompare(b[0]));
    const stateP = el("section", { class: "panel" }, el("h2", {}, S.known ? `State as this system knew it at ${when(S.known)}` : `State at ${cur ? snapLabel(cur) : ""}`),
      el("div", { class: "body" }, el("div", { class: "note", text: S.known ?
        "Only events this memory had recorded by then. Later ingestion — including backfilled history — is excluded." :
        "Only knowledge from this first-parent revision and earlier on this lineage. Later commits and later graph knowledge are excluded." }),
        el("p", { class: "faint", text: `direction: ${frame.direction ? frame.direction.state + " " + (frame.direction.record || "") : "none"} · ${recs.length} records · ${frame.relations.length} declared links` })),
      el("ul", { class: "rows" }, recs.map(([rid, e]) => recordRow(rid, e))));
    // compare
    if (!S.cmpTo) S.cmpTo = snaps[snaps.length - 1].snapshot_id;
    if (!S.cmpFrom) S.cmpFrom = snaps[0].snapshot_id;
    const a = snapById(S.cmpFrom), b = snapById(S.cmpTo);
    const between = B.events.filter(e => { const s = snapById(e.snapshot_id); return s && a && b && s.lineage === b.lineage && s.position > Math.min(a.position, b.position) && s.position <= Math.max(a.position, b.position); });
    const cmp = el("section", { class: "panel" }, el("h2", {}, "Compare two revisions"), el("div", { class: "body" },
      el("div", { class: "controls" },
        el("label", {}, "From", el("select", { onchange: e => { S.cmpFrom = e.target.value; render(); } }, opts(S.cmpFrom))),
        el("label", {}, "To", el("select", { onchange: e => { S.cmpTo = e.target.value; render(); } }, opts(S.cmpTo)))),
      a && b && a.lineage !== b.lineage ? el("div", { class: "note warn", text: "Different lineages: no ancestry is inferred across a force-push or divergence." }) :
        diffList(diffFrames(B.snapshot_frames[S.cmpFrom], B.snapshot_frames[S.cmpTo])),
      el("p", { class: "faint", text: `${between.length} recorded events between them. A diff states what changed, never why; reasons appear only where a source declares them.` })));
    return [controls, el("div", { class: "grid2" }, stateP, cmp), replayPanel()];
  }

  // ------------------------------------------------------------ REPLAY (shared with Graph)
  function rpFrame() { const r = B.replay[S.rp]; return r ? r.frame : frameNow(); }
  function setRp(i) { S.rp = Math.max(0, Math.min(B.replay.length - 1, i)); render(); }
  function play() {
    if (S.playing) { clearInterval(S.playing); S.playing = null; render(); return; }
    if (S.rp === null || S.rp >= B.replay.length - 1) S.rp = 0;
    S.playing = setInterval(() => { if (S.rp >= B.replay.length - 1) { clearInterval(S.playing); S.playing = null; } else S.rp++; render(); }, 900 / S.speed);
    render();
  }
  function scrubber() {
    if (!B.replay.length) return el("div", { class: "empty", text: "No knowledge events to replay." });
    if (S.rp === null) S.rp = B.replay.length - 1;
    const ev = B.events.find(e => e.seq === B.replay[S.rp].seq);
    return el("div", { class: "scrub", role: "group", "aria-label": "Replay position" },
      el("button", { class: "btn", type: "button", onclick: () => setRp(S.rp - 1), "aria-label": "Previous event", text: "◀" }),
      el("button", { class: "btn primary", type: "button", onclick: play, "aria-pressed": S.playing ? "true" : "false", text: S.playing ? "Pause" : "Play" }),
      el("button", { class: "btn", type: "button", onclick: () => setRp(S.rp + 1), "aria-label": "Next event", text: "▶" }),
      el("input", { type: "range", min: "0", max: String(B.replay.length - 1), value: String(S.rp), "aria-label": "Replay event", "aria-valuetext": `event ${ev.seq}: ${ev.type} ${ev.subject}`, oninput: e => setRp(+e.target.value) }),
      el("label", { class: "faint" }, "speed ", el("select", { onchange: e => { S.speed = +e.target.value; if (S.playing) { clearInterval(S.playing); S.playing = null; play(); } } },
        [0.5, 1, 2, 4].map(x => el("option", { value: String(x), selected: S.speed === x ? true : null, text: x + "×" })))),
      el("span", { class: "mono faint", "aria-live": "polite", text: `event ${ev.seq}/${B.events[B.events.length - 1].seq} · ${ev.type} · ${ev.subject}` }));
  }
  function replayPanel() {
    const curSeq = B.replay.length ? B.replay[S.rp === null ? B.replay.length - 1 : S.rp].seq : null;
    const rows = B.events.map(e => el("tr", { class: e.seq === curSeq ? "cur" : (curSeq !== null && e.seq > curSeq ? "future" : "") },
      el("td", { class: "mono", text: String(e.seq) }), el("td", { text: when(e.recorded_at) }), el("td", { class: "mono", text: short(e.commit) }),
      el("td", {}, el("button", { class: "row", type: "button", style: "padding:0;min-height:0", onclick: () => select("event", e.event_id), text: e.type })),
      el("td", { class: "mono", text: e.relation ? `${e.relation.from} ${e.relation.rel} ${e.relation.to}` : e.subject }),
      el("td", { class: "faint", text: e.note || (e.reason ? "reason: source declared" : "") })));
    return el("section", { class: "panel" }, el("h2", {}, "Knowledge replay — recorded events"), el("div", { class: "body" },
      el("p", { class: "faint", text: "Replays this memory's recorded knowledge events in order. Repository file history and retrieval-index jobs are separate logs and are not mixed in here." }),
      scrubber(),
      el("div", { class: "scroll" }, el("table", { class: "log" }, el("thead", {}, el("tr", {}, ["seq", "recorded", "commit", "event", "subject", "note"].map(h => el("th", { scope: "col", text: h })))), el("tbody", {}, rows)))));
  }

  // ------------------------------------------------------------ GRAPH
  function viewGraph() {
    const f = S.follow ? rpFrame() : frameNow();
    const nodes = B.layout.nodes, cols = B.layout.columns;
    const W = 190, H = 34, GX = 220, GY = 52, X0 = 16, Y0 = 40;
    const maxRow = Math.max(0, ...Object.values(nodes).map(n => n.row));
    const width = X0 * 2 + GX * cols.length, height = Y0 + GY * (maxRow + 1) + 20;
    const pos = id => nodes[id] ? { x: X0 + nodes[id].col * GX, y: Y0 + nodes[id].row * GY } : null;
    const svg = sv("svg", { class: "graph", viewBox: `0 0 ${width} ${height}`, width: String(width), height: String(height), role: "group", "aria-label": "Knowledge graph: records by type, declared links" });
    cols.forEach((c, i) => svg.append(sv("text", { class: "col-h", x: String(X0 + i * GX), y: "22", text: c })));
    const edges = sv("g", {}), labels = sv("g", {});
    for (const lid of f.relations) {
      const r = B.relation_versions[lid]; if (!r) continue;
      const a = pos(r.from), b = pos(r.to); if (!a || !b) continue;
      const x1 = a.x + W, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2;
      const same = Math.abs(x1 - W - x2) < 1;
      const d = same ? `M${a.x + W} ${y1} C${a.x + W + 30} ${y1} ${b.x + W + 30} ${y2} ${b.x + W} ${y2}` : `M${x1} ${y1} C${(x1 + x2) / 2} ${y1} ${(x1 + x2) / 2} ${y2} ${x2} ${y2}`;
      edges.append(sv("path", { class: "edge", d, "marker-end": "url(#arrow)" }, sv("title", { text: `${r.from} ${r.rel} ${r.to} (declared: ${r.origin})` })));
      labels.append(sv("text", { class: "edge-l", x: String(same ? a.x + W + 18 : (x1 + x2) / 2 - 20), y: String((y1 + y2) / 2 - 3), text: r.rel }));
    }
    for (const l of (B.suggested_links.links || [])) {
      const a = pos(l.from), b = pos(l.to); if (!a || !b) continue;
      edges.append(sv("path", { class: "edge suggested", d: `M${a.x + W} ${a.y + H / 2} L${b.x} ${b.y + H / 2}` }, sv("title", { text: `suggested by model: ${l.label}` })));
    }
    svg.append(sv("defs", {}, sv("marker", { id: "arrow", viewBox: "0 0 8 8", refX: "7", refY: "4", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" }, sv("path", { d: "M0 0 L8 4 L0 8 z", fill: "currentColor", class: "edge" }))), edges);
    const ids = Object.keys(nodes);
    ids.forEach((rid, i) => {
      const p = pos(rid), e = f.records[rid], v = e ? V(e[0]) : null;
      const cls = ["node", !e ? "absent" : "", v && ["superseded", "historical"].includes(v.status) ? "historical" : "", e && e[1] !== "current" ? "unavailable" : "", S.sel === "record:" + rid ? "sel" : ""].join(" ");
      const label = (v ? v.title : recTitle(rid)) || rid;
      const g = sv("g", { class: cls, tabindex: "0", role: "button", "aria-label": `${label}, ${v ? v.type + " " + v.status : "not selected at this point"}`, "data-i": String(i),
        onclick: () => select("record", rid), onkeydown: ev => graphKey(ev, ids, i, rid) },
        sv("rect", { x: String(p.x), y: String(p.y), width: String(W), height: String(H), rx: "5" }),
        sv("text", { x: String(p.x + 8), y: String(p.y + 14), text: label.length > 30 ? label.slice(0, 29) + "…" : label }),
        sv("text", { x: String(p.x + 8), y: String(p.y + 27), class: "edge-l", text: v ? v.status : "not selected" }));
      svg.append(g);
    });
    svg.append(labels);
    const listRows = f.relations.map(l => B.relation_versions[l]).filter(Boolean).map(r =>
      el("tr", {}, el("td", { text: recTitle(r.from, f) }), el("td", { class: "mono", text: r.rel }), el("td", { text: recTitle(r.to, f) }), el("td", { class: "faint", text: r.origin })));
    return [
      el("section", { class: "panel" }, el("h2", {}, "Atlas — records and declared links"), el("div", { class: "body" },
        el("div", { class: "controls" }, el("label", { style: "flex-direction:row;gap:6px;align-items:center" },
          el("input", { type: "checkbox", checked: S.follow ? true : null, onchange: e => { S.follow = e.target.checked; render(); } }), "Follow replay position")),
        S.follow ? scrubber() : null,
        el("div", { class: "legend" },
          el("span", {}, svgMini("edge"), " declared link (source or manifest)"),
          el("span", {}, svgMini("edge suggested"), " suggested by a model — never a declaration"),
          el("span", {}, "dashed box: superseded/historical · dotted: not selected at this point")),
        B.suggested_links.state !== "current" ? el("div", { class: "note", text: `Suggested links: ${B.suggested_links.state} — ${B.suggested_links.reason}` }) : null,
        el("div", { class: "graph-wrap" }, svg),
        el("p", { class: "faint", text: "Positions are fixed by type and first appearance, so nothing moves during replay except what actually changed. Arrow keys move between nodes; Enter inspects." }))),
      el("section", { class: "panel" }, el("h2", {}, "Links as a list"), el("div", { class: "body scroll" },
        listRows.length ? el("table", { class: "log" }, el("thead", {}, el("tr", {}, ["from", "relation", "to", "origin"].map(h => el("th", { scope: "col", text: h })))), el("tbody", {}, listRows)) : el("div", { class: "empty", text: "No declared links at this point." })))];
  }
  function svgMini(cls) { return sv("svg", { width: "28", height: "8", "aria-hidden": "true", class: "graph" }, sv("path", { class: cls, d: "M0 4 L28 4" })); }
  function graphKey(ev, ids, i, rid) {
    const n = B.layout.nodes;
    let j = null;
    if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select("record", rid); return; }
    const me = n[rid];
    const find = (dc, dr) => ids.findIndex(x => n[x].col === me.col + dc && n[x].row === me.row + dr);
    if (ev.key === "ArrowDown") j = find(0, 1); else if (ev.key === "ArrowUp") j = find(0, -1);
    else if (ev.key === "ArrowRight" || ev.key === "ArrowLeft") {
      const dc = ev.key === "ArrowRight" ? 1 : -1;
      for (let c = me.col + dc; c >= 0 && c < B.layout.columns.length && j === null; c += dc) {
        const cand = ids.map((x, k) => [x, k]).filter(([x]) => n[x].col === c);
        if (cand.length) j = cand.reduce((best, cur) => Math.abs(n[cur[0]].row - me.row) < Math.abs(n[best[0]].row - me.row) ? cur : best)[1];
      }
    }
    if (j !== null && j >= 0) { ev.preventDefault(); const t = document.querySelector(`svg.graph g[data-i="${j}"]`); if (t) t.focus(); }
  }

  // ------------------------------------------------------------ CONTEXT
  function download(name, text, type) {
    const a = el("a", { href: URL.createObjectURL(new Blob([text], { type })), download: name });
    document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
  }
  async function issue(form) {
    const body = { task: form.task.value.trim(), snapshot_id: form.snap.value || null, include_historical: form.hist.checked, limit: +form.limit.value || 12 };
    if (!body.task) { S.packet = { error: "Describe the task the context is for." }; render(); return; }
    S.packet = { pending: true }; render();
    try {
      const r = await fetch(API + "context", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
      const j = await r.json();
      S.packet = r.ok ? j : { error: j.error || r.statusText };
    } catch (e) { S.packet = { error: String(e) }; }
    render();
    const out = document.getElementById("packet-out"); if (out) out.focus();
  }
  function packetView(P) {
    if (!P) return null;
    if (P.pending) return el("div", { class: "empty", role: "status", text: "Issuing…" });
    if (P.error) return el("div", { class: "note warn", role: "alert", text: P.error });
    const p = P.packet;
    return el("section", { class: "panel", id: "packet-out", tabindex: "-1" }, el("h2", {}, "Issued packet ", el("span", { class: "mono", text: p.packet_id })),
      el("div", { class: "body" },
        el("dl", { class: "kv" },
          el("dt", { text: "Cutoff" }), el("dd", { class: "mono", text: p.cutoff ? `${p.cutoff.snapshot_id} · ${short(p.cutoff.commit)} · #${p.cutoff.position}` : p.reason }),
          el("dt", { text: "Records" }), el("dd", { text: p.records ? `${p.records.length} included · ${p.omissions.length} omitted with reasons` : "—" }),
          el("dt", { text: "Proposals" }), el("dd", { text: p.proposals ? p.proposals.map(x => `${x.id}: ${x.state}`).join(", ") || "none" : "—" }),
          el("dt", { text: "Receipt" }), el("dd", { class: "mono", text: P.receipt ? `${P.receipt.receipt_id} · ${when(P.receipt.issued_at)}` : "not recorded (static export)" }),
          el("dt", { text: "Hashes" }), el("dd", { class: "mono", text: P.receipt ? `json ${short(P.receipt.json_sha256)} · md ${short(P.receipt.markdown_sha256)}` : "—" })),
        el("div", { class: "note", text: "Issued does not mean read. An assistant's use of this packet is only known if it cites the packet_id in what it returns." }),
        el("div", { class: "controls" },
          el("button", { class: "btn primary", type: "button", onclick: () => download(p.packet_id + ".json", JSON.stringify(p, null, 2) + "\n", "application/json"), text: "Download JSON" }),
          el("button", { class: "btn", type: "button", onclick: () => download(p.packet_id + ".md", P.markdown, "text/markdown"), text: "Download Markdown" }),
          navigator.clipboard ? el("button", { class: "btn", type: "button", onclick: () => navigator.clipboard.writeText(P.markdown), text: "Copy Markdown" }) : null),
        el("pre", { class: "src", "aria-label": "Markdown preview", text: P.markdown })));
  }
  function viewContext() {
    const snaps = B.snapshots.slice().reverse();
    const form = el("form", { onsubmit: e => { e.preventDefault(); issue(e.target); } },
      el("label", { class: "faint", for: "task" }, "Task the context is for"),
      el("textarea", { id: "task", name: "task", placeholder: "e.g. Review the current concept and its research basis before proposing the next experiment", disabled: LIVE ? null : true }),
      el("div", { class: "controls" },
        el("label", {}, "Revision", el("select", { name: "snap", disabled: LIVE ? null : true }, el("option", { value: "", text: "head (latest recorded)" }), snaps.map(s => el("option", { value: s.snapshot_id, text: snapLabel(s) })))),
        el("label", {}, "Task records limit", el("input", { type: "number", name: "limit", value: "12", min: "1", max: "50", disabled: LIVE ? null : true })),
        el("label", { style: "flex-direction:row;gap:6px;align-items:center" }, el("input", { type: "checkbox", name: "hist", disabled: LIVE ? null : true }), "include historical records"),
        el("button", { class: "btn primary", type: "submit", disabled: LIVE ? null : true, text: "Issue packet" })));
    const out = [el("section", { class: "panel" }, el("h2", {}, "Reading desk — task context"), el("div", { class: "body" },
      el("p", { class: "muted", text: "One projection produces the JSON and the Markdown. The same request on the same recorded state always yields the same packet_id. Historical requests use recorded versions only — never the retrieval index." }),
      LIVE ? form : el("div", { class: "note", text: "This is a static export: it cannot issue or record packets. Use the pre-issued packets below, or on the NUC: knowledge-lab memory context \"TASK\"." })))];
    out.push(packetView(S.packet));
    if (B.packets.length) out.push(el("section", { class: "panel" }, el("h2", {}, "Pre-issued packets in this export"), el("ul", { class: "rows" },
      B.packets.map(P => el("li", {}, el("button", { class: "row", type: "button", onclick: () => { S.packet = P; render(); }, }, el("span", { class: "title", text: P.packet.request.task }), el("span", { class: "mono faint", text: P.packet.packet_id })))))));
    if (B.receipts.length) out.push(el("section", { class: "panel" }, el("h2", {}, "Context receipts"), el("div", { class: "body scroll" },
      el("table", { class: "log" }, el("thead", {}, el("tr", {}, ["issued", "packet", "task", "cutoff", "consumer"].map(h => el("th", { scope: "col", text: h })))),
        el("tbody", {}, B.receipts.slice().reverse().map(r => el("tr", {}, el("td", { text: when(r.issued_at) }), el("td", { class: "mono", text: r.packet_id }), el("td", { text: r.task }), el("td", { class: "mono", text: short(r.cutoff_commit) }), el("td", { text: r.consumer || "—" }))))))));
    return out;
  }

  // ------------------------------------------------------------ INSPECTOR
  function inspector() {
    const box = el("aside", { class: "inspector" + (S.sel ? " open" : ""), id: "inspector", "aria-label": "Evidence inspector" });
    box.append(el("button", { class: "btn close", type: "button", onclick: closeInspector, text: "Close" }));
    if (!S.sel) { box.append(el("h2", { text: "Evidence inspector" }), el("p", { class: "muted", text: "Select a record, event or proposal to see its versions, declarations and pinned sources." })); return box; }
    const [kind, ...rest] = S.sel.split(":"); const id = rest.join(":");
    if (kind === "record") inspectRecord(box, id);
    else if (kind === "event") inspectEvent(box, id);
    else if (kind === "proposal") inspectProposal(box, id);
    return box;
  }
  function inspectRecord(box, rid) {
    const f = S.tab === "graph" && S.follow ? rpFrame() : S.tab === "history" ? (S.known ? B.known_at_frames[S.known] : B.snapshot_frames[S.snap] || frameNow()) : frameNow();
    const e = f.records[rid];
    const evs = B.events.filter(x => x.subject === rid || (x.relation && (x.relation.from === rid || x.relation.to === rid)));
    const vids = []; evs.forEach(x => [x.before, x.after].forEach(v => v && B.versions[v] && !vids.includes(v) && vids.push(v)));
    const v = e ? V(e[0]) : (vids.length ? V(vids[vids.length - 1]) : null);
    if (!v) { box.append(el("h2", { text: rid }), el("p", { class: "muted", text: "No recorded version." })); return; }
    box.append(el("h2", { text: v.title || rid }), el("div", {}, chip(v.type), " ", chip(v.status), e ? (e[1] !== "current" ? chip("unavailable", "source unavailable") : null) : chip("historical", "not selected at this point")),
      el("dl", { class: "kv" },
        el("dt", { text: "Record" }), el("dd", { class: "mono", text: v.logical_id }),
        el("dt", { text: "Version" }), el("dd", { class: "mono", text: v.version_id }),
        el("dt", { text: "Source" }), el("dd", {}, el("span", { class: "mono", text: v.path + (v.section ? " § " + v.section : "") }), " ", link(v.url, "open at commit")),
        el("dt", { text: "Blob" }), el("dd", { class: "mono", text: v.blob || "—" }),
        el("dt", { text: "Basis" }), el("dd", { text: v.basis.kind === "source_declared" ? "declared by the source" : "manifest classification (not a source declaration)" })));
    if (v.note) box.append(el("div", { class: "note", text: v.note }));
    for (const d of v.basis.declarations || []) box.append(el("div", { class: "note" + (d.found ? "" : " warn") }, el("div", { class: "faint", text: `${d.path}${d.line ? ":" + d.line : ""} · ${d.found ? "quote found at this commit" : "quote not found"}` }), el("q", { text: d.quote }), " ", d.url ? link(d.url, "line") : null));
    if (v.excerpt) box.append(el("h3", { class: "faint", text: "Source text (as recorded, untrusted)" }), el("pre", { class: "src", text: v.excerpt + (v.excerpt_truncated ? " …" : "") }));
    box.append(el("h3", { class: "faint", text: `Versions (${vids.length})` }), el("ul", { class: "rows" }, vids.map(id => el("li", {}, el("div", { class: "row" }, el("span", { class: "mono", text: id }), chip(V(id).status), el("span", { class: "faint mono", text: short(V(id).blob) }))))));
    box.append(el("h3", { class: "faint", text: `History (${evs.length} events)` }), el("ul", { class: "rows" }, evs.map(x => el("li", {}, rowBtn("event", x.event_id, [el("span", { class: "mono faint", text: "#" + x.seq }), el("span", { class: "title", text: x.type + (x.relation ? ` · ${x.relation.from} ${x.relation.rel} ${x.relation.to}` : "") }), el("span", { class: "faint", text: when(x.source_time) })])))));
    const props = B.now ? Object.entries(B.now.proposals).filter(([, p]) => (p.proposal.evidence || []).some(x => x.record === rid)) : [];
    if (props.length) box.append(el("h3", { class: "faint", text: "Proposals citing it" }), el("ul", { class: "rows" }, props.map(([pid, p]) => el("li", {}, rowBtn("proposal", pid, [el("span", { class: "title", text: p.proposal.title }), chip(p.status.state)])))));
  }
  function inspectEvent(box, eid) {
    const e = B.events.find(x => x.event_id === eid);
    if (!e) { box.append(el("h2", { text: "Unknown event" })); return; }
    const i = B.replay.findIndex(r => r.seq === e.seq);
    box.append(el("h2", { text: `${e.type} · #${e.seq}` }), el("dl", { class: "kv" },
      ...[["Subject", e.relation ? `${e.relation.from} ${e.relation.rel} ${e.relation.to}` : e.subject], ["Event id", e.event_id], ["Commit", e.commit], ["Snapshot", e.snapshot_id], ["Source time", when(e.source_time)],
        ["Recorded at", when(e.recorded_at)], ["Valid from/to", `${e.valid_from || "unknown"} / ${e.valid_to || "unknown"}`], ["Before", e.before || "—"], ["After", e.after || "—"],
        ["Actor", e.actor ? `${e.actor.name} (${e.actor.kind})` : "—"], ["Producer", e.producer]].flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { class: "mono", text: String(v ?? "—") })])));
    box.append(el("div", { class: "note" + (e.reason ? "" : " warn"), text: e.reason ? "Reason declared by the source:" : "No declared reason. A diff says what changed, not why." }));
    for (const d of (e.reason && e.reason.declarations) || []) box.append(el("div", { class: "note" }, el("q", { text: d.quote }), " ", el("span", { class: "faint", text: d.path })));
    if (e.note) box.append(el("div", { class: "note", text: e.note }));
    for (const ev of e.evidence || []) if (ev.path) box.append(el("div", { class: "faint mono", text: `${ev.path} @ ${short(ev.blob || ev.commit)}` }));
    if (e.subject && B.layout.nodes[e.subject]) box.append(el("button", { class: "btn", type: "button", onclick: () => select("record", e.subject), text: "Inspect record" }));
    if (i >= 0) box.append(" ", el("button", { class: "btn", type: "button", onclick: () => { S.rp = i; S.follow = true; go("graph"); }, text: "Show on atlas" }));
  }
  function inspectProposal(box, pid) {
    const P = B.now && B.now.proposals[pid];
    if (!P) { box.append(el("h2", { text: pid })); return; }
    const p = P.proposal, s = P.status;
    box.append(el("h2", { text: p.title }), el("div", {}, chip(p.kind), " ", chip(s.state)),
      el("p", { text: p.statement }),
      el("dl", { class: "kv" },
        el("dt", { text: "Author" }), el("dd", { text: `${p.author.name} (${p.author.kind}${p.author.via ? ", via " + p.author.via : ""})` }),
        el("dt", { text: "Submitted" }), el("dd", { text: when(p.submitted_at) }),
        el("dt", { text: "Base" }), el("dd", { class: "mono", text: `${short(p.base.commit)}${p.base.context_packet_id ? " · " + p.base.context_packet_id : ""}` }),
        el("dt", { text: "Change" }), el("dd", { class: "mono", text: JSON.stringify(p.proposed_change || { op: "none" }) }),
        el("dt", { text: "File" }), el("dd", { class: "mono", text: `${p.path} @ ${short(p.blob)}` })),
      s.review ? el("div", { class: "note" }, `Reviewed: ${s.review.outcome} by ${s.review.reviewer.name} · ${s.review.basis.kind}: ${s.review.basis.ref} · ${when(s.review.reviewed_at)}`) :
        el("div", { class: "note warn", text: "Not reviewed. It travels in context labelled unreviewed and changes nothing until a human review record accepts it." }),
      s.stale_evidence.length ? el("div", { class: "note warn", text: "Base is stale: " + s.stale_evidence.map(x => `${x.record} cited ${x.cited || "?"}, now ${x.current || "not selected"}`).join("; ") }) : null,
      s.accepted && s.change_applied_in_source === false ? el("div", { class: "note warn", text: "Accepted, but the proposed status change is not yet in the source. The source still declares the old status." }) : null,
      el("h3", { class: "faint", text: "Conditions" }), el("ul", {}, (p.conditions || []).map(c => el("li", { text: c }))),
      el("h3", { class: "faint", text: "Evidence" }), el("ul", { class: "rows" }, (p.evidence || []).map(x => el("li", {}, x.record && B.layout.nodes[x.record] ?
        rowBtn("record", x.record, [el("span", { class: "title", text: x.record }), el("span", { class: "faint mono", text: x.version_id || x.path || "" })]) :
        el("div", { class: "row" }, el("span", { class: "mono", text: x.path || x.record }), x.quote ? el("q", { text: x.quote }) : null)))));
  }

  // ------------------------------------------------------------ frame
  function render() {
    const scrollY = window.scrollY;
    const active = document.activeElement && document.activeElement.getAttribute("aria-label");
    root.replaceChildren(
      el("a", { class: "skip", href: "#main", text: "Skip to content" }),
      header(), tabs(),
      el("div", { class: "shell" },
        el("main", { id: "main", tabindex: "-1" }, ({ now: viewNow, history: viewHistory, graph: viewGraph, context: viewContext })[S.tab]()),
        inspector()),
      el("footer", { class: "foot", text: `Observstory observes; it does not decide or dispatch. Bundle ${B.schema} · generated ${when(B.generated_at)} · ${B.events.length} recorded events.` }));
    window.scrollTo(0, scrollY);
    if (active && (active.startsWith("Replay") || active.startsWith("Previous") || active.startsWith("Next"))) { const t = root.querySelector(`[aria-label="${active}"]`); if (t) t.focus(); }
  }
  async function refresh() {
    try { const r = await fetch(API + "bundle"); if (r.ok) { B = await r.json(); S.rp = null; render(); } } catch (e) { /* keep showing loaded data */ }
  }
  document.addEventListener("keydown", e => { if (e.key === "Escape" && S.sel) closeInspector(); });
  window.addEventListener("hashchange", () => { readHash(); render(); });
  reduceMotion.addEventListener && reduceMotion.addEventListener("change", render);
  readHash(); render();
})();
