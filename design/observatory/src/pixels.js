/* Observatory pixel kit — deterministic, procedural, dependency-free.
 *
 * Editable source of every pixel asset in the study. The same functions draw
 * to <canvas> in the study page and to SVG files in build.mjs, so the
 * exported assets in assets/ are byte-for-byte reproducible.
 *
 * Model: a PixelBuffer is a w×h grid of palette *names* (strings). Drawing
 * functions only write names; colours are resolved at render time from
 * PALETTE (or from matching --px-* CSS custom properties in the page).
 *
 * Rules enforced here (see README → "Pixel rules"):
 *   - integer scale only; one art pixel is never split or anti-aliased;
 *   - scenery uses the closed --px-* palette; the only shared colour is the
 *     accent, and it appears only as the lit window (state, not decoration);
 *   - decorative stars are 1 art px and dim; data stars use STAR_GLYPHS (5×5)
 *     and are drawn by the UI layer, never by scenery;
 *   - everything random is seeded (mulberry32), so a seed always yields the
 *     same picture.
 */
(function (root) {
  "use strict";

  const PALETTE = {
    "void": "#070a10",
    "sky-hi": "#0d1420",
    "sky-lo": "#142032",
    "star-decor": "#3d4b60",
    "star-faint": "#2a3546",
    "hill-far": "#121a26",
    "hill-near": "#0c121b",
    "stone": "#3a4556",
    "stone-hi": "#56637a",
    "stone-lo": "#283140",
    "dome": "#8492a3",
    "dome-hi": "#b6c0cc",
    "dome-lo": "#5b6779",
    "slit": "#05080c",
    "window-off": "#2a2219",
    "window-on": "#f09a45",
    "glow": "#2e2116",
    "brass": "#9a8a6a",
    "tube": "#c9d1da",
    "tube-lo": "#8792a0",
    "leaf": "#101a1c",
    "leaf-hi": "#16252a",
    "mark": "#8db5c9",
    "mark-dim": "#57707e",
    "select": "#78aaf5",
    "accent": "#f09a45",
  };

  /* Lane → azimuth (degrees from zenith, negative = west/left).
   * Stable by lane order, never by activity: the telescope turning means
   * "you selected something in this lane", not "something happened here". */
  const AZIMUTH = { intent: -50, build: -18, verify: 18, ship: 50, other: 0 };
  const PARKED = 0;

  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function hash(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h;
  }

  class PixelBuffer {
    constructor(w, h) {
      this.w = w;
      this.h = h;
      this.px = new Array(w * h).fill(null);
    }
    set(x, y, name) {
      x = Math.round(x); y = Math.round(y);
      if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
      this.px[y * this.w + x] = name;
    }
    get(x, y) {
      if (x < 0 || y < 0 || x >= this.w || y >= this.h) return null;
      return this.px[y * this.w + x];
    }
    rect(x, y, w, h, name) {
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) this.set(x + i, y + j, name);
    }
    /* Stamp a character grid. legend maps chars to palette names; '.' is transparent. */
    grid(x, y, rows, legend) {
      rows.forEach((row, j) => {
        [...row].forEach((ch, i) => {
          if (ch !== "." && legend[ch]) this.set(x + i, y + j, legend[ch]);
        });
      });
    }
  }

  /* ── Scenery ─────────────────────────────────────────────────────── */

  /* Night sky: two-tone ordered dither (no gradients) + seeded 1px decorative stars.
   * `quiet` is a list of {x,y,w,h} rects that must stay free of decorative stars
   * (labels, data, anything readable). */
  function sky(buf, seed, opts = {}) {
    const rnd = mulberry32(seed);
    const bayer = [0, 2, 3, 1];
    const split = opts.horizon ?? buf.h;
    for (let y = 0; y < buf.h; y++) {
      const t = y / Math.max(1, split);
      for (let x = 0; x < buf.w; x++) {
        const thr = (bayer[(x & 1) + 2 * (y & 1)] + 0.5) / 4;
        const m = (t - 0.62) / 0.22;                // dither only in a narrow band
        buf.set(x, y, opts.solid ? opts.solid : m >= 1 || (m > 0 && m > thr) ? "sky-lo" : "sky-hi");
      }
    }
    const density = opts.density ?? 0.012;
    const n = Math.round(buf.w * split * density);
    const quiet = opts.quiet || [];
    for (let i = 0; i < n; i++) {
      const x = Math.floor(rnd() * buf.w);
      const y = Math.floor(rnd() * split * 0.92);
      const bright = rnd() > 0.82;
      if (quiet.some((q) => x >= q.x && x < q.x + q.w && y >= q.y && y < q.y + q.h)) continue;
      buf.set(x, y, bright ? "star-decor" : "star-faint");
    }
  }

  /* Seeded 1-D value noise, smoothed — used for hill silhouettes. */
  function ridge(seed, w, base, amp, period) {
    const rnd = mulberry32(seed);
    const knots = [];
    for (let i = 0; i <= Math.ceil(w / period) + 1; i++) knots.push(rnd());
    const out = [];
    for (let x = 0; x < w; x++) {
      const k = x / period, i = Math.floor(k), f = k - i;
      const s = f * f * (3 - 2 * f);
      out.push(Math.round(base - amp * (knots[i] * (1 - s) + knots[i + 1] * s)));
    }
    return out;
  }

  function hills(buf, seed, groundY) {
    const far = ridge(seed, buf.w, groundY - 2, 9, 22);
    const near = ridge(seed + 7, buf.w, groundY + 1, 4, 13);
    for (let x = 0; x < buf.w; x++) {
      for (let y = far[x]; y < buf.h; y++) buf.set(x, y, "hill-far");
      for (let y = near[x]; y < buf.h; y++) buf.set(x, y, "hill-near");
    }
  }

  const TREE = [
    "...a...",
    "..aaa..",
    "..aAa..",
    ".aaaaa.",
    ".aAaaa.",
    "aaaaaAa",
    ".aaaaa.",
    "aaaAaaa",
    "...s...",
    "...s...",
  ];
  function tree(buf, x, groundY) {
    buf.grid(x, groundY - TREE.length, TREE, { a: "leaf", A: "leaf-hi", s: "stone-lo" });
  }

  /* The observatory: a stone house with a rotating dome.
   *   state.angle   telescope azimuth in degrees (−60…60); the dome slit rotates with it
   *   state.open    shutter open (something is selected) / closed (parked)
   *   state.lit     window lit = the loaded snapshot asks for a conversation
   * Returns anchor points so the UI can align labels. */
  function observatory(buf, x, groundY, state = {}) {
    const W = 26, H = 12, R = 12;
    const top = groundY - H;
    const cx = x + 13;
    const angle = quantize(state.angle ?? PARKED);
    const open = !!state.open;
    const lit = !!state.lit;

    // Glow first, so the house draws over it.
    if (lit) {
      for (let j = 0; j < 3; j++) {
        for (let i = -j; i < 4 + j; i++) {
          const gx = x + 5 + i, gy = groundY + j;
          if (buf.get(gx, gy) && (j < 2 || (gx + gy) % 2 === 0)) buf.set(gx, gy, "glow");
        }
      }
    }

    // House body with brick courses.
    for (let j = 0; j < H; j++) {
      for (let i = 0; i < W; i++) {
        let c = i > W - 8 ? "stone-lo" : "stone";
        if (j === 0) c = "stone-hi";
        else if (j % 4 === 0 && (i + (j % 8 === 0 ? 0 : 3)) % 6 !== 0) c = "stone-lo";
        buf.set(x + i, top + j, c);
      }
    }
    // Ledge under the dome.
    buf.rect(x - 1, top - 1, W + 2, 1, "stone-hi");

    // Dome (semicircle) with light from upper left.
    const base = top - 1;
    for (let dy = 0; dy <= R; dy++) {
      const half = Math.floor(Math.sqrt(R * R - dy * dy));
      for (let dx = -half; dx <= half; dx++) {
        const edge = Math.abs(dx) === half || dy === R;
        let c = "dome";
        if (dx < -half / 3 && dy > R / 3) c = "dome-hi";
        if (dx > half / 2) c = "dome-lo";
        if (edge) c = "dome-lo";
        buf.set(cx + dx, base - dy, c);
      }
    }

    // Slit: rotates with the telescope (projected onto the dome face).
    const slitX = Math.round(cx + Math.sin(rad(angle)) * R * 0.6);
    for (let dy = 1; dy <= R; dy++) {
      const half = Math.floor(Math.sqrt(R * R - dy * dy));
      for (let k = -1; k <= 1; k++) {
        const sx = slitX + k;
        if (Math.abs(sx - cx) > half - 1) continue;
        buf.set(sx, base - dy, open ? "slit" : (k === 0 ? "dome-lo" : buf.get(sx, base - dy)));
      }
    }

    // Telescope tube through the open slit.
    let tip = null;
    if (open) {
      const px = slitX, py = base - 3;
      tip = tube(buf, px, py, angle, 15, 2);
    }

    // Window (lit or not) and door.
    const wx = x + 5, wy = top + 3;
    buf.rect(wx - 1, wy - 1, 6, 7, "stone-lo");
    buf.rect(wx, wy, 4, 5, lit ? "window-on" : "window-off");
    buf.rect(wx + 2, wy, 1, 5, "stone-lo");
    buf.rect(wx, wy + 2, 4, 1, "stone-lo");
    buf.rect(x + 17, top + 4, 5, 8, "stone-lo");
    buf.rect(x + 18, top + 5, 3, 7, "slit");

    return { cx, base, slitX, tip, window: { x: wx, y: wy, w: 4, h: 5 }, door: { x: x + 17, y: top + 4 } };
  }

  /* A tube of given thickness along `angle` (deg from vertical) from (x,y). */
  function tube(buf, x, y, angle, len, thick) {
    const a = rad(angle);
    const ux = Math.sin(a), uy = -Math.cos(a);
    const nx = -uy, ny = ux;
    for (let t = 0; t <= len; t += 0.5) {
      for (let k = 0; k < thick; k++) {
        const px = x + ux * t + nx * (k - (thick - 1) / 2);
        const py = y + uy * t + ny * (k - (thick - 1) / 2);
        buf.set(px, py, k === 0 ? "tube" : "tube-lo");
      }
    }
    const tx = Math.round(x + ux * len), ty = Math.round(y + uy * len);
    buf.set(tx, ty, "brass");
    return { x: tx, y: ty };
  }

  /* Study B — a refractor on a German equatorial mount, for the instrument panel.
   * Counterweight sits on the declination axis (perpendicular to the tube). */
  function refractor(buf, x, groundY, state = {}) {
    const angle = quantize(state.angle ?? PARKED);
    const a = rad(angle);
    const ux = Math.sin(a), uy = -Math.cos(a);
    let nx = Math.cos(a), ny = Math.sin(a);
    if (ny < 0 || (ny === 0 && nx > 0)) { nx = -nx; ny = -ny; }   // n points downward
    // Pier, feet, mount head.
    buf.rect(x - 2, groundY - 14, 4, 14, "stone");
    buf.rect(x + 1, groundY - 14, 1, 14, "stone-lo");
    buf.rect(x - 6, groundY - 1, 12, 1, "stone-hi");
    buf.rect(x - 5, groundY, 10, 1, "stone-lo");
    buf.rect(x - 3, groundY - 18, 6, 4, "brass");
    buf.rect(x + 1, groundY - 18, 2, 4, "stone-lo");
    const px = x, py = groundY - 20;
    // Counterweight shaft and weight (down side).
    tube(buf, px, py, Math.atan2(nx, -ny) * 180 / Math.PI, 7, 1);
    buf.rect(Math.round(px + nx * 8) - 1, Math.round(py + ny * 8) - 1, 3, 3, "stone-hi");
    // Main tube, dew shield, finder (up side), eyepiece.
    tube(buf, px - ux * 6, py - uy * 6, angle, 24, 3);
    const tip = tube(buf, px + ux * 18, py + uy * 18, angle, 6, 5);
    tube(buf, px - nx * 3 + ux * 2, py - ny * 3 + uy * 2, angle, 7, 1);
    buf.rect(Math.round(px - ux * 7) - 1, Math.round(py - uy * 7) - 1, 2, 2, "brass");
    buf.rect(Math.round(px) - 1, Math.round(py) - 1, 2, 2, "brass");
    return { pivot: { x: px, y: py }, tip };
  }

  /* Graduated azimuth arc around a pivot. Ticks every 10°, long ticks at lane azimuths. */
  function arc(buf, cx, cy, r, laneIds) {
    for (let d = -70; d <= 70; d += 5) {
      const a = rad(d);
      const long = laneIds.some((id) => AZIMUTH[id] === d);
      const len = long ? 3 : d % 10 === 0 ? 1 : 0;
      for (let k = 0; k <= len; k++) {
        buf.set(cx + Math.sin(a) * (r + k), cy - Math.cos(a) * (r + k), long ? "stone-hi" : "stone");
      }
    }
  }

  /* Eyepiece field (study B inspector). Field stars are decorative and 1px;
   * data glyphs are added by the UI on top. */
  function eyepiece(buf, seed) {
    const cx = (buf.w - 1) / 2, cy = (buf.h - 1) / 2, r = Math.min(cx, cy);
    const rnd = mulberry32(seed);
    for (let y = 0; y < buf.h; y++) {
      for (let x = 0; x < buf.w; x++) {
        const d = Math.hypot(x - cx, y - cy);
        if (d <= r - 2) buf.set(x, y, "void");
        else if (d <= r) buf.set(x, y, "stone");
      }
    }
    for (let i = 0; i < 26; i++) {
      const x = Math.floor(rnd() * buf.w), y = Math.floor(rnd() * buf.h);
      if (buf.get(x, y) === "void" && Math.hypot(x - cx, y - cy) > 6) buf.set(x, y, "star-faint");
    }
    // Reticle: dashed crosshair with a gap at the centre.
    for (let t = 0; t < buf.w; t++) {
      if (Math.abs(t - cx) < 5 || t % 3 === 2) continue;
      if (buf.get(t, Math.round(cy)) === "void" || buf.get(t, Math.round(cy)) === "star-faint") buf.set(t, Math.round(cy), "stone");
      if (buf.get(Math.round(cx), t) === "void" || buf.get(Math.round(cx), t) === "star-faint") buf.set(Math.round(cx), t, "stone");
    }
  }

  /* ── Data glyphs (UI layer) ──────────────────────────────────────
   * 5×5, one per work-item status. Shape carries status so it survives
   * greyscale; colour only adds selection (select) or attention (accent). */
  const STAR_GLYPHS = {
    in_flight: ["..x..", "..x..", "xxXxx", "..x..", "..x.."],
    draft:     ["..x..", ".....", "x.X.x", ".....", "..x.."],
    stale:     [".....", "..x..", ".xXx.", "..x..", "....."],
    landed:    [".xxx.", "x...x", "x...x", "x...x", ".xxx."],
  };

  /* 9×9 icons. One-colour silhouettes; meaning is also always written in text. */
  const ICONS = {
    overlap:  [".........", ".xxx.....", "x...x....", "x..xxxx..", "x..x.x.x.", ".xxxx..x.", "...x...x.", "....xxx..", "........."],
    waiting:  [".........", "....x....", "....xx...", "xxxxxxx..", "....xx...", "....x....", ".........", "x.x.x.x..", "........."],
    stale:    [".........", "..xxxxx..", ".x.....x.", ".x..x..x.", ".x..xx.x.", ".x.....x.", "..xxxxx..", ".........", "........."],
    declared: [".........", ".xxxxxx..", ".x....x..", ".x.xx.x..", ".x....x..", ".x.xx.x..", ".x....x..", ".xxxxxx..", "........."],
    plate:    [".........", "xxxxxxxxx", "x.......x", "x..x....x", "x.xxx...x", "x..x..x.x", "x.......x", "xxxxxxxxx", "........."],
    dome:     [".........", "...xxx...", "..xx.xx..", ".xxx.xxx.", ".xxx.xxx.", "xxxxxxxxx", "x.x...x.x", "x.x...x.x", "xxxxxxxxx"],
  };

  function glyph(buf, x, y, rows, name, centerName) {
    rows.forEach((row, j) => [...row].forEach((ch, i) => {
      if (ch === "x") buf.set(x + i, y + j, name);
      if (ch === "X") buf.set(x + i, y + j, centerName || name);
    }));
  }

  /* ── Renderers ───────────────────────────────────────────────── */

  function resolve(name, overrides) {
    return (overrides && overrides[name]) || PALETTE[name] || "#ff00ff";
  }

  function toCanvas(canvas, buf, scale, overrides) {
    canvas.width = buf.w * scale;
    canvas.height = buf.h * scale;
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let y = 0; y < buf.h; y++) {
      for (let x = 0; x < buf.w; x++) {
        const n = buf.px[y * buf.w + x];
        if (!n) continue;
        ctx.fillStyle = resolve(n, overrides);
        ctx.fillRect(x * scale, y * scale, scale, scale);
      }
    }
  }

  /* SVG with horizontal run-length rects; shape-rendering keeps edges crisp. */
  function toSVG(buf, overrides, title) {
    const rects = [];
    for (let y = 0; y < buf.h; y++) {
      let x = 0;
      while (x < buf.w) {
        const n = buf.px[y * buf.w + x];
        let run = 1;
        while (x + run < buf.w && buf.px[y * buf.w + x + run] === n) run++;
        if (n) rects.push(`<rect x="${x}" y="${y}" width="${run}" height="1" fill="${resolve(n, overrides)}"/>`);
        x += run;
      }
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${buf.w} ${buf.h}" width="${buf.w * 4}" height="${buf.h * 4}" shape-rendering="crispEdges">` +
      (title ? `<title>${title}</title>` : "") + rects.join("") + `</svg>\n`;
  }

  /* Read --px-* custom properties so tokens.css stays the single source of colour. */
  function paletteFromCSS(el) {
    if (typeof getComputedStyle === "undefined") return {};
    const cs = getComputedStyle(el || document.documentElement);
    const out = {};
    for (const k of Object.keys(PALETTE)) {
      const v = cs.getPropertyValue("--px-" + k).trim();
      if (v && !v.startsWith("var(")) out[k] = v;
    }
    const acc = cs.getPropertyValue("--accent").trim();
    if (acc) { out["window-on"] = acc; out.accent = acc; }
    for (const k of ["mark", "mark-dim", "select"]) {
      const v = cs.getPropertyValue("--" + k).trim();
      if (v) out[k] = v;
    }
    return out;
  }

  function rad(d) { return (d * Math.PI) / 180; }
  function quantize(d) { return Math.round(d / 5) * 5; }

  root.ObsPixels = {
    PALETTE, AZIMUTH, PARKED, STAR_GLYPHS, ICONS,
    PixelBuffer, mulberry32, hash,
    sky, hills, tree, observatory, refractor, arc, eyepiece, tube, glyph,
    toCanvas, toSVG, paletteFromCSS, quantize,
  };
})(typeof window !== "undefined" ? window : globalThis);
