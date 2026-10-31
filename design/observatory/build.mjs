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
  .replace("<!-- @inline-frames -->", () => {
    const uri = (f) => "data:image/png;base64," + readFileSync(join(here, "creature/frames", f)).toString("base64");
    return `<script>\n/* creature/frames (owner's painted north star, pixelated) */\nwindow.ObsFrames = ${JSON.stringify({ cutUp: uri("cut-up.png"), cutRest: uri("cut-rest.png") })};\n</script>`;
  })
  .replace(/<!-- @inline-js (\S+) -->/g, (_, p) => `<script>\n/* ${p} */\n${read(p).replace(/<\/script/gi, "<\\/script")}</script>`);
writeFileSync(join(here, "index.html"), html);

// 2 · Export assets from the same drawing code the page uses.
const ctx = vm.createContext({});
vm.runInContext(read("src/pixels.js"), ctx);
vm.runInContext(read("src/creature.js"), ctx);
const P = ctx.ObsPixels, C = ctx.ObsCreature;
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

// D · the living observatory, one SVG per habit pose.
const POSES = {
  resting: { eyes: "closed", angle: 70 },
  attentive: { eyes: "open", angle: 35, lantern: true, note: true },
  listening: { eyes: "open", lift: 1, lean: -1, angle: 10, door: 2, look: -1 },
  notes: { eyes: "half", chart: 4, angle: 50 },
  greeting: { eyes: "wide", smoke: 3, angle: 60, look: 1 },
};
for (const [k, pose] of Object.entries(POSES)) {
  const b = new P.PixelBuffer(58, 50);
  C.duskSky(b, 5, { horizon: 46, density: 0.01 }); C.hill(b, 2, 0, 0, 46, 46);
  C.creature(b, 6, 46, pose);
  out(`living-${k}.svg`, b, `Living observatory: ${k}`);
}
const WALK = {
  lying: { raise: 0, head: 0, eyes: "closed", angle: 60 },
  rising: { raise: 2, head: 1, eyes: "half", angle: 45 },
  standing: { raise: 5, head: 3, eyes: "open", lantern: true, angle: 20, note: true },
  walking: { raise: 5, head: 3, step: 1, eyes: "open", angle: -15 },
  greeting: { raise: 5, head: 4, eyes: "wide", angle: 40 },
};
for (const [k, pose] of Object.entries(WALK)) {
  const b = new P.PixelBuffer(50, 40);
  C.duskSky(b, 41, { horizon: 35, density: 0.02 }); b.rect(0, 35, 50, 5, "moss-1"); for (let x = 0; x < 50; x++) b.set(x, 35, "moss-2");
  C.turtle(b, 3, 35, pose);
  out(`walking-observatory-${k}.svg`, b, `Walking observatory: ${k}`);
}
const wsprite = new P.PixelBuffer(46, 40); C.turtle(wsprite, 1, 38, WALK.standing);
out("walking-observatory-sprite.svg", wsprite, "Walking observatory sprite on transparent ground");
const sprite = new P.PixelBuffer(50, 50); C.creature(sprite, 2, 46, POSES.attentive);
out("living-sprite-transparent.svg", sprite, "Living observatory sprite on transparent ground");

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
  dusk_direction_d: block(':root[data-direction="d"]'),
  azimuth: P.AZIMUTH,
  pixel_palette: P.PALETTE,
}, null, 2) + "\n");

console.log("built index.html and assets/");
