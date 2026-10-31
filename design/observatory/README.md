# Observatory pixel-design studies

> **Synthetic data notice.** Every work item, author handle, commit and file in this study is
> invented. The project name echoes the BaselHack use case (Photo Frame Commons) only so the
> content reads plausibly. Nothing here was observed from GitHub.

This is a **design study**: the slice-1 deliverable of
[`docs/plans/OBSERVATORY-REWRITE.md`](../../docs/plans/OBSERVATORY-REWRITE.md), briefed in
[`CLAUDE-PIXEL-DESIGN-HANDOFF.md`](../../docs/plans/CLAUDE-PIXEL-DESIGN-HANDOFF.md). It is not the
frontend rewrite. It changes no producer code, schema, renderer or Action.

Open `index.html` in a browser. It is self-contained and makes no network requests. The study bar
at the top switches between:

- **Direction:** D Living (the default since owner feedback on 31 Oct), A Courtyard, B Instrument, C Atlas;
- **State:** Quiet, Overlap, Replay;
- **Theme:** Night (the default for this study), Paper;
- **Motion:** decorative motion on or off. The system's reduced-motion setting always wins.

The URL hash holds the whole state (`#study=c&state=overlap&sel=pr:22`), so any screenshot can be
reproduced.

Recommendation and open decisions: [RECOMMENDATION.md](RECOMMENDATION.md).

## Files

| Path | What it is |
|---|---|
| `index.html` | Built study page with everything inlined. Generated; do not edit it by hand. |
| `study.src.html` | Page template |
| `tokens.css` | **Token proposal**: night and paper themes, the scenery palette, type, space, pixel scale and motion |
| `src/pixels.js` | **Editable pixel source**: a seeded PRNG, a palette-name pixel buffer, and procedural observatory, refractor, sky, hills, tree and eyepiece drawings, plus the 5×5 data-star glyphs and 9×9 icons. The same code draws to canvas and to SVG. |
| `src/creature.js` | D's sprite and scenery: the dusk sky, hill and creature with pose parameters (eyes, look, lean, settle, lift, door, lantern, note, chart, smoke) |
| `src/living.js` | D's engine: sky layout, habit loop, listening sequence, hand-inked edges, hover gaze, replay shooting stars and the honest "new look" note |
| `src/ornament.js` | Round 4 corner ornament: the painted tortoise frames with posture, blink, breathing, glow and the dome reveal; also the status-card face |
| `src/data.js` | Synthetic data shaped like `observstory.scene/v1` (zones, groups, nodes, edges, attention), the replay events and a deterministic `replayAt(pos)` |
| `src/study.js`, `src/study.css` | Working interface: navigation, board/field/atlas maps, list, replay, attention rail, inspector, keyboard |
| `build.mjs` | `node design/observatory/build.mjs` builds `index.html`, `assets/*.svg` and `assets/tokens.json`. It is deterministic: two runs give byte-identical output. |
| `assets/` | Exported SVGs: the observatory in every lane and window state, the refractor at each lane, the courtyard, the horizon strip, the eyepiece, the star glyphs and the icons. Also `tokens.json`. |
| `shoot.sh` | Rebuilds the page and regenerates `screenshots/` with headless Chromium, with motion off |
| `screenshots/` | Desktop (1440) and mobile (390) captures of all three directions in every state |

## D · round 4 (final design shell): brutalist workbench with the painted ornament

- Live page: https://claude.ai/artifact/PQXy4HJn6C4hdbxhZzPNsY (private to the owner until shared).
  This is the same build as `index.html`.
- **Ornament:** the owner's painted observatory tortoise, pixelated to 320×179 (see
  `creature/`), sits top-left as a quiet ornament, like Weavr's sidebar character. It carries
  posture only, and the page always says it in words:
  - **resting:** dome closed, sleepy eyes;
  - **up:** dome open, telescope out, lantern lit;
  - **travelling:** a slow plod while replay plays.
  - Blinking, breathing, glow and flicker stop under reduced motion. The same frames give the
    status-card face.
  - Source: `src/ornament.js`. The frames are inlined by `build.mjs` from `creature/frames/`.
- **Brutalist shell:**
  - concrete night tokens (`:root[data-direction="d"]` in `tokens.css`);
  - recessed slabs, 2px joints, square corners and one chamfer (the status card);
  - a cantilevered tab bar with the current tab cut into it;
  - condensed uppercase labels (Barlow Condensed from Google Fonts, falling back to system
    condensed faces);
  - **sage** for selection and focus, **lamp amber** for lit lanes, and **signal orange**
    reserved for "needs a conversation".
- **Ribbon-window lane strip** on Overview: one recessed slot per lane.
  - Lit means work is in flight; an orange frame means it takes part in an overlap or wait.
  - Each slot is labelled in text and scrolls to its lane.
- All four tabs (Overview, Sky, List, Replay) use the shell. The Sky tab keeps its own dusk sky
  chart.
- The round-3 low-fi turtle (`critter.js`) is removed. The `turtle()` drawing in `creature.js`
  remains only for the exported comparison assets.

## D · round 3: a clean workbench, and the walking observatory in the corner

Owner feedback on round 2: the living scene is lovely, but it is ornamental. The real UI must stay
very clean and overview-first, aligned with Weavr's shell. The creature should be *more* alive: a
walking house that lies down and is an observatory, then stands up. It should still be low-fi
pixel art.

- **Default view = Overview**, a clean dark workbench in Weavr's density:
  - large top tabs (Overview, Sky, List, Replay);
  - a status card with a small portrait, e.g. "The observatory is up · 2 things may need a
    conversation";
  - a "Needs a conversation" list with arrows;
  - the declared **mission strip** (gates passed, in progress or not started, plus a NOW marker),
    carried over from today's Project Map;
  - the numbered **lane board** (01 Intent … 04 Ship);
  - a right column with the inspector, collection, legend and a decorative pixel field;
  - no ornament in the reading path.
- **The walking observatory** sits in the sidebar corner, where Weavr's character sits. It is a
  turtle whose shell is the copper dome. Its posture is the single state it carries, always also
  in words:
  - **lying down** (legs tucked, head in: just a building): nothing needs a conversation;
  - **standing** (legs out, head out, lantern lit): an overlap or waiting signal exists;
  - **walking**: replay is playing. When paused it stands at that point in history.
- **The telescope** still turns to the lane of the selection or the replay event.
- **Decorative habits:** breathing while lying, blinking, a peek, and a greeting when clicked.
  All of them stop with reduced motion.
- **Sky** is now a tab. It shows the same star chart, without its own creature; the one in the
  corner does the watching.
- **"Ask for a new look"** lives in the snapshot card and explains why the static page can't
  start a collection.
- **Pixel style:** 6× in the sidebar (4× on mobile), flat 2–3-tone materials, the same dusk
  palette. Editable in `src/creature.js` (`turtle()`) and `src/critter.js` (posture engine,
  portrait). Exported poses: `assets/walking-observatory-*.svg`.

## D2 · Living observatory (round 2, kept as the Sky tab's engine)

After the first round the owner asked for warmth: *the observatory should be the creature*. It is
an old, gentle caretaker whose way of understanding the world is to watch the repository, collect
its small events and draw connections between them. Direction D does this while keeping A–C's
architecture and honesty laws.

- **Look:** a dusk sky (indigo to violet), warm cream stars, mossy stone and an aged, patched
  copper dome. The telescope is the snout, the attic windows read as eyes only through their
  light, the foundation folds into tucked paws, and there is a fern and an amber side door. No
  laser grids, holograms, particle streams or red alarms.
- **The scene is the map.** The sky above the creature is the project chart, with stable lane
  regions, area clusters on paper tags, and work items as 5×5 stars. The list, rail and
  inspector stay crisp HTML. Paper tags carry the readable labels on the sky.
- **Habits** (see the behaviour law table on the page and in `src/living.js`):
  - *Listens before it looks:* the door brightens, the dome lifts, then the telescope turns.
  - *Has weight:* it leans against the turn and hesitates once halfway.
  - *Draws by hand:* a relation is inked once, when it first appears.
  - *Comfortable at rest:* eyes closed, breathing, a moth, a chart peeking out of the hatch.
- **Interactions:**
  - Hovering or focusing a star shares its gaze, and a paper label appears.
  - Selecting opens the inspector.
  - Replay sends a shooting star per commit, which lands as a lasting point in its area.
    Removals stay as hollow points.
  - Clicking the building gets a single acknowledgement (a wide-eyed look and a chimney puff).
  - **"Ask for a new look"** answers honestly. It shows when the snapshot was taken and says
    that a new look happens when the GitHub Action runs, which this page cannot start. Nothing
    pretends to scan.
- **Colour roles in D:**
  - The amber lamp is ambient: "someone is home".
  - The copper is scenery.
  - The attention accent becomes a brighter **signal orange**, used only for the lantern under
    the telescope, overlap lines and attention centres.
  - Selection stays cool blue.
- **Pixel scale:** one picture at one integer scale, 4× on desktop and 3× on small screens. On
  small screens the sky scrolls sideways instead of shrinking.

Editable source: `src/creature.js` (sprite, sky, hill, poses) and `src/living.js` (habits and the
data layer). Exported poses: `assets/living-*.svg`.

## The laws this study proposes

1. **Every meaningful mark leads to evidence.** Each data star, row, connector and attention
   entry can be selected, and selecting it opens the inspector with its evidence and the rule
   that produced it.
2. **Scenery is never data, and data is never scenery.** Decorative stars are 1 art pixel, dim
   (`--decor` / `--px-star-*`), not focusable, and kept away from labels and clusters. Data stars
   are 5×5 glyphs with a label, a list equivalent and an `aria-label`.
3. **The warm window is the accent.** The observatory window is lit (`--accent`) only when the
   loaded snapshot holds an overlap or waiting signal. This is the existing "one accent =
   conversation needed" rule given a place in the picture. It is unlit when things are quiet and
   during replay, because coordination is not reconstructed from commit history. A lit window
   means "lit" and nothing more: the number of signals never changes its brightness or size.
4. **The telescope points; it never scans.** Its azimuth comes from the **lane** of the current
   selection, or of the current replay event. Lane azimuths are fixed: Intent −50°, Build −18°,
   Verify +18°, Ship +50°. With nothing selected it is parked and the shutter is closed. There is
   no scanning or "collecting" animation, because a static snapshot is not live collection. A
   live state would need real live data before it could earn one.
5. **Text always states what the picture shows.** The status bar names the snapshot time and
   says "not live", gives the telescope's target, and gives the window's reason. The courtyard
   caption and the instrument readout repeat these.
6. **Absent data is not zero.** Coverage is listed per source. A skipped source shows as
   "skipped" in the accent colour with the reason, and unavailable replay feeds are listed and
   disabled with their reason.

## State → visual mapping

| Mark | Means | Also in text | Notes |
|---|---|---|---|
| Lit window | ≥1 overlap or waiting signal | status bar, Needs attention | unlit in quiet and in replay |
| Dome slit and telescope azimuth | lane of the selection | status bar "Telescope pointing at …" | parked with the shutter closed when nothing is selected |
| Telescope in replay | lane of the current event | event card, area table | moves only when the position changes |
| Star glyph shape | status: cross = in flight, broken cross = draft, small = stale, ring = landed | status word, aria-label | readable in greyscale |
| Accent centre pixel | item is part of an attention signal | pills such as "overlap · #22" | never brightness or size |
| Dashed accent line | overlap (derived), undirected | legend; label when ≤6 connectors | confidence shown as ●◐○ plus a word |
| Solid wire with arrow | waits on (heuristic or declared), directed | legend, label | differs from overlap in shape, not only colour |
| Opacity 62% | stale or draft (receding) | status word | — |
| Opacity 35% | unrelated while something is selected | — | nothing disappears |
| 1px dim star | nothing | — | decoration only |

## Tokens, type and icons

- **Colour:** see `tokens.css`. The UI tokens keep the existing semantics: `--mark` for neutral
  work, `--accent` for conversation, `--select` for selection and focus, `--wire` for waiting.
  The `--px-*` scenery palette is a **closed set** of 22 colours that only pixel art uses.
  Pixel art borrows four UI colours, and only when it draws data or state: `mark`, `mark-dim`
  and `select` for data glyphs (in the eyepiece), and `accent` for the lit window.
- **Type:** the system sans for everything readable and monospace for refs, paths, SHAs, ages
  and coordinates. Sizes are 11/12/13/15. Lane names use small caps with 0.08em tracking. There
  is no pixel font anywhere in readable text.
- **Pixel scale:** integers only. That is 3× on desktop and 2× under 768px; the atlas glyphs use
  3 CSS px per art pixel. Canvases are sized to whole art pixels and never stretched.
- **Icons:** 9×9, one colour, drawn on the same grid as the scenery. An icon always sits next
  to a word; it never stands alone as a label.

## Motion

- Decorative motion is limited to a slow re-seed of horizon stars in study A, every 1.8s. It
  carries no information and stops under `prefers-reduced-motion` or the Motion toggle.
- Telescope turns step through 5° increments over about 70ms per step. With reduced motion the
  telescope jumps straight to its target.
- Replay playback is driven by the user (play/pause, step, scrub, 1×/2×/4×), so it is not
  decoration. CSS transitions are disabled under reduced motion.

## Accessibility (as built in the study)

- Every interactive element is a `<button>` or a focusable SVG group with `role="button"`,
  `aria-pressed` and a descriptive `aria-label`.
- In the map or list, ↑/↓ move between items, Enter/Space select, and Esc closes the inspector
  and **returns focus** to the item that opened it.
- The list view is the full equivalent of each map.
- Below 768px the inspector becomes a bottom sheet and the atlas scrolls sideways at a readable
  size instead of shrinking.
- All source strings are inserted with `textContent`; there is no `innerHTML` for data.

## Handoff: fitting this into the typed frontend

None of this needs a producer or schema change.

- **Data:** every field the study reads exists in `scene/v1`: zone order, group path, node
  `status`, `age_hours` and `also_touches`, edge `type`, `basis`, `confidence`, `directed`,
  `files` and `rule` (via `details`), plus attention, coordination and `source.degraded`. The
  per-source coverage list would come from `snapshot.provenance` through the adapter.
  `data.js` is a stand-in for the adapter's output.
- **Pure view functions:** `target()` (telescope azimuth and shutter) and `windowLit()` become
  pure functions of *(validated scene, UI selection, replay position)* in the frontend, and are
  unit-testable without a browser.
- **Pixels:** `src/pixels.js` ports directly to a typed module (`PixelBuffer`, the drawing
  functions, `toCanvas`, `toSVG`). React components (`<Courtyard>`, `<Refractor>`, `<Eyepiece>`,
  `<StarGlyph>`) wrap a canvas and redraw when their props change. The exported SVGs are for
  documentation and static fallbacks; the components should keep drawing procedurally so that
  lane azimuths and window state stay data-driven.
- **Tokens:** `assets/tokens.json` mirrors `tokens.css` for TS consumption. Pick one of the two
  as the source when the rewrite starts. The study treats the CSS as the source.
- **Replay:** `replayAt(pos)` shows the contract: a baseline plus first-parent events, rebuilt
  from scratch at each position. It never interpolates and never invents PR state. The real
  feed would come from the existing `build_replay.py` output in Open Presence.

## Verified / not verified

Verified:
- The build is deterministic (two runs give identical hashes for `index.html` and `assets/*`).
- Every screenshot in `screenshots/` was generated with `shoot.sh` and looked at.
- In a browser: keyboard navigation (↑/↓, Enter, Esc with focus return), replay play/scrub,
  telescope readout following selection, and no console errors.

Not verified:
- No screen-reader pass.
- No automated contrast audit. The token comments give estimated ratios only.
- The 768px tablet layout was not captured.
- The paper theme was checked on the atlas only.
- Not tested in Safari or Firefox.
