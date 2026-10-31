/* Direction D — living sky engine.
 *
 * The observatory watches its sky (the project map) and keeps a few habits:
 *   listens before it looks — door brightens, dome lifts, then the telescope turns;
 *   has weight              — the body leans against a turn, hesitates halfway, settles;
 *   draws by hand           — a relation (overlap / waiting) is inked once, then kept;
 *   is comfortable at rest  — eyes closed, one lamp lit, tends its chart, a moth visits.
 *
 * Law: habits are decoration and may stop at any time (reduced motion, Motion off);
 * every *state* they reflect is also stated in text by the page. The engine never
 * invents a relation: it only inks edges it is given, and only animates commits
 * during replay, where the event really is a commit.
 */
(function (root) {
  "use strict";
  const P = root.ObsPixels, C = root.ObsCreature;
  const SVGNS = "http://www.w3.org/2000/svg";

  function el(tag, attrs, ...kids) {
    const e = tag.startsWith("svg:") ? document.createElementNS(SVGNS, tag.slice(4)) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "on") for (const [ev, fn] of Object.entries(v)) e.addEventListener(ev, fn);
      else e.setAttribute(k, v === true ? "" : v);
    }
    for (const k of kids.flat(3)) if (k != null && k !== false) e.append(k instanceof Node ? k : document.createTextNode(String(k)));
    return e;
  }

  function create() {
    const node = el("div", { class: "living" });
    const scroller = el("div", { class: "living-scroll" });
    const stage = el("div", { class: "living-stage" });
    const bg = el("canvas", { class: "px", "aria-hidden": "true" });
    const actor = el("canvas", { class: "px actor", "aria-hidden": "true" });
    const fx = el("canvas", { class: "px fx", "aria-hidden": "true" });
    const svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("class", "living-data");
    const tags = el("div", { class: "living-tags" });
    const greet = el("button", { type: "button", class: "greet", "aria-label": "Greet the observatory (decorative)" });
    const bell = el("button", { type: "button", class: "bell", "data-key": "living:bell" });
    const note = el("div", { class: "living-note", role: "status", hidden: true });
    stage.append(bg, svg, actor, fx, tags, greet, bell, note);
    scroller.append(stage);
    node.append(scroller);

    let M = null;                  // last model
    let S = 3, W = 0, H = 0;       // scale and art size
    let bgBuf = null, layout = null, lastDrift = null, lastW = 0;
    let hover = null;              // {x,y} art point the viewer is looking at
    const traced = new Set();
    let timer = null;
    const REST_ANGLE = 70;            // resting: snout lowered toward the horizon
    const st = { t: 0, angle: REST_ANGLE, target: REST_ANGLE, seq: null, ack: 0, notes: 0, smoke: 0, chart: 0, cool: 0 };

    const motion = () => M && M.motion;
    const pal = () => P.paletteFromCSS();

    /* ── geometry ── */
    function measure() {
      // The living scene is one picture at one integer scale: 4× desktop, 3× small screens.
      S = window.innerWidth < 768 ? 3 : 4;
      const cw = Math.max(node.clientWidth || 900, 720);
      W = Math.floor(cw / S);
      H = S === 3 ? 172 : 150;
    }
    const G = () => H - 12;                      // creature ground line
    const CX = 6;                                // creature x

    function computeLayout() {
      const lanes = M.lanes, groups = M.groups;
      const x0 = 10, x1 = W - 8, top = 22, bottom = H - 54;
      const colW = (x1 - x0) / lanes.length;
      const clusters = {};
      lanes.forEach((z, zi) => {
        const gs = groups.filter((g) => g.zone === z.id);
        const slot = (bottom - top) / gs.length;
        gs.forEach((g, gi) => {
          const j = (P.hash(g.id) % 13) - 6;
          clusters[g.id] = { id: g.id, path: g.path, zone: z.id, x: Math.round(x0 + colW * (zi + 0.5) + j), y: Math.round(top + slot * (gi + 0.5)) };
        });
      });
      const stars = {};
      Object.values(clusters).forEach((c) => {
        const ns = M.stars.filter((s) => s.group === c.id);
        const placed = [];
        ns.forEach((s) => {
          let a = (P.hash(s.id) % 8) * 45, p;
          for (let k = 0; k < 8; k++, a += 45) {
            const r = ns.length === 1 ? 0 : 9;
            p = { x: Math.round(c.x + Math.cos((a * Math.PI) / 180) * r * 1.3), y: Math.round(c.y - 2 + Math.sin((a * Math.PI) / 180) * r * 0.8) };
            if (placed.every((q) => Math.hypot(q.x - p.x, q.y - p.y) > 9)) break;
          }
          placed.push(p);
          stars[s.id] = Object.assign({}, p, { s });
        });
      });
      return { x0, x1, top, bottom, colW, clusters, stars };
    }

    function dotPos(d) {
      const c = Object.values(layout.clusters).find((x) => x.path === d.area);
      const hsh = P.hash(d.key);
      const a = (hsh % 360) * Math.PI / 180, r = 4 + (hsh >> 9) % 9;
      return { x: Math.round(c.x + Math.cos(a) * r * 1.4), y: Math.round(c.y + Math.sin(a) * r * 0.8) };
    }

    function pointFor(id) {
      if (!id || !layout) return null;
      if (layout.stars[id]) return layout.stars[id];
      if (layout.clusters[id]) return layout.clusters[id];
      const e = M.edges.find((x) => x.id === id);
      if (e && layout.stars[e.from] && layout.stars[e.to]) {
        const a = layout.stars[e.from], b = layout.stars[e.to];
        return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
      }
      return null;
    }

    /* ── drawing ── */
    function drawBg() {
      const drift = M.drift || 0;
      if (bgBuf && lastDrift === drift && lastW === W) return;
      lastDrift = drift; lastW = W;
      bgBuf = new P.PixelBuffer(W, H);
      C.duskSky(bgBuf, 23, { horizon: H - 8, density: 0.007, drift,
        quiet: Object.values(layout.clusters).map((c) => ({ x: c.x - 22, y: c.y - 14, w: 44, h: 32 })) });
      C.hill(bgBuf, 4, 54, 96, G(), H - 5);
      P.toCanvas(bg, bgBuf, S, pal());
    }

    function pose() {
      const rest = M.mood === "rest";
      const p = {
        angle: st.angle, eyes: rest ? "closed" : "open", look: 0, lean: 0, settle: 0, lift: 0,
        door: M.loaded ? 1 : 0, lantern: !!M.lantern, note: !!M.note, chart: st.chart, smoke: st.smoke,
      };
      if (!motion()) { p.eyes = rest ? "half" : "open"; p.angle = st.target; return p; }
      const t = st.t;
      // breathing / settling
      if ((t % (rest ? 50 : 42)) < (rest ? 7 : 4)) p.settle = 1;
      // eyes
      if (rest) { if (t % 110 > 96) { p.eyes = "half"; p.look = -1; } }
      else if (t % 64 > 61) p.eyes = "closed";
      // listening sequence
      if (st.seq) {
        const k = t - st.seq.start;
        if (k < 6) p.door = 2;
        if (k >= 2) p.lift = 1;
        p.eyes = "open";
        p.look = Math.sign(st.target - st.angle) || st.seq.dir;
        if (st.angle !== st.target && k >= 4) p.lean = -Math.sign(st.target - st.angle);
      }
      if (st.notes > 0) { p.eyes = "half"; p.look = 0; p.chart = 4; }
      if (st.ack > 0) { p.eyes = "wide"; }
      return p;
    }

    function drawActor() {
      const ax = 0, ay = G() - 48, aw = 64, ah = 56;
      const buf = new P.PixelBuffer(aw, ah);
      for (let y = 0; y < ah; y++) for (let x = 0; x < aw; x++) buf.px[y * aw + x] = bgBuf.get(ax + x, ay + y);
      const p = pose();
      const out = C.creature(buf, CX - ax, G() - ay, p);
      if (motion() && M.mood === "rest") C.moth(buf, CX + 20 + Math.round(Math.sin(st.t / 4) * 5), G() - ay - 16 + Math.round(Math.cos(st.t / 3) * 2), st.t);
      P.toCanvas(actor, buf, S, pal());
      actor.style.left = ax * S + "px"; actor.style.top = ay * S + "px";
      st.pivot = { x: out.pivot.x + ax, y: out.pivot.y + ay };
      Object.assign(greet.style, { left: (CX + 7) * S + "px", top: (G() - 30) * S + "px", width: 32 * S + "px", height: 30 * S + "px" });
    }

    function retarget() {
      if (!st.pivot) st.pivot = { x: CX + 28, y: G() - 26 };
      const pt = hover || pointFor(M.aimId);
      const tgt = pt ? C.aimAt(st.pivot, pt) : REST_ANGLE;
      if (tgt !== st.target) {
        st.target = tgt;
        if (motion()) st.seq = { start: st.t, dir: Math.sign(tgt - st.angle), paused: false, half: (st.angle + tgt) / 2 };
        else st.angle = tgt;
      }
    }

    function tick() {
      if (!node.isConnected) return;
      st.t++;
      if (st.seq) {
        const k = st.t - st.seq.start;
        if (k >= 4 && st.angle !== st.target) {
          const crossing = !st.seq.paused && Math.abs(st.angle - st.seq.half) < 5;
          if (crossing) { st.seq.paused = true; st.seq.hold = 3; }
          if (st.seq.hold > 0) st.seq.hold--;
          else st.angle += 5 * Math.sign(st.target - st.angle);
          if (st.angle === st.target) st.seq.doneAt = st.t;
        }
        if (st.angle === st.target && st.seq.doneAt == null) st.seq.doneAt = st.t;
        if (st.seq.doneAt != null && st.t - st.seq.doneAt > 4) st.seq = null;
      }
      if (st.ack > 0) st.ack--;
      if (st.cool > 0) st.cool--;
      if (st.notes > 0) st.notes--;
      if (st.smoke > 0) st.smoke = st.smoke >= 6 ? 0 : st.smoke + 1;
      if (!st.notes) {
        const c = st.t % 170;
        st.chart = M.mood === "rest" && c > 150 ? Math.min(3, (c - 150) >> 1) - (c > 164 ? (c - 164) : 0) : 0;
        if (st.chart < 0) st.chart = 0;
      }
      drawActor();
    }

    function startLoop() {
      clearInterval(timer);
      if (motion()) timer = setInterval(tick, 100);
    }

    /* ── shooting star (replay only) ── */
    function shoot(to) {
      if (!motion()) return;
      const ctx = fx.getContext("2d");
      fx.width = W * S; fx.height = H * S;
      const pl = pal();
      const from = { x: to.x - 46, y: Math.max(2, to.y - 30) };
      const t0 = performance.now(), dur = 650;
      const trail = ["cream", "cream", "cream-dim", "cream-faint", "dusk-4"];
      (function frame(now) {
        const f = Math.min(1, (now - t0) / dur);
        ctx.clearRect(0, 0, fx.width, fx.height);
        if (f < 1) {
          trail.forEach((c, i) => {
            const g = Math.max(0, f - i * 0.035);
            const x = Math.round(from.x + (to.x - from.x) * g), y = Math.round(from.y + (to.y - from.y) * g);
            ctx.fillStyle = pl[c] || P.PALETTE[c];
            ctx.fillRect(x * S, y * S, S, S);
          });
          requestAnimationFrame(frame);
        }
      })(t0);
    }

    /* ── data layer ── */
    function drawData() {
      const s = S;
      svg.setAttribute("viewBox", `0 0 ${W * s} ${H * s}`);
      svg.setAttribute("width", W * s); svg.setAttribute("height", H * s);
      svg.replaceChildren();
      tags.replaceChildren();
      const add = (n) => { svg.append(n); return n; };
      const tag = (x, y, text, cls) => tags.append(el("span", { class: "ptag " + (cls || ""), style: `left:${x * s}px;top:${y * s}px` }, text));
      add(el("svg:defs", null, el("svg:marker", { id: "larrow", viewBox: "0 0 6 6", refX: 9, refY: 3, markerWidth: 6, markerHeight: 6, orient: "auto" }, el("svg:path", { d: "M0 0 L6 3 L0 6 Z", fill: "var(--l-thread)" }))));
      // lane names along the top, faint meridians between lanes
      M.lanes.forEach((z, i) => {
        const x = layout.x0 + layout.colW * (i + 0.5);
        add(el("svg:text", { x: x * s, y: 11 * s, "text-anchor": "middle", class: "lane-name" }, z.label.toUpperCase()));
        if (i) add(el("svg:line", { x1: (layout.x0 + layout.colW * i) * s, y1: 16 * s, x2: (layout.x0 + layout.colW * i) * s, y2: (layout.bottom + 8) * s, class: "meridian" }));
      });
      const rel = M.related;
      // clusters (hover target + paper tag)
      Object.values(layout.clusters).forEach((c) => {
        const has = M.mode === "replay" || M.stars.some((x) => x.group === c.id);
        const cur = M.replay && M.replay.event && c.path === M.replay.event.area;
        const g = add(el("svg:g", { class: "lcluster" + (cur ? " cur" : ""), on: {
          mouseenter: () => { hover = c; retarget(); }, mouseleave: () => { hover = null; retarget(); },
        } }));
        g.append(el("svg:ellipse", { cx: c.x * s, cy: (c.y - 1) * s, rx: 16 * s, ry: 11 * s, class: "halo-area" }));
        tag(c.x, c.y + 10, M.replay ? `${c.path} · ${M.replay.files[c.path]} files` : c.path, has ? "" : "quiet");
      });
      // replay dots: the lasting record each commit leaves
      if (M.replay) {
        M.replay.dots.forEach((d) => {
          const p = dotPos(d);
          add(el("svg:rect", { x: p.x * s, y: p.y * s, width: 2 * s, height: 2 * s, class: "fdot" + (d.removed ? " removed" : "") + (d.fresh && motion() ? " fresh" : "") }));
        });
      }
      // relations, inked by hand the first time they appear
      const ids = new Set(M.edges.map((e) => e.id));
      [...traced].forEach((id) => { if (!ids.has(id)) traced.delete(id); });
      M.edges.forEach((e) => {
        const a = layout.stars[e.from], b = layout.stars[e.to];
        if (!a || !b) return;
        const on = !rel || rel.has(e.id);
        const attrs = { x1: a.x * s, y1: a.y * s, x2: b.x * s, y2: b.y * s, class: `edge ${e.type}` + (on ? "" : " off"), "marker-end": e.directed ? "url(#larrow)" : null };
        const final = add(el("svg:line", attrs));
        if (!traced.has(e.id) && motion()) {
          final.classList.add("pending");
          const len = Math.hypot(b.x - a.x, b.y - a.y) * s;
          const ink = add(el("svg:line", { x1: a.x * s, y1: a.y * s, x2: b.x * s, y2: b.y * s, class: "ink", style: `stroke-dasharray:${len};stroke-dashoffset:${len}` }));
          st.chart = 3;
          setTimeout(() => { ink.remove(); final.classList.remove("pending"); }, 1300);
        }
        traced.add(e.id);
      });
      // stars: selectable, labelled
      Object.values(layout.stars).forEach((p) => {
        const x = p.s;
        const sel = M.selId === x.id;
        const g = add(el("svg:g", {
          class: "lstar " + x.status + (sel ? " sel" : "") + (rel && !rel.has(x.id) ? " dim" : ""), tabindex: 0, role: "button",
          "data-sel": "", "data-key": `l:${x.id}`, "aria-pressed": String(sel), "aria-label": x.aria,
          transform: `translate(${p.x * s} ${p.y * s})`,
          on: {
            click: (ev) => M.onSelect(x.id, ev.currentTarget),
            keydown: (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); M.onSelect(x.id, ev.currentTarget); } },
            mouseenter: () => { hover = p; retarget(); showLabel(p); }, mouseleave: () => { hover = null; retarget(); hideLabel(); },
            focus: () => { hover = p; retarget(); showLabel(p); }, blur: () => { hover = null; retarget(); hideLabel(); },
          },
        }));
        g.append(el("svg:rect", { class: "hit", x: -4 * s, y: -4 * s, width: 8 * s, height: 8 * s }));
        const rows = P.STAR_GLYPHS[x.status] || P.STAR_GLYPHS.in_flight;
        rows.forEach((r, yy) => [...r].forEach((ch, xx) => {
          if (ch === "x" || ch === "X") g.append(el("svg:rect", { x: (xx - 2) * s, y: (yy - 2) * s, width: s, height: s, class: ch === "X" && x.attn ? "core signal" : "core" }));
        }));
        if (sel) g.append(el("svg:rect", { class: "ring", x: -4 * s + 0.5, y: -4 * s + 0.5, width: 8 * s - 1, height: 8 * s - 1 }));
        g.append(el("svg:text", { x: 4 * s, y: -2 * s, class: "sref" }, x.ref));
      });
      const selP = layout.stars[M.selId];
      if (selP) showLabel(selP, true);
    }

    function bellIcon() {
      const g = el("svg:svg", { width: 11, height: 11, viewBox: "0 0 9 9", "shape-rendering": "crispEdges", "aria-hidden": "true" });
      P.ICONS.bell.forEach((r, y) => [...r].forEach((ch, x) => { if (ch === "x") g.append(el("svg:rect", { x, y, width: 1, height: 1, fill: "#8c4d33" })); }));
      return g;
    }

    let labelEl = null;
    function showLabel(p, sticky) {
      hideLabel(true);
      const x = p.s;
      labelEl = el("span", { class: "ptag big" + (sticky ? " sticky" : ""), style: `left:${p.x * S}px;top:${(p.y - 5) * S}px` },
        el("b", null, x.ref), " ", x.label, el("span", { class: "age" }, " · " + x.age));
      tags.append(labelEl);
    }
    function hideLabel(force) {
      if (labelEl && (force || !labelEl.classList.contains("sticky"))) { labelEl.remove(); labelEl = null; }
      if (!force && M && layout.stars[M.selId]) showLabel(layout.stars[M.selId], true);
    }

    /* ── interactions with the creature itself ── */
    greet.addEventListener("click", () => {
      if (st.cool > 0) return;
      st.ack = 8; st.smoke = 1; st.cool = 40;
      if (!motion()) drawActor();
    });
    bell.addEventListener("click", () => {
      note.hidden = false;
      note.replaceChildren(el("b", null, "Last look: "), M.lookText.when, el("br"), M.lookText.how,
        el("button", { type: "button", class: "note-close", "data-key": "living:note-close", on: { click: () => { note.hidden = true; bell.focus(); } } }, "OK"));
      st.notes = 25;
      clearTimeout(note._t); note._t = setTimeout(() => { note.hidden = true; }, 9000);
      if (!motion()) drawActor();
    });

    function update(model) {
      const prev = M;
      M = model;
      measure();
      layout = computeLayout();
      stage.style.width = W * S + "px"; stage.style.height = H * S + "px";
      drawBg();
      drawData();
      bell.replaceChildren(bellIcon(), "Ask for a new look");
      Object.assign(bell.style, { left: (CX + 48) * S + "px", top: (G() - 14) * S + "px" });
      Object.assign(note.style, { left: (CX + 48) * S + "px", top: (G() - 44) * S + "px" });
      if (!motion()) { st.angle = st.target; st.seq = null; }
      retarget();
      if (!motion()) st.angle = st.target;
      drawActor();
      if (M.replay && prev && prev.replay && M.replay.pos === prev.replay.pos + 1 && M.replay.event) {
        const fresh = M.replay.dots.find((d) => d.fresh);
        shoot(fresh ? dotPos(fresh) : layout.clusters[M.aimId] || { x: W / 2, y: 30 });
      }
      if (!prev || prev.motion !== M.motion) startLoop();
    }

    window.addEventListener("resize", () => { if (M) { lastW = 0; update(M); } });
    return { node, update };
  }

  root.ObsLiving = { create };
})(typeof window !== "undefined" ? window : globalThis);
