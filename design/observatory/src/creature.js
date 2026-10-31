/* Direction D — the living observatory. Editable pixel source.
 *
 * The observatory *is* the creature: a copper dome like an oversized shell,
 * a telescope like a curious snout, two attic windows that read as eyes only
 * through their light, a stone foundation folded into tucked paws, moss in the
 * seams, an amber side door where someone is always working.
 *
 * Every pose parameter maps either to project state or to a declared
 * decorative habit (see README → "D · behaviour law"). Nothing here decides
 * what a pose means; the engine (living.js) does, from typed state.
 *
 * Depends on ObsPixels (pixels.js). Adds the dusk palette to it.
 */
(function (root) {
  "use strict";
  const P = root.ObsPixels;

  Object.assign(P.PALETTE, {
    "dusk-0": "#191b38", "dusk-1": "#212448", "dusk-2": "#2c2b55", "dusk-3": "#3e3560", "dusk-4": "#56426a",
    "cream": "#f3e6c4", "cream-dim": "#8e88a6", "cream-faint": "#5d5880",
    "moss-0": "#1f3029", "moss-1": "#2b4434", "moss-2": "#3f6040", "moss-3": "#6b8c4c", "fern": "#557a45",
    "rock-0": "#2e2a3a", "rock-1": "#4d4759", "rock-2": "#6d6679", "rock-3": "#938a9c",
    "plaster": "#b3a8ae", "plaster-lo": "#857a8b",
    "copper-0": "#5e3227", "copper-1": "#8c4d33", "copper-2": "#b56b45", "copper-3": "#d99263",
    "patina": "#5b998b", "patina-hi": "#86bfac",
    "brass-0": "#7d6136", "brass-1": "#c39d58", "brass-2": "#e2c487",
    "lamp-dim": "#8f6c49", "lamp": "#f2cf8f", "lamp-hi": "#fff0c8",
    "ink": "#15121f", "paper": "#efe3c6", "signal": "#ff9550", "smoke": "#a7a1b6",
  });

  const W = 46, H = 44;               // sprite box (art px); ground at H-4
  const rad = (d) => (d * Math.PI) / 180;

  /* Dusk sky: indigo above, violet toward the horizon, narrow dither seams.
   * `drift` slides the decorative star field (history moves the sky). */
  function duskSky(buf, seed, opts = {}) {
    const bands = ["dusk-0", "dusk-1", "dusk-2", "dusk-3", "dusk-4"];
    const stops = opts.stops || [0, 0.34, 0.6, 0.8, 0.93];
    const bayer = [0, 2, 3, 1];
    const hzn = opts.horizon ?? buf.h;
    for (let y = 0; y < buf.h; y++) {
      const t = y / hzn;
      let i = 0;
      while (i < stops.length - 1 && t >= stops[i + 1]) i++;
      const next = Math.min(i + 1, bands.length - 1);
      const span = (stops[i + 1] ?? 1) - stops[i];
      const f = (t - stops[i]) / span;        // 0..1 inside band
      for (let x = 0; x < buf.w; x++) {
        const thr = (bayer[(x & 1) + 2 * (y & 1)] + 0.5) / 4;
        buf.set(x, y, f > 0.9 && (f - 0.9) / 0.1 > thr ? bands[next] : bands[i]);   // narrow seams only
      }
    }
    const rnd = P.mulberry32(seed);
    const n = Math.round(buf.w * hzn * (opts.density ?? 0.01));
    const drift = Math.round(opts.drift || 0);
    const quiet = opts.quiet || [];
    for (let k = 0; k < n; k++) {
      const x = ((Math.floor(rnd() * buf.w * 2) + drift) % buf.w + buf.w) % buf.w;
      const y = Math.floor(rnd() * hzn * 0.8);
      const b = rnd();
      if (quiet.some((q) => x >= q.x && x < q.x + q.w && y >= q.y && y < q.y + q.h)) continue;
      buf.set(x, y, b > 0.9 ? "cream-dim" : "cream-faint");
    }
  }

  /* A rounded grassy hill rising from the left, with tufts. */
  function hill(buf, seed, x0, x1, top, ground) {
    const rnd = P.mulberry32(seed);
    for (let x = 0; x < buf.w; x++) {
      let y;
      if (x < x0) y = top;
      else if (x < x1) { const f = (x - x0) / (x1 - x0); y = Math.round(top + (ground - top) * (0.5 - 0.5 * Math.cos(f * Math.PI))); }
      else y = ground;
      for (let j = y; j < buf.h; j++) buf.set(x, j, j === y ? "moss-2" : j - y < 3 ? "moss-1" : "moss-0");
      if (rnd() < 0.18) buf.set(x, y - 1, "moss-2");
      if (rnd() < 0.06) { buf.set(x, y - 1, "moss-3"); buf.set(x, y - 2, "moss-3"); }
    }
  }

  const FERN = ["..f..f", ".f.ff.", "f.ff..", ".ff.f.", "ff....", ".f...."];

  /* The creature. pose:
   *   angle    telescope azimuth, degrees from vertical (+ = right)
   *   eyes     "closed" | "half" | "open" | "wide"
   *   look     -1 | 0 | 1   pupils
   *   lean     -1 | 0 | 1   upper body shifts against a turn (weight)
   *   settle   0 | 1        breathing: upper body sinks one pixel
   *   lift     0 | 1        dome lifts (listening)
   *   door     0 | 1 | 2    side-door lamp: dim / working / bright
   *   lantern  bool         signal lantern under the telescope (attention)
   *   note     bool         paper slip pinned by the door (declared commitment)
   *   chart    0..4         star chart poking out of the hatch
   *   smoke    0..6         chimney puff frame
   */
  function creature(buf, x, g, pose = {}) {
    const p = Object.assign({ angle: 35, eyes: "open", look: 0, lean: 0, settle: 0, lift: 0, door: 1, lantern: false, note: false, chart: 0, smoke: 0 }, pose);
    const set = (a, b, c) => buf.set(a, b, c);

    // ── foundation (folded body) ──
    const fx0 = x + 7, fx1 = x + 38, ftop = g - 13;
    for (let j = 0; j < 13; j++) {
      const inset = j === 0 ? 2 : j === 1 ? 1 : 0;
      for (let i = fx0 + inset; i <= fx1 - inset; i++) {
        let c = "rock-2";
        if (i < fx0 + 3) c = "rock-3";
        if (i > fx1 - 7) c = "rock-1";
        if (j > 10) c = "rock-1";
        if (j % 4 === 3 && (i + (j % 8 === 3 ? 0 : 3)) % 7 !== 0) c = i > fx1 - 7 ? "rock-0" : "rock-1";
        set(i, ftop + j, c);
      }
    }
    // paws, tucked forward
    const paw = (px) => {
      for (let j = 0; j < 5; j++) for (let i = 0; i < 9; i++) {
        if (j === 0 && (i === 0 || i === 8)) continue;
        let c = j === 0 ? "rock-3" : j === 4 ? "rock-1" : "rock-2";
        if ((i === 3 || i === 6) && j >= 3) c = "rock-0";
        set(px + i, g - 5 + j, c);
      }
    };
    paw(x + 3); paw(x + 33);
    // moss along the seams
    const rnd = P.mulberry32(91);
    for (let i = fx0 + 2; i <= fx1 - 2; i++) {
      set(i, ftop, rnd() < 0.3 ? "moss-3" : "moss-2");
      if (rnd() < 0.25) set(i, ftop + 1, "moss-1");
      if (rnd() < 0.08) set(i, ftop + 2, "moss-1");
    }
    for (let i = 0; i < 9; i++) if (rnd() < 0.5) set(x + 3 + i, g - 5, "moss-2");
    for (let i = 0; i < 9; i++) if (rnd() < 0.4) set(x + 33 + i, g - 5, "moss-2");
    buf.grid(x + 1, g - 10, FERN, { f: "fern" });

    // side door, always a little lit: someone is working inside
    const dx = x + 15, dtop = g - 10;
    for (let j = 0; j < 9; j++) for (let i = 0; i < 6; i++) {
      if (j === 0 && (i === 0 || i === 5)) continue;
      const edge = i === 0 || i === 5 || j === 0;
      let c = edge ? "rock-0" : p.door === 0 ? "lamp-dim" : "lamp";
      if (!edge && p.door === 2 && i > 1 && i < 4 && j > 2) c = "lamp-hi";
      set(dx + i, dtop + j, c);
    }
    set(dx + 3, dtop + 5, "brass-1");
    if (p.door > 0) for (let k = 0; k < 4; k++) for (let i = -k; i < 6 + k; i++) if ((i + k) % 2 === 0 || k === 0) {
      if (buf.get(dx + i, g + k)) set(dx + i, g + k, k === 0 ? "moss-3" : "lamp-dim");
    }
    if (p.note) { buf.rect(x + 23, g - 9, 3, 4, "paper"); set(x + 24, g - 8, "ink"); set(x + 24, g - 9, "brass-1"); }

    // ── upper body: drum with eyes, chimney, hatch ──
    const ux = x + p.lean, uy = -p.settle;
    const D0 = x + 9 + p.lean, D1 = x + 35 + p.lean, dTop = ftop - 7 + uy;
    for (let j = 0; j < 7; j++) for (let i = D0; i <= D1; i++) {
      let c = i > D1 - 7 ? "plaster-lo" : "plaster";
      if (j === 0) c = "copper-1";
      if (j === 6) c = "plaster-lo";
      set(i, dTop + j, c);
    }
    // eyes: attic windows (6×5 with frame)
    const eye = (ex) => {
      for (let j = 0; j < 5; j++) for (let i = 0; i < 6; i++) {
        const frame = i === 0 || i === 5 || j === 0 || j === 4;
        set(ex + i, dTop + 1 + j, frame ? "rock-0" : "lamp");
      }
      const ix = ex + 1, iy = dTop + 2;           // interior 4×3
      const pupX = ix + 1 + p.look;
      if (p.eyes === "open") { set(pupX, iy + 1, "ink"); set(pupX + 1, iy + 1, "ink"); set(pupX, iy + 2, "ink"); set(pupX + 1, iy + 2, "ink"); }
      if (p.eyes === "wide") { for (let i = 0; i < 4; i++) for (let j = 0; j < 3; j++) set(ix + i, iy + j, "lamp-hi"); set(pupX, iy + 1, "ink"); set(pupX + 1, iy + 1, "ink"); }
      if (p.eyes === "half") { for (let i = 0; i < 4; i++) set(ix + i, iy, "copper-1"); set(pupX, iy + 2, "ink"); set(pupX + 1, iy + 2, "ink"); }
      if (p.eyes === "closed") { for (let i = 0; i < 4; i++) { set(ix + i, iy, "copper-1"); set(ix + i, iy + 1, "copper-1"); set(ix + i, iy + 2, "lamp-dim"); } }
    };
    eye(ux + 12); eye(ux + 25);
    // hatch + chart
    set(D0, dTop + 2, "ink"); set(D0, dTop + 3, "ink"); set(D0, dTop + 4, "ink");
    for (let k = 1; k <= p.chart; k++) { set(D0 - k, dTop + 3, "paper"); if (k < 3) set(D0 - k, dTop + 2, "paper"); if (k === 2) set(D0 - k, dTop + 3, "cream-dim"); }
    // ── dome, an oversized patched copper shell ──
    const R = 12, ccx = ux + 22, base = dTop - 1 - p.lift;
    if (p.lift) for (let i = ccx - R + 1; i <= ccx + R - 1; i++) set(i, dTop - 1, "ink");
    for (let dy = 0; dy <= R; dy++) {
      const half = Math.floor(Math.sqrt(R * R - dy * dy) + 0.3);
      for (let dxx = -half; dxx <= half; dxx++) {
        let c = "copper-2";
        if (dxx < -half / 3 && dy > R / 3) c = "copper-3";
        if (dxx > half / 2) c = "copper-1";
        if (Math.abs(dxx) === half || dy === R) c = "copper-0";
        if (dy === 3 && (dxx + 30) % 3 === 0 && Math.abs(dxx) < half) c = "copper-0";   // rivets
        set(ccx + dxx, base - dy, c);
      }
    }
    [[-7, 5], [-6, 5], [-6, 6], [-5, 6], [5, 8], [6, 8], [6, 9], [2, 10]].forEach(([a, b]) => set(ccx + a, base - b, "patina"));
    set(ccx - 6, base - 6, "patina-hi");
    for (let i = -2; i <= 1; i++) for (let j = 5; j <= 7; j++) set(ccx + i, base - j, (i === -2 || i === 1 || j === 5 || j === 7) ? "copper-1" : "copper-2");
    set(ccx - 2, base - 7, "copper-3"); set(ccx + 1, base - 5, "copper-3");

    // slit faces the telescope
    const a = rad(p.angle);
    const slitX = Math.round(ccx + Math.sin(a) * R * 0.5);
    for (let dy = 2; dy <= R - 1; dy++) {
      const half = Math.floor(Math.sqrt(R * R - dy * dy));
      for (let k = -1; k <= 1; k++) if (Math.abs(slitX + k - ccx) < half) set(slitX + k, base - dy, "ink");
    }

    // chimney + smoke
    const cx0 = ux + 33;
    for (let j = 0; j < 6; j++) for (let i = 0; i < 3; i++) set(cx0 + i, dTop - 5 + j, j === 0 ? "rock-3" : i === 2 ? "rock-1" : "rock-2");
    if (p.smoke > 0) {
      const f = p.smoke;
      const puff = (ox, oy, r) => { for (let i = -r; i <= r; i++) for (let j = -r; j <= r; j++) if (Math.abs(i) + Math.abs(j) <= r) set(cx0 + 1 + ox + i, dTop - 7 - oy + j, "smoke"); };
      puff(0, f, f > 4 ? 0 : 1);
      if (f > 2) puff(1, f + 3, 0);
    }

    // ── telescope snout ──
    const pvx = slitX, pvy = base - 5;
    const ux1 = Math.sin(a), uy1 = -Math.cos(a), nx = -uy1, ny = ux1;
    for (let t = 0; t <= 16; t += 0.5) {
      const thick = t > 12 ? 4 : 3;                       // dew shield
      for (let k = 0; k < thick; k++) {
        const o = k - (thick - 1) / 2;
        const px = pvx + ux1 * t + nx * o, py = pvy + uy1 * t + ny * o;
        set(px, py, (t > 6 && t < 7.5) || (t > 11.5 && t < 12.5) ? "copper-1" : k === 0 ? "brass-2" : k === thick - 1 ? "brass-0" : "brass-1");
      }
    }
    const tipX = Math.round(pvx + ux1 * 16.5), tipY = Math.round(pvy + uy1 * 16.5);
    set(tipX, tipY, "ink"); set(tipX + Math.round(nx), tipY + Math.round(ny), "ink");
    if (p.lantern) {
      const lx = Math.round(pvx + ux1 * 12), ly = Math.round(pvy + uy1 * 12) + 2;
      set(lx, ly, "ink"); set(lx, ly + 1, "ink");
      buf.rect(lx - 1, ly + 2, 3, 3, "signal"); set(lx, ly + 3, "lamp-hi");
    }
    return { pivot: { x: pvx, y: pvy }, tip: { x: tipX, y: tipY }, box: { x, y: g - H + 4, w: W, h: H } };
  }

  function moth(buf, x, y, f) {
    buf.set(x, y, "cream-dim");
    if (f % 2) { buf.set(x - 1, y - 1, "cream"); buf.set(x + 1, y - 1, "cream"); }
    else { buf.set(x - 1, y, "cream"); buf.set(x + 1, y, "cream"); }
  }

  /* Angle (deg from vertical) from the telescope pivot to an art-space point. */
  function aimAt(pivot, pt) {
    const d = (Math.atan2(pt.x - pivot.x, pivot.y - pt.y) * 180) / Math.PI;
    return Math.max(-20, Math.min(80, P.quantize(d)));
  }

  root.ObsCreature = { W, H, duskSky, hill, creature, moth, aimAt };
})(typeof window !== "undefined" ? window : globalThis);
