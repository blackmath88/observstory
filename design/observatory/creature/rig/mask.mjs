// Creature masks from the flat-background frame (19), adapted per state frame.
import { readFileSync, writeFileSync } from "node:fs";
const W = 320, H = 179, N = W * H;
const rd = (f) => readFileSync(f);
const f19 = rd("f19.raw"), f17 = rd("f17.raw"), f18 = rd("f18.raw");
const px = (b, i) => [b[i * 3], b[i * 3 + 1], b[i * 3 + 2]];
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
// background estimate per pixel: median of the border columns in the same row band (navy with soft clouds)
const bgRow = [];
for (let y = 0; y < H; y++) { const s = []; for (const x of [0, 1, 2, 3, W - 4, W - 3, W - 2, W - 1]) s.push(px(f19, y * W + x)); s.sort((a, b) => a[0] + a[1] + a[2] - (b[0] + b[1] + b[2])); bgRow.push(s[4]); }
const bgLike = new Uint8Array(N);
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const i = y * W + x; bgLike[i] = dist(px(f19, i), bgRow[y]) < 34 ? 1 : 0; }
// flood fill background from the border; everything unreached is creature (fills dark interior holes)
const reach = new Uint8Array(N); const q = [];
for (let x = 0; x < W; x++) { q.push(x, (H - 1) * W + x); } for (let y = 0; y < H; y++) { q.push(y * W, y * W + W - 1); }
while (q.length) { const i = q.pop(); if (reach[i] || !bgLike[i]) continue; reach[i] = 1; const x = i % W, y = (i / W) | 0; if (x > 0) q.push(i - 1); if (x < W - 1) q.push(i + 1); if (y > 0) q.push(i - W); if (y < H - 1) q.push(i + W); }
let mUp = new Uint8Array(N); for (let i = 0; i < N; i++) mUp[i] = reach[i] ? 0 : 1;
// remove specks (opening: drop pixels with < 3 mask neighbours)
const clean = (m) => { const o = new Uint8Array(m); for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) { const i = y * W + x; if (!m[i]) continue; let n = 0; for (const d of [-1, 1, -W, W, -W - 1, -W + 1, W - 1, W + 1]) n += m[i + d]; if (n < 3) o[i] = 0; } return o; };
mUp = clean(clean(mUp));
// close small holes (outline pixels that matched the background)
const close = (m) => { const o = new Uint8Array(m); for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) { const i = y * W + x; if (m[i]) continue; let n = 0; for (const d of [-1, 1, -W, W, -W - 1, -W + 1, W - 1, W + 1]) n += m[i + d]; if (n >= 5) o[i] = 1; } return o; };
mUp = close(close(mUp));
// keep the creature: largest component plus small parts (birds, balcony) close to it
const comp = new Int32Array(N).fill(-1); const sizes = []; const boxes = [];
for (let s = 0; s < N; s++) { if (!mUp[s] || comp[s] >= 0) continue; const id = sizes.length; let n = 0, x0 = W, y0 = H, x1 = 0, y1 = 0; const st = [s]; comp[s] = id;
  while (st.length) { const i = st.pop(); n++; const x = i % W, y = (i / W) | 0; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    for (const d of [-1, 1, -W, W]) { const j = i + d; if (j < 0 || j >= N || Math.abs((j % W) - x) > 1) continue; if (mUp[j] && comp[j] < 0) { comp[j] = id; st.push(j); } } }
  sizes.push(n); boxes.push([x0, y0, x1, y1]); }
const big = sizes.indexOf(Math.max(...sizes)); const B = boxes[big];
const keep = sizes.map((n, k) => k === big || (n >= 2 && boxes[k][0] >= B[0] - 3 && boxes[k][2] <= B[2] + 3 && boxes[k][1] >= B[1] - 6 && boxes[k][3] <= B[3] + 3));
for (let i = 0; i < N; i++) if (mUp[i] && !keep[comp[i]]) mUp[i] = 0;
// the lantern's glow halo in frame 19 is not creature in frame 17: drop sky-coloured pixels around it
const skyish = (c) => c[2] > c[0] && c[2] > c[1] && c[0] + c[1] + c[2] > 200;
for (let y = 24; y < 64; y++) for (let x = 128; x < 170; x++) { const i = y * W + x; if (mUp[i] && skyish(px(f17, i))) mUp[i] = 0; }
// loose cloud fragments from frame 19
for (let y = 0; y < 46; y++) for (let x = 0; x < W; x++) if (x < 126 || x > 236) mUp[y * W + x] = 0;
// resting mask: same, but where the telescope was, keep only pixels that do not look like that row's sky in frame 18
const mRest = new Uint8Array(mUp);
for (let y = 0; y < H; y++) {
  const sky = px(f18, y * W + 100);           // a sky sample left of the creature at this row
  for (let x = 120; x < 176; x++) { const i = y * W + x; if (y > 58) continue; const c = px(f18, i); if (mRest[i] && ((dist(c, sky) < 26 && c[2] > c[1]) || (c[2] > c[0] && c[2] > c[1] && c[0] + c[1] + c[2] > 200))) mRest[i] = 0; }
}
const outMask = (m, f) => { const o = Buffer.alloc(N); for (let i = 0; i < N; i++) o[i] = m[i] ? 255 : 0; writeFileSync(f, o); };
outMask(mUp, "mUp.gray"); outMask(clean(mRest), "mRest.gray");
let a = 0, b = 0; for (let i = 0; i < N; i++) { a += mUp[i]; b += mRest[i]; }
console.log("mask px up", a, "rest", b);
