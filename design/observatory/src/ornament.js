/* Direction D — the observatory tortoise as a corner ornament (like Weavr's sidebar character).
 *
 * Frames are the owner's painted north star, pixelated (creature/frames, see creature/rig/README.md).
 * Posture is the one state it carries, and the page always says it in words too:
 *   rest   — dome closed, sleepy eyes: nothing needs a conversation
 *   up     — dome open, telescope out, lantern lit: an overlap or wait exists
 *   travel — up, with a slow one-pixel plod: replay is playing
 * Blinking, breathing, glow and flicker are decoration: they stop with reduced motion.
 */
(function (root) {
  "use strict";
  const W = 320, H = 179, FOOT = 140;
  const CROP = [74, 0, 236, 152];
  const FACE = [74, 62, 104, 88];
  const BOX = { eyeNear: [116, 74, 46, 37], eyeFar: [79, 86, 21, 27], lantern: [142, 35, 12, 14] };
  const PIVOT = [182, 40];
  const NIGHT = [25, 27, 56];

  let px = null, rank = null, nDiff = 0, ready = null;
  const hash = (i) => { let h = (i * 2654435761) >>> 0; h ^= h >>> 15; return (h % 1000) / 1000; };
  const inBox = (x, y, b) => x >= b[0] && x < b[0] + b[2] && y >= b[1] && y < b[1] + b[3];

  function load() {
    if (ready) return ready;
    const F = root.ObsFrames || {};
    const get = (src) => new Promise((res) => {
      const im = new Image();
      im.onload = () => { const c = document.createElement("canvas"); c.width = W; c.height = H; const x = c.getContext("2d"); x.drawImage(im, 0, 0); res(x.getImageData(0, 0, W, H).data); };
      im.onerror = () => res(null);
      im.src = src;
    });
    ready = Promise.all([get(F.cutUp), get(F.cutRest)]).then(([up, rest]) => {
      if (!up || !rest) return;
      px = { up, rest };
      // the dome opens as a reveal spreading out from the slit
      const diff = [];
      for (let i = 0; i < W * H; i++) {
        const k = i * 4, x = i % W, y = (i / W) | 0;
        if (inBox(x, y, BOX.eyeNear) || inBox(x, y, BOX.eyeFar)) continue;
        if (up[k + 3] !== rest[k + 3] || up[k] !== rest[k] || up[k + 1] !== rest[k + 1] || up[k + 2] !== rest[k + 2]) diff.push([i, Math.hypot(x - PIVOT[0], (y - PIVOT[1]) * 1.3) + hash(i) * 7]);
      }
      diff.sort((a, b) => a[1] - b[1]);
      rank = new Int32Array(W * H).fill(-1);
      diff.forEach(([i], r) => { rank[i] = r; });
      nDiff = diff.length;
    });
    return ready;
  }

  function compose(img, st) {
    const O = img.data, U = px.up, R = px.rest, t = st.t, motion = st.motion;
    // night ground with a few fixed pixel stars (decorative)
    for (let i = 0; i < W * H; i++) { const k = i * 4; O[k] = NIGHT[0]; O[k + 1] = NIGHT[1]; O[k + 2] = NIGHT[2]; O[k + 3] = 255; if (hash(i * 7 + 3) > 0.996 && ((i / W) | 0) < 70) { const tw = motion && hash(i + Math.floor(t / 5)) > 0.75 ? 0.55 : 1; O[k] = 230 * tw; O[k + 1] = 222 * tw; O[k + 2] = 200 * tw; } }
    const shown = Math.round(nDiff * st.open), upBase = st.open > 0.5;
    let eyesOpen = st.state !== "rest";
    if (motion && st.state !== "rest" && t % 62 > 59) eyesOpen = false;
    if (motion && st.state === "rest" && t % 150 > 134) eyesOpen = true;
    const rise = motion && ((st.state === "rest" && t % 44 < 9) || (st.state === "travel" && Math.floor(t / 3) % 2 === 0)) ? 1 : 0;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x;
      let src;
      if (inBox(x, y, BOX.eyeNear) || inBox(x, y, BOX.eyeFar)) src = eyesOpen ? U : R;
      else if (rank[i] >= 0) src = rank[i] < shown ? U : R;
      else src = upBase ? U : R;
      const k = i * 4;
      if (!src[k + 3]) continue;
      const dy = rise && y < FOOT && y > 0 ? y - 1 : y;
      const d = (dy * W + x) * 4;
      O[d] = src[k]; O[d + 1] = src[k + 1]; O[d + 2] = src[k + 2];
    }
    const warm = (k, f) => { if (O[k] > 150 && O[k] > O[k + 2] + 60) { O[k] = Math.min(255, O[k] * f); O[k + 1] = Math.min(255, O[k + 1] * f); } };
    if (motion && eyesOpen) { const f = 1 + 0.07 * Math.sin(t / 5); for (const b of [BOX.eyeNear, BOX.eyeFar]) for (let y = b[1]; y < b[1] + b[3]; y++) for (let x = b[0]; x < b[0] + b[2]; x++) warm((y * W + x) * 4, f); }
    if (motion && st.open > 0.5) { const f = 0.93 + 0.14 * hash(t); const b = BOX.lantern; for (let y = b[1]; y < b[1] + b[3]; y++) for (let x = b[0]; x < b[0] + b[2]; x++) warm((y * W + x) * 4, f); }
  }

  function paint(canvas, img, crop, scale) {
    const s = document.createElement("canvas"); s.width = W; s.height = H; s.getContext("2d").putImageData(img, 0, 0);
    canvas.width = crop[2] * scale; canvas.height = crop[3] * scale;
    const ctx = canvas.getContext("2d"); ctx.imageSmoothingEnabled = false;
    ctx.drawImage(s, crop[0], crop[1], crop[2], crop[3], 0, 0, crop[2] * scale, crop[3] * scale);
  }

  function create() {
    const node = document.createElement("div");
    node.className = "ornament";
    const cv = document.createElement("canvas");
    cv.className = "px"; cv.setAttribute("aria-hidden", "true");
    node.append(cv);
    const st = { state: "rest", motion: true, t: 0, open: 0 };
    const img = new ImageData(W, H);
    let timer = null;
    const draw = () => { if (px) { compose(img, st); paint(cv, img, CROP, 1); } };
    function tick() {
      if (!node.isConnected) return;
      st.t++;
      const target = st.state === "rest" ? 0 : 1;
      st.open += Math.max(-0.07, Math.min(0.07, target - st.open));
      draw();
    }
    function update(s) {
      st.state = s.state;
      const changed = st.motion !== s.motion;
      st.motion = s.motion;
      if (!s.motion) st.open = s.state === "rest" ? 0 : 1;
      if (changed || !timer) { clearInterval(timer); timer = s.motion ? setInterval(tick, 100) : null; }
      load().then(draw);
    }
    return { node, update };
  }

  function portrait(canvas, state) {
    load().then(() => {
      if (!px) return;
      const img = new ImageData(W, H);
      compose(img, { state, motion: false, t: 0, open: state === "rest" ? 0 : 1 });
      paint(canvas, img, FACE, 1);
    });
  }

  root.ObsOrnament = { create, portrait };
})(typeof window !== "undefined" ? window : globalThis);
