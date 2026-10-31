/* Observatory pixel-design study — interactive page.
 *
 * One working interface, three pixel treatments (A courtyard, B instrument,
 * C atlas) over identical synthetic data. Everything readable is HTML/SVG
 * text; pixel art only frames it. All source strings go through textContent.
 *
 * URL hash carries the full state so screenshots are reproducible:
 *   #study=a|b|c&state=quiet|overlap|replay&view=map|list&sel=<id>&pos=<n>&theme=night|paper&motion=on|off
 */
(function () {
  "use strict";
  const P = window.ObsPixels;
  const D = window.ObsData;

  const STUDIES = {
    a: { key: "a", name: "Courtyard", long: "A · Observatory courtyard" },
    b: { key: "b", name: "Instrument", long: "B · Telescope instrument" },
    c: { key: "c", name: "Atlas", long: "C · Star atlas" },
    d: { key: "d", name: "Living", long: "D · Living observatory" },
  };
  const ZONE_CODE = { intent: "INT", build: "BLD", verify: "VER", ship: "SHP" };
  const CONF = { high: "●", medium: "◐", low: "○" };

  const S = {
    study: "d", state: "overlap", view: "map", sel: null, pos: 11,
    theme: "night", motion: true, playing: false, speed: 1, lastView: "map",
  };
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let angleNow = P.PARKED, angleTimer = null, playTimer = null, twinkle = 0, twinkleTimer = null;
  let lastTrigger = null;

  /* ── tiny DOM helper (text only, never innerHTML for data) ── */
  function h(tag, attrs, ...kids) {
    const ns = attrs && attrs.ns;
    const e = ns ? document.createElementNS(ns, tag) : document.createElement(tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) {
      if (k === "ns" || v == null || v === false) continue;
      if (k === "on") for (const [ev, fn] of Object.entries(v)) e.addEventListener(ev, fn);
      else if (k === "class") e.setAttribute("class", v);
      else e.setAttribute(k, v === true ? "" : v);
    }
    for (const k of kids.flat(3)) {
      if (k == null || k === false) continue;
      e.append(k instanceof Node ? k : document.createTextNode(String(k)));
    }
    return e;
  }
  const SVGNS = "http://www.w3.org/2000/svg";
  const s = (tag, attrs, ...kids) => h(tag, Object.assign({ ns: SVGNS }, attrs), ...kids);

  /* ── hash state ── */
  function readHash() {
    const q = new URLSearchParams(location.hash.slice(1));
    if (STUDIES[q.get("study")]) S.study = q.get("study");
    if (["quiet", "overlap", "replay"].includes(q.get("state"))) S.state = q.get("state");
    if (["map", "list"].includes(q.get("view"))) S.view = q.get("view");
    S.sel = q.get("sel") || null;
    if (q.get("pos")) S.pos = Math.max(0, Math.min(D.EVENTS.length - 1, +q.get("pos") || 0));
    if (q.get("theme") === "paper") S.theme = "paper";
    if (q.get("motion") === "off") S.motion = false;
  }
  function writeHash() {
    const q = new URLSearchParams({ study: S.study, state: S.state, view: S.view });
    if (S.sel) q.set("sel", S.sel);
    if (S.state === "replay") q.set("pos", S.pos);
    if (S.theme !== "night") q.set("theme", S.theme);
    if (!S.motion) q.set("motion", "off");
    history.replaceState(null, "", "#" + q.toString());
  }
  const motionOn = () => S.motion && !reducedMotion.matches;

  /* ── data access ── */
  const snap = () => D.STATES[S.state] || D.STATES.overlap;
  const groupById = (id) => D.GROUPS.find((g) => g.id === id);
  const zoneOfGroup = (id) => (groupById(id) || {}).zone;
  function nodeById(id) { return snap().nodes.find((n) => n.id === id); }
  function edgeById(id) { return snap().edges.find((e) => e.id === id); }
  function edgesOf(nodeId) { return snap().edges.filter((e) => e.from === nodeId || e.to === nodeId); }
  function relatedIds() {
    if (!S.sel) return null;
    const ids = new Set([S.sel]);
    const e = edgeById(S.sel);
    if (e) { ids.add(e.from); ids.add(e.to); }
    if (nodeById(S.sel)) edgesOf(S.sel).forEach((x) => { ids.add(x.from); ids.add(x.to); ids.add(x.id); });
    if (S.sel.startsWith("area:")) snap().nodes.filter((n) => n.group === S.sel).forEach((n) => ids.add(n.id));
    return ids;
  }
  function coord(n) {
    const g = groupById(n.group);
    const inZone = D.GROUPS.filter((x) => x.zone === g.zone);
    const gi = inZone.indexOf(g) + 1;
    const ni = snap().nodes.filter((x) => x.group === n.group).indexOf(n) + 1;
    return `${ZONE_CODE[g.zone]} ${gi}·${ni}`;
  }
  function age(hrs) {
    if (hrs < 1) return Math.round(hrs * 60) + "m";
    if (hrs < 48) return Math.round(hrs) + "h";
    return Math.floor(hrs / 24) + "d";
  }
  const STATUS_WORD = { in_flight: "in flight", draft: "draft", stale: "stale", landed: "landed" };

  /* Telescope target: lane of the selection, or of the replay event. Never activity. */
  function target() {
    if (S.state === "replay") {
      const ev = D.EVENTS[S.pos];
      const g = D.GROUPS.find((x) => x.path === ev.area);
      return { angle: P.AZIMUTH[g.zone], open: true, why: `following replay event in ${laneLabel(g.zone)} · ${ev.area}` };
    }
    if (!S.sel) return { angle: P.PARKED, open: false, why: S.study === "d" ? "resting, lowered toward the horizon — nothing selected" : "parked — nothing selected" };
    let zone = null, what = "";
    if (S.sel.startsWith("area:")) { zone = zoneOfGroup(S.sel); what = groupById(S.sel).path; }
    const n = nodeById(S.sel);
    if (n) { zone = zoneOfGroup(n.group); what = groupById(n.group).path; }
    const e = edgeById(S.sel);
    if (e) { const a = nodeById(e.from); zone = zoneOfGroup(a.group); what = e.areas.join(", "); }
    if (!zone) return { angle: P.PARKED, open: false, why: "parked" };
    return { angle: P.AZIMUTH[zone], open: true, why: `pointing at ${laneLabel(zone)} · ${what}` };
  }
  const laneLabel = (z) => (D.ZONES.find((x) => x.id === z) || {}).label || z;
  function windowLit() {
    const d = S.study === "d";
    if (S.state === "replay") return { lit: false, why: d ? "lantern dark — coordination is not reconstructed from commit history" : "window unlit — coordination is not reconstructed from commit history" };
    const n = snap().attention.filter((a) => a.kind === "overlap" || a.kind === "waiting").length;
    if (d) return n
      ? { lit: true, why: `lantern lit — ${n} signal${n > 1 ? "s" : ""} suggest a conversation` }
      : { lit: false, why: S.sel ? "lantern dark — nothing needs a conversation" : "resting — nothing needs a conversation" };
    return n
      ? { lit: true, why: `window lit — ${n} signal${n > 1 ? "s" : ""} suggest a conversation` }
      : { lit: false, why: "window unlit — nothing needs a conversation" };
  }

  /* ── glyphs ── */
  function glyphSVG(status, opts = {}) {
    const rows = P.STAR_GLYPHS[status] || P.STAR_GLYPHS.in_flight;
    const col = opts.sel ? "var(--select)" : status === "stale" || status === "landed" || status === "draft" ? "var(--mark-dim)" : "var(--mark)";
    const ctr = opts.attn ? "var(--accent)" : col;
    const u = opts.u || 2;
    const g = s("svg", { class: "glyph", width: 5 * u, height: 5 * u, viewBox: "0 0 5 5", "shape-rendering": "crispEdges", "aria-hidden": "true" });
    rows.forEach((r, y) => [...r].forEach((ch, x) => {
      if (ch === "x" || ch === "X") g.append(s("rect", { x, y, width: 1, height: 1, fill: ch === "X" ? ctr : col }));
    }));
    return g;
  }
  function iconSVG(name, color, u = 1.5) {
    const rows = P.ICONS[name];
    const g = s("svg", { class: "glyph", width: 9 * u, height: 9 * u, viewBox: "0 0 9 9", "shape-rendering": "crispEdges", "aria-hidden": "true" });
    rows.forEach((r, y) => [...r].forEach((ch, x) => { if (ch === "x") g.append(s("rect", { x, y, width: 1, height: 1, fill: color })); }));
    return g;
  }

  /* ── selection ── */
  function select(id, trigger) {
    if (trigger) lastTrigger = trigger.getAttribute("data-key");
    S.sel = S.sel === id ? null : id;
    render();
  }
  function clearSelection() {
    if (!S.sel) return;
    S.sel = null;
    render();
    const back = lastTrigger && document.querySelector(`[data-key="${CSS.escape(lastTrigger)}"]`);
    if (back) back.focus();
  }

  /* ═════════════════ RENDER ═════════════════ */
  function render() {
    const focusKey = document.activeElement && document.activeElement.getAttribute && document.activeElement.getAttribute("data-key");
    document.documentElement.dataset.theme = S.theme;
    document.documentElement.dataset.direction = S.study;
    writeHash();
    renderStudyBar();
    const app = document.getElementById("app");
    app.dataset.study = S.study;
    app.dataset.state = S.state;
    renderTitle();
    renderSide();
    renderMain();
    renderRail();
    renderStatus();
    renderNotes();
    turnTelescope();
    if (focusKey) {
      const el = document.querySelector(`[data-key="${CSS.escape(focusKey)}"]`);
      if (el) el.focus({ preventScroll: true });
    }
  }

  function seg(label, key, opts, onPick) {
    return h("span", { class: "ctl" }, h("span", { class: "seg-label" }, label),
      h("span", { class: "seg", role: "group", "aria-label": label },
        opts.map(([v, text]) => h("button", {
          type: "button", "aria-pressed": String(S[key] === v), "data-key": `ctl:${key}:${v}`,
          on: { click: () => onPick(v) },
        }, text))));
  }

  function renderStudyBar() {
    const bar = document.getElementById("studybar");
    bar.replaceChildren(
      h("h1", null, "Observatory · pixel-design study"),
      seg("Direction", "study", [["d", "D Living"], ["a", "A Courtyard"], ["b", "B Instrument"], ["c", "C Atlas"]], (v) => { S.study = v; render(); }),
      seg("State", "state", [["quiet", "Quiet"], ["overlap", "Overlap"], ["replay", "Replay"]], (v) => setState(v)),
      seg("Theme", "theme", [["night", "Night"], ["paper", "Paper"]], (v) => { S.theme = v; render(); }),
      h("span", { class: "ctl" }, h("span", { class: "seg-label" }, "Motion"),
        h("span", { class: "seg" }, h("button", {
          type: "button", "aria-pressed": String(motionOn()), "data-key": "ctl:motion",
          title: reducedMotion.matches ? "Reduced motion is set by your system" : "Decorative motion",
          on: { click: () => { S.motion = !S.motion; render(); } },
        }, reducedMotion.matches ? "reduced (system)" : S.motion ? "on" : "off"))),
      h("span", { class: "notice" }, "⚠ " + D.PROJECT.notice),
    );
  }

  function setState(v) {
    stopPlay();
    if (v === "replay") { S.lastView = S.view; S.sel = null; }
    else if (S.state === "replay") S.view = S.lastView;
    if (S.sel && v !== S.state && !(D.STATES[v] || {}).nodes?.some((n) => n.id === S.sel)) S.sel = null;
    S.state = v;
    render();
  }

  function renderTitle() {
    const t = document.getElementById("titlebar");
    const icon = h("canvas", { class: "px", "aria-hidden": "true" });
    const b = new P.PixelBuffer(9, 9);
    P.glyph(b, 0, 0, P.ICONS.dome, "dome-hi");
    P.toCanvas(icon, b, 2, P.paletteFromCSS());
    let status;
    if (S.state === "replay") {
      status = h("span", { class: "status" }, h("b", null, "Replay"), " · repository file history · event ", h("b", null, `${S.pos + 1}/${D.EVENTS.length}`));
    } else {
      const st = snap(), ov = st.edges.filter((e) => e.type === "overlap").length, wt = st.edges.filter((e) => e.type === "waiting").length;
      const stale = st.nodes.filter((n) => n.status === "stale").length;
      status = h("span", { class: "status" },
        h("b", null, `${st.nodes.filter((n) => n.status !== "landed").length} work items`), " in flight or open · ",
        ov ? h("span", { class: "acc" }, `${ov} overlap`) : "0 overlaps", " · ",
        wt ? h("span", { class: "acc" }, `${wt} waiting`) : "0 waiting", " · ", `${stale} stale`,
        " · snapshot ", h("span", { class: "mono" }, st.collected));
    }
    t.replaceChildren(
      h("span", { class: "wordmark" }, icon, "Observatory"),
      h("span", { class: "repo mono" }, D.PROJECT.repository),
      status);
  }

  /* ── pixel scenes ── */
  function drawScenes(angle) {
    const pal = P.paletteFromCSS();
    const tgt = target(), win = windowLit();
    const scale = parseInt(getComputedStyle(document.documentElement).getPropertyValue("--px-scale"), 10) || 3;

    const hz = document.querySelector("#horizon canvas");
    if (hz) {
      const w = Math.max(40, Math.floor(hz.parentElement.clientWidth / scale));
      const b = new P.PixelBuffer(w, 12);
      P.sky(b, 31 + (motionOn() ? twinkle % 3 : 0), { horizon: 12, density: 0.03, solid: "sky-hi" });
      P.hills(b, 5, 13);
      P.toCanvas(hz, b, scale, pal);
    }

    const sc = document.querySelector("#courtyard canvas");
    if (sc) {
      const w = Math.max(60, Math.floor(sc.parentElement.clientWidth / scale));
      const H = window.innerWidth < 768 ? 46 : 66;
      const ground = H - 10;
      const b = new P.PixelBuffer(w, H);
      P.sky(b, 17, { horizon: ground - 6, density: 0.02, quiet: [{ x: 0, y: H - 12, w, h: 12 }] });
      P.hills(b, 3, ground - 2);
      b.rect(0, ground, w, H - ground, "hill-near");
      for (let x = 0; x < w; x += 4) b.set(x + (x % 8 ? 1 : 0), ground + 2, "stone-lo");
      P.tree(b, 6, ground);
      if (w > 70) P.tree(b, 15, ground + 1);
      P.observatory(b, w - 34, ground, { angle, open: tgt.open, lit: win.lit });
      P.toCanvas(sc, b, scale, pal);
      sc.parentElement.querySelector(".caption").textContent = `Telescope ${tgt.why}. ${cap(win.why)}.`;
    }

    const ins = document.querySelector("#instrument canvas");
    if (ins) {
      const w = 82, H = 70, cx = 41, groundY = 66;
      const b = new P.PixelBuffer(w, H);
      P.sky(b, 9, { horizon: H, density: 0.015, solid: "sky-hi", quiet: [{ x: 0, y: 0, w, h: 10 }] });
      b.rect(0, groundY + 1, w, H - groundY - 1, "hill-near");
      P.arc(b, cx, groundY - 20, 32, D.ZONES.map((z) => z.id));
      P.refractor(b, cx, groundY, { angle });
      P.toCanvas(ins, b, scale === 3 ? 3 : 2, pal);
      const box = ins.parentElement;
      box.querySelectorAll(".lane-tag").forEach((tag) => {
        const z = tag.dataset.zone, a = (P.AZIMUTH[z] * Math.PI) / 180;
        const px = cx + Math.sin(a) * 39, py = groundY - 20 - Math.cos(a) * 39;
        tag.style.left = (px / w) * 100 + "%";
        tag.style.top = (py / H) * 100 + "%";
        tag.classList.toggle("on", tgt.open && P.AZIMUTH[z] === tgt.angle);
      });
      box.parentElement.querySelector(".readout").textContent = tgt.open
        ? `AZ ${tgt.angle > 0 ? "+" : ""}${tgt.angle}° · ${tgt.why.replace(/^pointing at |^following replay event in /, "")}`
        : "AZ 0° · parked · nothing selected";
    }

    const cart = document.querySelector("#cartouche");
    if (cart) {
      const b = new P.PixelBuffer(44, 30);
      P.sky(b, 4, { horizon: 22, density: 0.03 });
      P.hills(b, 8, 26);
      b.rect(0, 26, 44, 4, "hill-near");
      P.observatory(b, 14, 26, { angle, open: tgt.open, lit: win.lit });
      P.toCanvas(cart, b, 2, pal);
    }

    const eye = document.querySelector("#eyepiece");
    if (eye) drawEyepiece(eye, pal);
  }
  const cap = (x) => x.charAt(0).toUpperCase() + x.slice(1);

  function turnTelescope() {
    const goal = P.quantize(target().angle);
    clearInterval(angleTimer);
    if (!motionOn() || goal === angleNow) { angleNow = goal; drawScenes(angleNow); return; }
    angleTimer = setInterval(() => {
      angleNow += Math.sign(goal - angleNow) * 5;
      drawScenes(angleNow);
      if (angleNow === goal) clearInterval(angleTimer);
    }, 70);
  }

  function drawEyepiece(box, pal) {
    const c = box.querySelector("canvas");
    const b = new P.PixelBuffer(56, 56);
    P.eyepiece(b, 13);
    box.querySelectorAll(".tag").forEach((t) => t.remove());
    const place = [];
    const n = nodeById(S.sel), e = edgeById(S.sel);
    if (n) {
      place.push({ node: n, x: 28, y: 28 });
      edgesOf(n.id).forEach((ed, i) => {
        const other = nodeById(ed.from === n.id ? ed.to : ed.from);
        const a = ((P.hash(other.id) % 360) * Math.PI) / 180 + i;
        place.push({ node: other, x: 28 + Math.round(Math.cos(a) * 15), y: 28 + Math.round(Math.sin(a) * 15), edge: ed });
      });
    } else if (e) {
      place.push({ node: nodeById(e.from), x: 20, y: 28 }, { node: nodeById(e.to), x: 36, y: 28 });
    } else if (S.sel && S.sel.startsWith("area:")) {
      snap().nodes.filter((x) => x.group === S.sel).forEach((x, i, arr) => {
        const a = (i / arr.length) * Math.PI * 2 - Math.PI / 2;
        place.push({ node: x, x: 28 + Math.round(Math.cos(a) * (arr.length > 1 ? 12 : 0)), y: 28 + Math.round(Math.sin(a) * (arr.length > 1 ? 12 : 0)) });
      });
    }
    place.forEach((p, i) => {
      const color = i === 0 && !e ? "select" : p.node.attention ? "accent" : "mark";
      P.glyph(b, p.x - 2, p.y - 2, P.STAR_GLYPHS[p.node.status], color, color);
      box.append(h("span", { class: "tag", style: `left:${((p.x + 0.5) / 56) * 100}%;top:${((p.y + 4) / 56) * 100}%` }, p.node.ref));
    });
    P.toCanvas(c, b, 3, pal);
  }

  /* ── sidebar ── */
  function renderSide() {
    const side = document.getElementById("side");
    const kids = [];
    if (S.study === "b") {
      kids.push(h("div", { id: "instrument", class: "instrument", "aria-hidden": "true" },
        h("div", { class: "stage" }, h("canvas", { class: "px" }),
          D.ZONES.map((z) => h("span", { class: "lane-tag", "data-zone": z.id }, z.label))),
        h("div", { class: "readout" })));
    }
    const views = [["map", "Map"], ["list", "List"], ["replay", "Replay"]];
    kids.push(h("div", { class: "side-section" },
      h("div", { class: "caps" }, "Views"),
      h("ul", { class: "navlist" }, views.map(([v, label]) => h("li", null, h("button", {
        type: "button", "data-key": `nav:${v}`,
        "aria-current": String(v === "replay" ? S.state === "replay" : S.state !== "replay" && S.view === v),
        on: { click: () => { if (v === "replay") setState("replay"); else { if (S.state === "replay") setState("overlap"); S.view = v; render(); } } },
      }, iconSVG(v === "replay" ? "plate" : v === "map" ? "dome" : "declared", "var(--ink-3)"), label))))));

    const lanes = h("div", { class: "side-section lanes-nav" }, h("div", { class: "caps" }, S.state === "replay" ? "Areas · files at this event" : "Lanes · areas"));
    const ul = h("ul", { class: "navlist" });
    const rp = S.state === "replay" ? D.replayAt(S.pos) : null;
    D.ZONES.forEach((z) => {
      const nodes = rp ? [] : snap().nodes.filter((n) => zoneOfGroup(n.group) === z.id);
      ul.append(h("li", null, h("div", { class: "caps", style: "padding:6px 6px 2px" }, z.label,
        rp ? "" : h("span", { class: "count", style: "float:right" }, nodes.length ? `${nodes.length} item${nodes.length > 1 ? "s" : ""}` : "quiet"))));
      D.GROUPS.filter((g) => g.zone === z.id).forEach((g) => {
        const cnt = rp ? `${rp.files[g.path]} files` : (snap().nodes.filter((n) => n.group === g.id).length || "");
        ul.append(h("li", { class: "sub" }, h("button", {
          type: "button", "data-key": `area:${g.id}`, "aria-current": String(S.sel === g.id),
          disabled: !!rp, on: { click: (ev) => select(g.id, ev.currentTarget) },
        }, g.path, h("span", { class: "count" }, cnt))));
      });
    });
    lanes.append(ul);
    kids.push(lanes);

    if (S.study === "a") {
      kids.push(h("div", { id: "courtyard", class: "scene" }, h("canvas", { class: "px", "aria-hidden": "true" }), h("div", { class: "caption", "aria-live": "polite" })));
    }
    side.replaceChildren(...kids);

    const hz = document.getElementById("horizon");
    hz.replaceChildren(S.study === "a" ? h("canvas", { class: "px", "aria-hidden": "true" }) : "");
  }

  /* ── main pane ── */
  function renderMain() {
    const m = document.getElementById("main");
    const rel = relatedIds();
    m.classList.toggle("dimmed", !!rel);
    if (S.state === "replay") { m.replaceChildren(...replayPane()); return; }
    const head = h("div", { class: "pane-head" },
      h("h2", null, S.view === "list" ? "All work items" : { a: "Project map", b: "Recency field", c: "Atlas", d: "Sky" }[S.study]),
      h("span", { class: "faint" }, S.view === "list" ? "full equivalent of the map, keyboard ↑↓ Enter Esc" : { a: "lanes → areas → work items", b: "distance from the right edge = time since last activity", c: "stable sky regions per lane; stars are work items", d: "stars are work items · hover one to share its gaze" }[S.study]),
      legend());
    if (S.study === "d" && S.view === "map") {
      m.replaceChildren(head, living().node);
      living().update(livingModel(rel));
      return;
    }
    let body;
    if (S.view === "list") body = listView(rel);
    else if (S.study === "a") body = boardView(rel);
    else if (S.study === "b") body = fieldView(rel);
    else body = atlasView(rel, null);
    m.replaceChildren(head, body);
  }

  function legend() {
    return h("span", { class: "legend", "aria-hidden": "true" },
      h("span", null, glyphSVG("in_flight"), "in flight"),
      h("span", null, glyphSVG("draft"), "draft"),
      h("span", null, glyphSVG("stale"), "stale"),
      h("span", null, s("svg", { width: 22, height: 6 }, s("line", { x1: 0, y1: 3, x2: 22, y2: 3, stroke: "var(--accent)", "stroke-width": 1.5, "stroke-dasharray": "4 3" })), "overlap (derived)"),
      h("span", null, s("svg", { width: 22, height: 6 }, s("line", { x1: 0, y1: 3, x2: 18, y2: 3, stroke: "var(--wire)", "stroke-width": 1.3 }), s("path", { d: "M17 0 L22 3 L17 6 Z", fill: "var(--wire)" })), "waits on"));
  }

  function rowFor(n, rel, opts = {}) {
    const edges = edgesOf(n.id);
    const pills = edges.map((e) => {
      const other = nodeById(e.from === n.id ? e.to : e.from);
      if (e.type === "overlap") return h("span", { class: "pill overlap" }, `overlap · ${other.ref}`);
      return h("span", { class: "pill waiting" }, e.from === n.id ? `waits on ${other.ref}` : `${other.ref} waits on this`);
    });
    if (n.status === "stale") pills.push(h("span", { class: "pill stale" }, `idle ${age(n.age_hours)}${n.flags.includes("no_pull_request") ? " · no PR" : ""}`));
    const cls = ["row", n.status, rel && rel.has(n.id) ? "related" : ""].join(" ");
    const kids = opts.list
      ? [glyphSVG(n.status, { attn: n.attention, sel: S.sel === n.id }), h("span", { class: "ref" }, n.ref), h("span", { class: "area" }, groupById(n.group).path),
         h("span", { class: "label" }, n.label), h("span", { class: "pills" }, pills), h("span", { class: "age" }, age(n.age_hours))]
      : [glyphSVG(n.status, { attn: n.attention, sel: S.sel === n.id }), h("span", { class: "ref" }, n.ref), h("span", { class: "label" }, n.label), h("span", { class: "age" }, age(n.age_hours)),
         pills.length ? h("span", { class: "pills" }, pills) : null];
    return h("button", {
      type: "button", class: cls, "data-sel": "", "data-key": `${opts.list ? "lrow" : "row"}:${n.id}`,
      "aria-pressed": String(S.sel === n.id),
      "aria-label": `${n.ref} ${n.label}, ${STATUS_WORD[n.status]}, ${groupById(n.group).path}, last activity ${age(n.age_hours)} ago${edges.length ? ", " + edges.length + " relationship" + (edges.length > 1 ? "s" : "") : ""}`,
      on: { click: (ev) => select(n.id, ev.currentTarget) },
    }, kids);
  }

  function boardView(rel) {
    const st = snap();
    return h("div", { class: "board" }, D.ZONES.map((z) => {
      const groups = D.GROUPS.filter((g) => g.zone === z.id);
      const shown = groups.filter((g) => st.nodes.some((n) => n.group === g.id || n.also_touches.includes(g.id)));
      const lane = h("div", { class: "lane" + (shown.length ? "" : " quiet") },
        h("div", { class: "lane-head" }, h("div", { class: "caps" }, z.label), h("div", { class: "desc" }, z.description)));
      if (!shown.length) lane.append(h("p", { class: "faint", style: "font-size:12px;margin:4px 0" }, "Nothing in flight."));
      shown.forEach((g) => {
        const nodes = st.nodes.filter((n) => n.group === g.id);
        const also = st.nodes.filter((n) => n.also_touches.includes(g.id));
        const attn = nodes.some((n) => n.attention) && st.edges.some((e) => e.type === "overlap" && e.areas.includes(g.path));
        lane.append(h("div", { class: "group" + (attn ? " attn" : "") },
          h("div", { class: "group-head" }, h("span", null, g.path), h("span", null, attn ? iconSVG("overlap", "var(--accent)") : "")),
          nodes.map((n) => rowFor(n, rel)),
          also.length ? h("div", { class: "also" }, "also changed by ", also.map((n) => n.ref).join(", ")) : null));
      });
      return lane;
    }));
  }

  function listView(rel) {
    const st = snap();
    return h("div", { class: "list" }, D.ZONES.map((z) => {
      const nodes = st.nodes.filter((n) => zoneOfGroup(n.group) === z.id);
      return h("div", { class: "list-group" },
        h("h3", { class: "caps" }, `${z.label} · ${nodes.length ? nodes.length + " item" + (nodes.length > 1 ? "s" : "") : "quiet"}`),
        nodes.length ? nodes.map((n) => {
          const r = rowFor(n, rel, { list: true });
          if (S.study === "b") r.querySelector(".ref").before(h("span", { class: "coord" }, coord(n)));
          else r.querySelector(".ref").before(h("span", { class: "coord" }, ""));
          return r;
        }) : h("p", { class: "faint", style: "margin:0;padding:0 16px 8px;font-size:12px" }, "Nothing in flight."));
    }));
  }

  /* Study B map: recency field. x = √(age/48h) from the right edge; rows = areas. */
  function fieldView(rel) {
    const st = snap();
    const W = 900, L = 150, R = 860;
    const rows = [];
    D.ZONES.forEach((z) => D.GROUPS.filter((g) => g.zone === z.id).forEach((g) => rows.push({ z, g })));
    const H = 40 + rows.length * 46 + 20;
    const xOf = (hrs) => R - Math.sqrt(Math.min(hrs, 48) / 48) * (R - L);
    const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, role: "group", "aria-label": "Recency field: work items by area and time since last activity" });
    // scale
    [0, 1, 3, 6, 12, 24, 48].forEach((t) => {
      const x = xOf(t);
      svg.append(s("line", { x1: x, y1: 28, x2: x, y2: H - 16, stroke: "var(--hair)", "stroke-width": 1 }),
        s("text", { x, y: 18, "text-anchor": "middle", fill: "var(--ink-3)", "font-size": 11, "font-family": "var(--font-mono)" }, t === 0 ? "now" : `${t}h`));
    });
    svg.append(s("text", { x: L - 8, y: 18, "text-anchor": "end", fill: "var(--ink-3)", "font-size": 11 }, "window edge →"));
    const pos = {};
    rows.forEach(({ z, g }, i) => {
      const y = 50 + i * 46;
      const first = i === 0 || rows[i - 1].z !== z;
      if (first) svg.append(s("text", { x: 4, y: y - 14, fill: "var(--ink-3)", "font-size": 10, "font-weight": 700, "letter-spacing": "0.08em" }, z.label.toUpperCase()));
      svg.append(s("line", { x1: L, y1: y, x2: R, y2: y, stroke: "var(--hair)", "stroke-dasharray": "1 5" }),
        s("text", { x: 14, y: y + 4, fill: "var(--ink-2)", "font-size": 11, "font-family": "var(--font-mono)" }, g.path));
      st.nodes.filter((n) => n.group === g.id).forEach((n, k) => { pos[n.id] = { x: n.age_hours > 48 ? L - 18 : xOf(n.age_hours), y, k, n }; });
    });
    st.edges.forEach((e) => {
      const a = pos[e.from], b = pos[e.to];
      if (!a || !b) return;
      const on = !rel || rel.has(e.id);
      const midY = Math.min(a.y, b.y) - 18 - Math.abs(a.y - b.y) * 0.2;
      const d = `M${a.x} ${a.y} Q${(a.x + b.x) / 2 + 30} ${midY} ${b.x} ${b.y}`;
      svg.append(s("path", {
        d, fill: "none", stroke: e.type === "overlap" ? "var(--accent)" : "var(--wire)", "stroke-width": e.type === "overlap" ? 1.6 : 1.3,
        "stroke-dasharray": e.type === "overlap" ? "5 3" : null, opacity: on ? 1 : 0.3, "marker-end": e.directed ? "url(#arrow)" : null,
      }));
    });
    svg.prepend(s("defs", null, s("marker", { id: "arrow", viewBox: "0 0 6 6", refX: 9, refY: 3, markerWidth: 6, markerHeight: 6, orient: "auto-start-reverse" }, s("path", { d: "M0 0 L6 3 L0 6 Z", fill: "var(--wire)" }))));
    Object.values(pos).forEach(({ x, y, k, n }) => {
      const g = s("g", {
        class: "fnode" + (S.sel === n.id ? " sel" : "") + (rel && rel.has(n.id) ? " related" : ""), tabindex: 0, role: "button", "data-sel": "", "data-key": `f:${n.id}`,
        "aria-pressed": String(S.sel === n.id), "aria-label": `${n.ref} ${n.label}, ${STATUS_WORD[n.status]}, ${age(n.age_hours)} ago`,
        transform: `translate(${x} ${y})`, opacity: n.status === "stale" || n.status === "draft" ? 0.62 : null,
        on: { click: (ev) => select(n.id, ev.currentTarget), keydown: (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(n.id, ev.currentTarget); } } },
      });
      g.append(s("rect", { class: "ring", x: -9, y: -9, width: 18, height: 18, fill: "var(--sky-0)", stroke: S.sel === n.id ? "var(--select)" : "transparent" }));
      const gl = glyphSVG(n.status, { attn: n.attention, sel: S.sel === n.id, u: 3 });
      gl.setAttribute("x", -7.5); gl.setAttribute("y", -7.5);
      g.append(gl);
      const up = k % 2 === 1, left = x > W * 0.62;
      g.append(s("text", { x: left ? -12 : 12, y: up ? -9 : 16, "text-anchor": left ? "end" : "start", class: "halo" }, `${n.ref} ${n.label.length > 26 ? n.label.slice(0, 25) + "…" : n.label}`));
      if (n.age_hours > 48) g.append(s("text", { x: -6, y: 20, "font-size": 10, fill: "var(--ink-3)" }, `${age(n.age_hours)} ←`));
      svg.append(g);
    });
    return h("div", { class: "field" }, svg);
  }

  /* Study C map: atlas. Stable regions per lane, clusters per area, stars per item. */
  function atlasLayout(st) {
    const W = 960, top = 54, bottom = 450, colW = 225, x0 = 30;
    const clusters = {};
    D.ZONES.forEach((z, zi) => {
      const gs = D.GROUPS.filter((g) => g.zone === z.id);
      gs.forEach((g, gi) => {
        const slotH = (bottom - top) / gs.length;
        const j = (P.hash(g.id) % 40) - 20;
        clusters[g.id] = { x: x0 + zi * colW + colW / 2 + j, y: top + slotH * (gi + 0.5) + 6, g, z };
      });
    });
    const stars = {};
    if (st) Object.values(clusters).forEach((c) => {
      const ns = st.nodes.filter((n) => n.group === c.g.id);
      const placed = [];
      ns.forEach((n) => {
        let a = (P.hash(n.id) % 12) * 30;
        let p;
        for (let tries = 0; tries < 12; tries++, a += 30) {
          const r = ns.length === 1 ? 0 : 24;
          p = { x: c.x + Math.cos((a * Math.PI) / 180) * r, y: c.y - 6 + Math.sin((a * Math.PI) / 180) * r * 0.7 };
          if (placed.every((q) => Math.hypot(q.x - p.x, q.y - p.y) > 26)) break;
        }
        placed.push(p);
        stars[n.id] = Object.assign(p, { n });
      });
    });
    return { W, H: 600, top, bottom, colW, x0, clusters, stars };
  }

  function atlasView(rel, replay) {
    const st = replay ? null : snap();
    const L = atlasLayout(st);
    const svg = s("svg", { viewBox: `0 0 ${L.W} ${L.H}`, role: "group", "aria-label": replay ? "Atlas: files per area at this replay event" : "Atlas: work items as stars grouped by area and lane" });
    svg.append(s("defs", null, s("marker", { id: "aarrow", viewBox: "0 0 6 6", refX: 10, refY: 3, markerWidth: 7, markerHeight: 7, orient: "auto" }, s("path", { d: "M0 0 L6 3 L0 6 Z", fill: "var(--wire)" }))));
    // decorative stars: margins and gutters only, never near clusters or labels
    const rnd = P.mulberry32(77);
    for (let i = 0; i < 160; i++) {
      const x = rnd() * L.W, y = rnd() * 470;
      if (Object.values(L.clusters).some((c) => Math.hypot(c.x - x, c.y - y) < 70) || y < 44) continue;
      svg.append(s("rect", { x: Math.round(x), y: Math.round(y), width: 1.5, height: 1.5, fill: "var(--decor)", opacity: rnd() > 0.8 ? 1 : 0.6, "aria-hidden": "true" }));
    }
    // graticule and lane regions
    for (let gx = L.x0; gx <= L.x0 + 4 * L.colW; gx += L.colW / 3) svg.append(s("line", { x1: gx, y1: L.top - 10, x2: gx, y2: L.bottom + 10, stroke: "var(--hair)", "stroke-width": 0.6, "stroke-dasharray": "1 6" }));
    for (let gy = L.top; gy <= L.bottom; gy += 66) svg.append(s("line", { x1: L.x0, y1: gy, x2: L.x0 + 4 * L.colW, y2: gy, stroke: "var(--hair)", "stroke-width": 0.6, "stroke-dasharray": "1 6" }));
    D.ZONES.forEach((z, zi) => {
      const x = L.x0 + zi * L.colW;
      svg.append(s("rect", { x: x + 0.5, y: L.top - 24, width: L.colW - 1, height: L.bottom - L.top + 36, fill: "none", stroke: "var(--hair-2)", "stroke-dasharray": "2 3" }),
        s("text", { x: x + L.colW / 2, y: L.top - 8, "text-anchor": "middle", fill: "var(--ink-3)", "font-size": 11, "font-weight": 700, "letter-spacing": "0.14em" }, z.label.toUpperCase()));
    });
    // clusters
    const rp = replay ? D.replayAt(S.pos) : null;
    Object.values(L.clusters).forEach((c) => {
      const cur = rp && rp.event.area === c.g.path;
      const active = st ? st.nodes.some((n) => n.group === c.g.id) : true;
      svg.append(s("g", { class: "cluster" },
        s("ellipse", { cx: c.x, cy: c.y - 6, rx: 52, ry: 40, fill: "none", stroke: cur ? "var(--select)" : "var(--hair-2)", "stroke-width": cur ? 1.5 : 0.8, "stroke-dasharray": cur ? null : "1 3" }),
        s("text", { x: c.x, y: c.y + 48, "text-anchor": "middle", fill: active ? "var(--ink-2)" : "var(--ink-3)", class: "halo" }, c.g.path),
        rp ? s("text", { x: c.x, y: c.y - 2, "text-anchor": "middle", fill: cur ? "var(--ink)" : "var(--ink-2)", "font-size": 13, "font-family": "var(--font-mono)" }, `${rp.files[c.g.path]} files`) : null,
        rp && cur ? s("text", { x: c.x, y: c.y + 14, "text-anchor": "middle", fill: "var(--select)", "font-size": 11, "font-family": "var(--font-mono)" }, `${rp.event.op} · ${rp.event.sha}`) : null,
        !active ? s("text", { x: c.x, y: c.y - 2, "text-anchor": "middle", fill: "var(--ink-3)", "font-size": 11 }, "quiet") : null));
    });
    if (st) {
      st.edges.forEach((e) => {
        const a = L.stars[e.from], b = L.stars[e.to];
        const on = !rel || rel.has(e.id);
        svg.append(s("line", {
          x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: e.type === "overlap" ? "var(--accent)" : "var(--wire)",
          "stroke-width": e.type === "overlap" ? 1.6 : 1.3, "stroke-dasharray": e.type === "overlap" ? "5 3" : null,
          "marker-end": e.directed ? "url(#aarrow)" : null, opacity: on ? 1 : 0.3,
        }));
        const len = Math.hypot(b.x - a.x, b.y - a.y), ox = -(b.y - a.y) / len * 12, oy = (b.x - a.x) / len * 12;
        if (st.edges.length <= 6 && len > 70) svg.append(s("text", { x: a.x + (b.x - a.x) * 0.35 + ox, y: a.y + (b.y - a.y) * 0.35 + oy + 4, "text-anchor": "middle", fill: e.type === "overlap" ? "var(--accent)" : "var(--wire)", "font-size": 10, class: "halo", opacity: on ? 1 : 0.4 }, e.type === "overlap" ? "overlap" : "waits on"));
      });
      Object.values(L.stars).forEach((p) => {
        const n = p.n;
        const g = s("g", {
          class: "astar" + (S.sel === n.id ? " sel" : "") + (rel && rel.has(n.id) ? " related" : ""), tabindex: 0, role: "button", "data-sel": "", "data-key": `a:${n.id}`,
          "aria-pressed": String(S.sel === n.id), "aria-label": `${n.ref} ${n.label}, ${STATUS_WORD[n.status]}, ${groupById(n.group).path}`,
          transform: `translate(${p.x} ${p.y})`, opacity: n.status === "stale" || n.status === "draft" ? 0.62 : null,
          on: { click: (ev) => select(n.id, ev.currentTarget), keydown: (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(n.id, ev.currentTarget); } } },
        });
        g.append(s("rect", { class: "ring", x: -11, y: -11, width: 22, height: 22, fill: "var(--sky-0)", stroke: "transparent" }));
        const gl = glyphSVG(n.status, { attn: n.attention, sel: S.sel === n.id, u: 3 });
        gl.setAttribute("x", -7.5); gl.setAttribute("y", -7.5);
        g.append(gl, s("text", { x: 12, y: 4, fill: S.sel === n.id ? "var(--ink)" : "var(--ink-2)", class: "halo", "font-weight": S.sel === n.id ? 700 : 400 }, n.ref));
        svg.append(g);
      });
    } else {
      svg.append(s("text", { x: L.x0, y: L.bottom + 34, fill: "var(--ink-3)", "font-size": 11 }, "Work items are not reconstructed from commit history; only files per area are plotted."));
    }
    // legend strip + cartouche area (reserved, nothing data-bearing overlaps it)
    svg.append(s("line", { x1: L.x0, y1: 488, x2: L.W - L.x0, y2: 488, stroke: "var(--hair-2)" }));
    const wrap = h("div", { class: "atlas", tabindex: 0, "aria-label": "Atlas chart (scrolls sideways on small screens)" }, svg);
    const st2 = snap();
    wrap.append(h("div", { class: "cartouche" },
      h("div", null,
        h("div", { style: "font-weight:600;color:var(--ink);letter-spacing:.06em;text-transform:uppercase;font-size:10px" }, "Atlas of Photo Frame Commons"),
        h("div", { class: "mono", style: "font-size:10px" }, replay ? `replay · ${D.EVENTS[S.pos].at.replace("T", " ")}` : `plate · ${st2.collected}`),
        h("div", { style: "font-size:10px;color:var(--ink-3)" }, "synthetic study data")),
      h("canvas", { id: "cartouche", class: "px", width: 88, height: 60, "aria-hidden": "true" })));
    return wrap;
  }

  /* ── D · living sky model (typed state → what the creature may reflect) ── */
  let livingInst = null;
  function living() { return livingInst || (livingInst = window.ObsLiving.create()); }
  let prevReplayPos = null;
  function livingModel(rel) {
    const replay = S.state === "replay";
    const st = snap();
    const win = windowLit();
    const ev = replay ? D.EVENTS[S.pos] : null;
    const model = {
      mode: replay ? "replay" : "snapshot",
      motion: motionOn(),
      loaded: true,
      lanes: D.ZONES, groups: D.GROUPS,
      stars: replay ? [] : st.nodes.map((n) => ({
        id: n.id, group: n.group, status: n.status, attn: !!n.attention, ref: n.ref, label: n.label, age: age(n.age_hours) + " ago",
        aria: `${n.ref} ${n.label}, ${STATUS_WORD[n.status]}, ${groupById(n.group).path}, last activity ${age(n.age_hours)} ago`,
      })),
      edges: replay ? [] : st.edges,
      related: rel,
      selId: S.sel,
      aimId: replay ? D.GROUPS.find((g) => g.path === ev.area).id : S.sel,
      mood: replay ? "replay" : win.lit || S.sel ? "attentive" : "rest",
      lantern: win.lit,
      note: !replay && st.commitments.length > 0,
      drift: replay ? S.pos * 3 : 0,
      lookText: {
        when: replay ? "this is a replay of saved commit history." : `${st.collected} (static snapshot).`,
        how: "A new look happens when the repository's GitHub Action runs. This page can't start it, and doesn't pretend to.",
      },
      replay: replay ? { pos: S.pos, event: ev, files: D.replayAt(S.pos).files, dots: D.replayDots(S.pos) } : null,
      onSelect: (id, el) => select(id, el),
    };
    prevReplayPos = replay ? S.pos : null;
    return model;
  }

  /* ── replay ── */
  function replayPane() {
    const rp = D.replayAt(S.pos);
    const ev = rp.event;
    const head = h("div", { class: "pane-head" }, h("h2", null, "Replay"), h("span", { class: "faint" }, "deterministic: the same position always yields the same state"));
    const feeds = h("div", { class: "feeds", role: "list", "aria-label": "Replay sources" }, D.FEEDS.map((f) =>
      h("div", { class: "feed" + (f.available ? "" : " off"), role: "listitem" },
        h("span", null, f.available ? iconSVG("plate", "var(--select)") : "–"),
        h("b", null, f.label, f.available ? " · selected" : " · unavailable"), h("span", { class: "d" }, f.detail))));
    const range = h("input", {
      type: "range", min: 0, max: D.EVENTS.length - 1, value: S.pos, "aria-label": "Replay position", "data-key": "rp:range",
      "aria-valuetext": `event ${S.pos + 1} of ${D.EVENTS.length}: ${ev.sha} ${ev.msg}`,
      on: { input: (e) => { S.pos = +e.target.value; render(); } },
    });
    const transport = h("div", { class: "transport" },
      h("button", { type: "button", "data-key": "rp:prev", "aria-label": "Previous event", on: { click: () => { S.pos = Math.max(0, S.pos - 1); render(); } } }, "◀"),
      h("button", { type: "button", "data-key": "rp:play", "aria-pressed": String(S.playing), on: { click: togglePlay } }, S.playing ? "Pause" : "Play"),
      h("button", { type: "button", "data-key": "rp:next", "aria-label": "Next event", on: { click: () => { S.pos = Math.min(D.EVENTS.length - 1, S.pos + 1); render(); } } }, "▶"),
      range,
      h("label", { class: "faint", style: "font-size:12px" }, "Speed ",
        h("select", { "data-key": "rp:speed", on: { change: (e) => { S.speed = +e.target.value; if (S.playing) { stopPlay(); togglePlay(); } } } },
          [1, 2, 4].map((v) => h("option", { value: v, selected: S.speed === v }, `${v}×`)))),
      h("span", { class: "mono faint" }, `${S.pos + 1} / ${D.EVENTS.length}`));
    const ticks = h("div", { class: "ticks", "aria-hidden": "true" }, D.EVENTS.map((e, i) =>
      h("i", { class: `${e.op}${i === S.pos ? " cur" : ""}`, style: `left:${(i / (D.EVENTS.length - 1)) * 100}%` })));
    const card = h("div", { class: "event-card", "aria-live": "polite" },
      h("div", { class: "meta" }, `${ev.sha} · ${ev.at.replace("T", " ")} · ${ev.op}`),
      h("div", null, ev.msg),
      h("div", { class: "mono muted" }, ev.path));
    let viz;
    if (S.study === "d") {
      const sky = living();
      queueMicrotask(() => sky.update(livingModel(null)));
      viz = null;
      return [head, sky.node, h("div", { class: "replay" }, feeds, transport, ticks, card,
        h("p", { class: "note" }, `Each commit arrives as a shooting star and leaves a point in its area; removals stay as hollow points. Baseline ${D.BASELINE.sha}. Pull-request, overlap and waiting state are not reconstructed from commit timestamps.`))];
    }
    if (S.study === "c") viz = atlasView(null, true);
    else {
      viz = h("table", { class: "areas" },
        h("thead", null, h("tr", null, h("th", null, "Lane"), h("th", null, "Area"), h("th", { style: "text-align:right" }, "Files"), h("th", { style: "text-align:right" }, "+ add"), h("th", { style: "text-align:right" }, "~ edit"), h("th", { style: "text-align:right" }, "− remove"))),
        h("tbody", null, D.GROUPS.map((g) => {
          const t = rp.touched[g.path] || { add: 0, edit: 0, remove: 0 };
          return h("tr", { class: ev.area === g.path ? "cur" : "" },
            h("td", { class: "caps" }, laneLabel(g.zone)), h("td", { class: "mono" }, g.path),
            h("td", { class: "n" }, rp.files[g.path]), h("td", { class: "n" }, t.add || "·"), h("td", { class: "n" }, t.edit || "·"), h("td", { class: "n" }, t.remove || "·"));
        })));
    }
    return [head, h("div", { class: "replay" }, feeds, transport, ticks, card, viz,
      h("p", { class: "note" }, `Baseline ${D.BASELINE.sha} (${D.BASELINE.label}). Counts include removals and corrections; nothing is interpolated between commits. Pull-request, overlap and waiting state are not reconstructed from commit timestamps.`))];
  }
  function togglePlay() {
    if (S.playing) { stopPlay(); render(); return; }
    S.playing = true;
    if (S.pos >= D.EVENTS.length - 1) S.pos = 0;
    playTimer = setInterval(() => {
      if (S.pos >= D.EVENTS.length - 1) { stopPlay(); render(); return; }
      S.pos++; render();
    }, 1200 / S.speed);
    render();
  }
  function stopPlay() { S.playing = false; clearInterval(playTimer); }

  /* ── rail ── */
  function renderRail() {
    const rail = document.getElementById("rail");
    const kids = [];
    const insp = inspector();
    if (insp) kids.push(insp);
    if (S.state === "replay") {
      kids.push(h("section", null, h("h2", { class: "caps" }, "Needs attention"),
        h("p", { class: "muted", style: "margin:0;font-size:12px" }, "Not shown during replay. Overlap, waiting and stale signals come from snapshots, and no past snapshots are stored.")));
      kids.push(h("section", null, h("h2", { class: "caps" }, "Source"),
        h("dl", { class: "kv" }, h("dt", null, "Feed"), h("dd", null, "Repository file history"),
          h("dt", null, "Baseline"), h("dd", { class: "mono" }, D.BASELINE.sha), h("dt", null, "Commits"), h("dd", null, `${D.EVENTS.length} first-parent`),
          h("dt", null, "Position"), h("dd", { class: "mono" }, D.EVENTS[S.pos].at.replace("T", " ")))));
    } else {
      const st = snap();
      const att = h("section", null, h("h2", { class: "caps" }, "Needs attention"));
      if (!st.attention.length) att.append(h("p", { class: "muted", style: "margin:0;font-size:12px" }, "Nothing here. No overlaps, waiting dependencies or stale work in this snapshot."));
      st.attention.forEach((a) => att.append(h("button", {
        type: "button", class: `attn-item ${a.kind}`, "data-key": `attn:${a.target}`, "aria-pressed": String(S.sel === a.target),
        on: { click: (ev) => select(a.target, ev.currentTarget) },
      }, iconSVG(a.kind === "overlap" ? "overlap" : a.kind === "waiting" ? "waiting" : "stale", a.kind === "overlap" ? "var(--accent)" : "var(--ink-3)", 1.33),
        h("span", null, h("span", { class: "lbl" }, a.label),
          h("span", { class: "rule" }, h("span", { class: "conf" }, CONF[a.confidence] + " "), `${a.basis} · ${a.confidence} confidence`)))));
      kids.push(att);
      if (st.commitments.length) kids.push(h("section", null, h("h2", { class: "caps" }, "Declared"),
        st.commitments.map((c) => h("div", { class: "declared-item" }, h("span", { class: "tag" }, "declared"), c.text,
          h("div", { class: "faint", style: "font-size:11px" }, `by ${c.declared_by} · ${c.note}`)))));
      kids.push(h("section", null, h("h2", { class: "caps" }, "Collection"),
        h("dl", { class: "kv" },
          h("dt", null, "Snapshot"), h("dd", { class: "mono" }, st.collected),
          h("dt", null, "Mode"), h("dd", null, "static file · not live"),
          h("dt", null, "Trigger"), h("dd", { class: "mono" }, st.trigger),
          h("dt", null, "Window"), h("dd", null, `${D.PROJECT.window_hours}h`),
          st.coverage.map(([k, v]) => [h("dt", null, k), h("dd", { class: v === "complete" ? "" : "skipped" }, v)])),
        st.degraded.length ? h("div", { class: "degraded" }, "Degraded: ", st.degraded.join("; "), ". Absent data is shown as skipped, not as zero.") : null));
    }
    rail.replaceChildren(...kids);
  }

  function appendAll(parent, ...kids) {
    for (const k of kids.flat(3)) if (k != null && k !== false) parent.append(k);
  }

  function inspector() {
    if (!S.sel || S.state === "replay") return null;
    const n = nodeById(S.sel), e = edgeById(S.sel), g = S.sel.startsWith("area:") ? groupById(S.sel) : null;
    if (!n && !e && !g) return null;
    const close = h("button", { type: "button", class: "close", "data-key": "insp:close", "aria-label": "Close inspector (Esc)", on: { click: clearSelection } }, "Esc");
    const sec = h("section", { class: "inspector open", role: "region", "aria-label": "Inspector" });
    if (S.study === "b") sec.append(h("div", { id: "eyepiece", class: "eyepiece", "aria-hidden": "true" }, h("canvas", { class: "px" })));
    const link = (id, text) => h("button", { type: "button", class: "pill", style: "cursor:pointer;background:none", "data-key": `insp:${id}`, on: { click: (ev) => select(id, ev.currentTarget) } }, text);
    if (n) {
      const grp = groupById(n.group);
      const rels = edgesOf(n.id);
      appendAll(sec,
        h("header", null, glyphSVG(n.status, { sel: true, u: 3 }), h("div", null, h("div", { class: "mono muted" }, `${n.ref} · ${n.kind.replace("_", " ")}`), h("h3", null, n.label)), close),
        h("div", { class: "basis" }, `observed · ${STATUS_WORD[n.status]} · last activity ${age(n.age_hours)} ago`),
        h("dl", { class: "kv" },
          h("dt", null, "Area"), h("dd", { class: "mono" }, `${grp.path} (${laneLabel(grp.zone)})`),
          n.also_touches.length ? [h("dt", null, "Also touches"), h("dd", { class: "mono" }, n.also_touches.map((a) => groupById(a).path).join(", "))] : null,
          S.study === "b" ? [h("dt", null, "Coordinate"), h("dd", { class: "mono" }, coord(n))] : null,
          h("dt", null, "Authors"), h("dd", null, [...n.actors].sort().join(", "))),
        h("div", { class: "caps", style: "margin-top:10px" }, "Relationships"),
        rels.length ? h("ul", { class: "ev" }, rels.map((x) => h("li", null, link(x.id, x.type === "overlap" ? "overlap" : "waits on"), " ", x.summary))) : h("p", { class: "faint", style: "margin:4px 0;font-size:12px" }, "None derived in this snapshot."),
        h("div", { class: "src" }, "Source: no URL in synthetic data. In the product this opens the pull request or branch on GitHub."));
    } else if (e) {
      appendAll(sec,
        h("header", null, iconSVG(e.type === "overlap" ? "overlap" : "waiting", e.type === "overlap" ? "var(--accent)" : "var(--wire)", 2), h("div", null, h("div", { class: "mono muted" }, e.type), h("h3", null, e.summary)), close),
        h("div", { class: "basis" }, `${CONF[e.confidence]} ${e.basis} · ${e.confidence} confidence${e.directed ? " · directed" : ""}`),
        h("div", { class: "caps" }, "Work items"),
        h("div", { style: "display:flex;gap:4px;margin:4px 0 8px" }, [e.from, e.to].map((id) => link(id, nodeById(id).ref))),
        e.files.length ? [h("div", { class: "caps" }, "Shared files"), h("ul", { class: "ev mono" }, e.files.map((f) => h("li", null, f)))] : null,
        e.quote ? [h("div", { class: "caps" }, "Evidence text"), h("blockquote", null, e.quote)] : null,
        h("div", { class: "rule" }, "rule: " + e.rule));
    } else {
      const ns = snap().nodes.filter((x) => x.group === g.id);
      appendAll(sec,
        h("header", null, h("div", null, h("div", { class: "mono muted" }, `area · ${laneLabel(g.zone)}`), h("h3", { class: "mono" }, g.path)), close),
        h("div", { class: "basis" }, `observed · ${ns.length} work item${ns.length === 1 ? "" : "s"} drawn here`),
        ns.length ? h("ul", { class: "ev" }, ns.map((x) => h("li", null, link(x.id, x.ref), " ", x.label))) : h("p", { class: "faint" }, "Nothing in flight."));
    }
    return sec;
  }

  function renderStatus() {
    const tgt = target(), win = windowLit();
    const st = snap();
    document.getElementById("statusbar").replaceChildren(
      h("span", null, h("i", { class: "dot" }), S.state === "replay" ? "Replay · repository file history" : `Static snapshot · ${st.collected} · not live`),
      h("span", null, h("i", { class: "dot" + (tgt.open ? " sel" : "") }), "Telescope ", tgt.why),
      h("span", { class: "hide-sm" }, h("i", { class: "dot" + (win.lit ? " on" : "") }), cap(win.why)),
      h("span", { class: "hide-sm", style: "margin-left:auto" }, STUDIES[S.study].long));
  }

  /* ── notes below the app: per-study rationale + shared mapping + asset sheet ── */
  const NOTES = {
    d: {
      idea: "The observatory is the creature: a caretaker, not a controller. It watches its sky (the project map), listens before it looks, inks a relation by hand once it has evidence for it, and rests without disappointment when nothing needs a conversation. The readable surfaces (list, rail, inspector) stay crisp HTML; the living scene is the map.",
      plus: ["Warmth and identity: you visit it, you don't operate it.", "Every habit maps to state or is declared decoration; text says the same thing.", "One scene does map, attention, selection and replay."],
      minus: ["Most build effort: sprite, habits, tracing, replay animation.", "Larger scene takes vertical space; list view must remain first-class.", "Risk of charm outrunning evidence; enforce the behaviour law in code review."],
    },
    a: {
      idea: "A place you return to. The courtyard sits in the sidebar's empty space; a thin horizon runs under the title bar. The working surface is the existing lane → area → item board, unchanged in meaning.",
      plus: ["Most legible: scenery never shares space with data.", "Warm window reads instantly as \"someone should talk\".", "Cheapest to build: one canvas, one strip."],
      minus: ["Scenery is mostly ambient; the telescope is small at 3×.", "Least distinctive map: close to today's Project Map."],
    },
    b: {
      idea: "The product is the instrument. A refractor on a pier tops the sidebar on a graduated azimuth arc (one long tick per lane). Selection turns it; the inspector opens with an eyepiece view of the selected item and its relationships. The map is a recency field: distance from the right edge is time since last activity.",
      plus: ["Strongest link between interaction and art (aim → inspect).", "Coordinates (BLD 2·1) give agents and people a shared short address.", "Recency field answers \"what moved\" faster than a board."],
      minus: ["More metaphor to learn; coordinates must be explained once.", "Eyepiece duplicates the inspector's facts (by design, never exclusive)."],
    },
    c: {
      idea: "The map is a chart. Lanes are sky regions with stable boundaries, areas are labelled clusters, work items are 5×5 star glyphs. Overlap is a dashed accent line, waiting a directed wire. The observatory shrinks to a cartouche, like the maker's mark on an old atlas.",
      plus: ["Most memorable and most \"observatory\".", "Stable placement: a star never moves because activity changed.", "Replay plots naturally onto the same chart."],
      minus: ["Spatial reading needs the list as equal partner on small screens.", "Highest risk of decoration creeping in; needs the decorative-star law enforced in code."],
    },
  };
  const MAPPING = [
    ["Lit window (accent)", "≥1 overlap or waiting signal in the loaded snapshot", "Status bar + Needs attention text", "Unlit in quiet and in replay (not reconstructed)"],
    ["Dome slit / telescope azimuth", "Lane of the current selection (stable per lane)", "Status bar: \"Telescope pointing at …\"", "Parked & shutter closed when nothing is selected"],
    ["Telescope during replay", "Lane of the current replay event", "Event card + area table", "Follows the scrubber; never animates on its own"],
    ["Star glyph shape", "Work-item status: cross = in flight, broken = draft, small = stale, ring = landed", "Status word in row and aria-label", "Works in greyscale"],
    ["Accent centre pixel", "Work item takes part in an attention signal", "Pills: \"overlap · #22\"", "Never brightness or size"],
    ["Dashed accent line", "Overlap (derived), undirected", "Legend + label when ≤6 connectors", "Confidence ●◐○ in text"],
    ["Solid wire + arrow", "Waits on (heuristic/declared), directed", "Legend + label", "Distinct from overlap in shape, not only colour"],
    ["1px dim star", "Nothing. Decoration only", "—", "Not focusable, not near labels or data"],
    ["Instrument motion", "Only when selection or replay position changes", "—", "No scanning animation: collection is never live here"],
  ];

  const MAPPING_D = [
    ["Eyes closed, settling, moth near the door", "Rest: no attention signal and nothing selected", "Status bar \"Resting — nothing needs a conversation\"", "Never sad or abandoned; no productivity cue"],
    ["Signal lantern under the telescope", "≥1 overlap or waiting signal", "Status bar + Needs attention", "Brightest colour in the scene, reserved"],
    ["Door lamp (amber)", "A snapshot is loaded (someone is home)", "Collection: snapshot time", "Dark only if nothing loaded"],
    ["Listen → look: door brightens, dome lifts, telescope turns, body leans", "Selection, hover/focus (shared gaze), or replay event", "Inspector / paper label / event card", "Turn hesitates once halfway; reduced motion: jump"],
    ["Hand-inked line", "An overlap (dashed signal) or waiting (thread + arrow) edge from the snapshot", "Legend, pills, inspector evidence", "Inked once when it first appears; never a guessed relation"],
    ["Shooting star → point in an area", "A commit in replay (repository file history)", "Event card, areas list", "Only in replay; removals stay as hollow points"],
    ["Sky drift", "Replay position (time passing)", "Position readout", "Decorative; stops with reduced motion"],
    ["Paper slip by the door", "A declared commitment exists", "Declared section", "Declared ≠ observed"],
    ["Chart peeking from the hatch, chimney puff, greeting", "Nothing (habit / one-time acknowledgement)", "—", "Never required to get anything done"],
    ["Telescope sweep (not shown)", "Reserved for a real, running collection", "—", "The static page cannot start one and says so"],
  ];

  function renderNotes() {
    const n = NOTES[S.study];
    const box = document.getElementById("notes");
    box.replaceChildren(
      h("div", { class: "card" }, h("h2", null, STUDIES[S.study].long), h("p", null, n.idea),
        h("table", null, h("tr", null, h("th", null, "Gains"), h("th", null, "Costs")),
          h("tr", null, h("td", null, h("ul", { style: "margin:0;padding-left:16px" }, n.plus.map((x) => h("li", null, x)))),
            h("td", null, h("ul", { style: "margin:0;padding-left:16px" }, n.minus.map((x) => h("li", null, x))))))),
      h("div", { class: "card", style: "grid-column: span 2" }, h("h2", null, S.study === "d" ? "Behaviour law — what each habit means" : "State → visual mapping (shared by A, B, C)"),
        h("table", null, h("tr", null, [S.study === "d" ? "Behaviour" : "Mark", "Means", "Also said in text", "Rule"].map((x) => h("th", null, x))),
          (S.study === "d" ? MAPPING_D : MAPPING).map((r) => h("tr", null, r.map((c) => h("td", null, c)))))),
      assetSheet());
  }

  function assetSheet() {
    const pal = P.paletteFromCSS();
    const fig = (label, w, hgt, draw, scale = 3) => {
      const c = h("canvas", { class: "px", "aria-hidden": "true" });
      const b = new P.PixelBuffer(w, hgt);
      draw(b);
      P.toCanvas(c, b, scale, pal);
      return h("figure", null, c, h("figcaption", null, label));
    };
    const obs = (o) => (b) => { b.rect(0, 30, b.w, 4, "hill-near"); P.observatory(b, 4, 30, o); };
    return h("div", { class: "card", style: "grid-column: 1 / -1" },
      h("h2", null, "Pixel sheet — editable source: src/creature.js, src/pixels.js · exported SVGs: assets/"),
      h("div", { class: "sheet" },
        ...[["resting", { eyes: "closed", angle: 70, door: 1 }], ["attentive · lantern", { eyes: "open", angle: 35, lantern: true, note: true }],
            ["listening · lift, lean", { eyes: "open", lift: 1, lean: -1, angle: 10, door: 2, look: -1 }], ["checking notes", { eyes: "half", chart: 4, angle: 50 }],
            ["greeting", { eyes: "wide", smoke: 3, angle: 60, look: 1 }]].map(([lbl, pose]) => fig("D · " + lbl, 58, 50, (b) => {
          window.ObsCreature.duskSky(b, 5, { horizon: 46, density: 0.01 }); window.ObsCreature.hill(b, 2, 0, 0, 46, 46);
          window.ObsCreature.creature(b, 6, 46, pose);
        }, 3)),
        fig("observatory · parked · unlit", 34, 34, obs({ open: false, lit: false })),
        fig("· Build (−18°) · lit", 34, 34, obs({ open: true, lit: true, angle: -18 })),
        fig("· Ship (+50°) · unlit", 34, 34, obs({ open: true, lit: false, angle: 50 })),
        fig("refractor · Intent −50°", 82, 62, (b) => { P.arc(b, 41, 38, 32, ["intent", "build", "verify", "ship"]); P.refractor(b, 41, 58, { angle: -50 }); }, 2),
        fig("refractor · Verify +18°", 82, 62, (b) => { P.arc(b, 41, 38, 32, ["intent", "build", "verify", "ship"]); P.refractor(b, 41, 58, { angle: 18 }); }, 2),
        fig("eyepiece field", 56, 56, (b) => { P.eyepiece(b, 13); P.glyph(b, 26, 26, P.STAR_GLYPHS.in_flight, "select", "select"); }, 2),
        ...Object.keys(P.STAR_GLYPHS).map((k) => fig(`star · ${k}`, 7, 7, (b) => P.glyph(b, 1, 1, P.STAR_GLYPHS[k], "mark", k === "in_flight" ? "accent" : "mark"), 5)),
        ...Object.keys(P.ICONS).map((k) => fig(`icon · ${k}`, 11, 11, (b) => P.glyph(b, 1, 1, P.ICONS[k], "dome-hi"), 4))),
      h("div", { class: "caps", style: "margin:12px 0 6px" }, "Scenery palette (closed set)"),
      h("div", { class: "swatches" }, Object.keys(P.PALETTE).map((k) => h("span", null, h("i", { style: `background:${pal[k] || P.PALETTE[k]}` }), k))));
  }

  /* ── keyboard ── */
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") { clearSelection(); return; }
    const main = document.getElementById("main");
    if ((ev.key === "ArrowDown" || ev.key === "ArrowUp") && main.contains(document.activeElement)) {
      const items = [...main.querySelectorAll("[data-sel]")];
      const i = items.indexOf(document.activeElement);
      if (i < 0) return;
      ev.preventDefault();
      const nxt = items[Math.max(0, Math.min(items.length - 1, i + (ev.key === "ArrowDown" ? 1 : -1)))];
      nxt.focus();
    }
  });

  window.addEventListener("hashchange", () => { readHash(); render(); });
  window.addEventListener("resize", () => drawScenes(angleNow));
  reducedMotion.addEventListener("change", render);
  twinkleTimer = setInterval(() => { if (motionOn() && S.study === "a") { twinkle++; drawScenes(angleNow); } }, 1800);

  readHash();
  angleNow = P.quantize(target().angle);
  render();
})();
