// Build the self-contained study page and export pixel assets.
//
//   node design/observatory/build.mjs
//
// Deterministic and dependency-free (Node ≥ 18). Writes:
//   index.html        — study.src.html with tokens, CSS and JS inlined
//   assets/*.svg      — pixel assets rendered from src/pixels.js
//   assets/tokens.json — the token proposal as data, for the typed frontend
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, p), "utf8");

// 1 · Inline the study page.
const html = read("study.src.html")
  .replace(/<!-- @inline-css (\S+) -->/g, (_, p) => `<style>\n/* ${p} */\n${read(p)}</style>`)
  .replace(/<!-- @inline-js (\S+) -->/g, (_, p) => `<script>\n/* ${p} */\n${read(p).replace(/<\/script/gi, "<\\/script")}</script>`);
writeFileSync(join(here, "index.html"), html);

// 2 · Export assets from the same drawing code the page uses.
const ctx = vm.createContext({});
vm.runInContext(read("src/pixels.js"), ctx);
const P = ctx.ObsPixels;
mkdirSync(join(here, "assets"), { recursive: true });
const out = (name, buf, title) => writeFileSync(join(here, "assets", name), P.toSVG(buf, null, title));
const lanes = ["intent", "build", "verify", "ship"];

const obs = (o) => { const b = new P.PixelBuffer(34, 34); b.rect(0, 30, 34, 4, "hill-near"); P.observatory(b, 4, 30, o); return b; };
out("observatory-parked.svg", obs({ open: false, lit: false }), "Observatory, parked, window unlit");
out("observatory-parked-lit.svg", obs({ open: false, lit: true }), "Observatory, parked, window lit");
for (const l of lanes) {
  out(`observatory-${l}.svg`, obs({ open: true, lit: false, angle: P.AZIMUTH[l] }), `Observatory pointing at ${l}`);
  out(`observatory-${l}-lit.svg`, obs({ open: true, lit: true, angle: P.AZIMUTH[l] }), `Observatory pointing at ${l}, window lit`);
  const r = new P.PixelBuffer(82, 62);
  P.arc(r, 41, 38, 32, lanes);
  P.refractor(r, 41, 58, { angle: P.AZIMUTH[l] });
  out(`refractor-${l}.svg`, r, `Refractor pointing at ${l}`);
}
const rp = new P.PixelBuffer(82, 62); P.arc(rp, 41, 38, 32, lanes); P.refractor(rp, 41, 58, { angle: 0 });
out("refractor-parked.svg", rp, "Refractor parked");

const court = new P.PixelBuffer(96, 66);
P.sky(court, 17, { horizon: 50, density: 0.02 }); P.hills(court, 3, 54); court.rect(0, 56, 96, 10, "hill-near");
P.tree(court, 6, 56); P.tree(court, 15, 57); P.observatory(court, 62, 56, { open: true, lit: true, angle: -18 });
out("courtyard-overlap.svg", court, "Courtyard scene: telescope on Build, window lit");

const hz = new P.PixelBuffer(320, 12); P.sky(hz, 31, { horizon: 12, density: 0.03, solid: "sky-hi" }); P.hills(hz, 5, 13);
out("horizon-strip.svg", hz, "Horizon strip (decorative)");

const eye = new P.PixelBuffer(56, 56); P.eyepiece(eye, 13);
out("eyepiece-field.svg", eye, "Eyepiece field with reticle (decorative field stars)");

for (const [k, rows] of Object.entries(P.STAR_GLYPHS)) {
  const b = new P.PixelBuffer(5, 5); P.glyph(b, 0, 0, rows, "mark", "mark"); out(`star-${k.replace("_", "-")}.svg`, b, `Data star: ${k}`);
}
for (const [k, rows] of Object.entries(P.ICONS)) {
  const b = new P.PixelBuffer(9, 9); P.glyph(b, 0, 0, rows, "dome-hi"); out(`icon-${k}.svg`, b, `Icon: ${k}`);
}

// 3 · Tokens as data (parsed from tokens.css :root, night + paper).
const css = read("tokens.css");
const block = (sel) => {
  const i = css.indexOf(sel + " {");
  const body = css.slice(css.indexOf("{", i) + 1, css.indexOf("\n}", i));
  return Object.fromEntries([...body.matchAll(/--([\w-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]));
};
writeFileSync(join(here, "assets", "tokens.json"), JSON.stringify({
  status: "proposal — pending owner templates",
  night: block(":root"),
  paper: block(':root[data-theme="paper"]'),
  azimuth: P.AZIMUTH,
  pixel_palette: P.PALETTE,
}, null, 2) + "\n");

console.log("built index.html and assets/");
