# Recommendation: Observatory pixel direction

Status: **provisional.** The owner's visual templates have not arrived yet. This is a leaning
with reasons. Final selection, palette and composition stay open until the templates have been
reviewed against these studies.

## Short version (round 4, final design shell)

Recommended: **D as now built** (https://claude.ai/artifact/PQXy4HJn6C4hdbxhZzPNsY):
- a clean brutalist workbench as the default;
- the owner's painted observatory tortoise as a small corner ornament;
- the ribbon-window lane strip as the at-a-glance summary.

Visual selection is settled. The palette and tokens are in `tokens.css` (direction D).

Still open, outside this design slice:
- the real typed frontend (`OBSERVATORY-REWRITE.md` slices 0–3, with the TanStack starter
  still to be identified);
- walk-cycle and telescope-aim frames, if the ornament should do more than rest, stand and plod;
- the trigger path for "Ask for a new look".

## Short version (round 3)

Recommended: **D as now built.** It is a clean, Weavr-aligned workbench as the default, with the
walking observatory as the identity in the sidebar corner and the star-chart sky as a tab. This
keeps the creature's warmth while the overview stays the product.

Why posture is the right single mapping: lying, standing and walking are three states anyone
reads instantly from a small sprite. They match the three things a visitor most needs to know:
everything is calm, something needs a conversation, or you are looking at history. And they never
compete with the data for attention.

For the first implementation, still follow the owner's "smallest version". In this layout that
means:
- the sprite with lying, standing and walking poses;
- telescope aim;
- the status card;
- the overview cards;
- the Sky tab, as an optional extra.

## Round 2 (kept for the record)

Recommended: **D · Living observatory.** It is the synthesis the round-1 recommendation pointed
towards, now with the warmth the owner asked for:
- C's atlas becomes the creature's sky;
- A's courtyard becomes the creature itself;
- B's "telescope turns to what you select" becomes shared gaze.

Keep A–C in the page for comparison only.

Trade-offs specific to D:
- It has the most build effort. Scope the first implementation to the owner's "smallest
  version": the silhouette, the idle loop, aiming at a selection, one incoming-event animation
  (replay shooting star), one inking animation, and the information panel. Everything else is
  optional.
- The scene takes about 600px of height on desktop. The list view must stay a first-class
  equivalent, and it does in the study.
- Charm can outrun evidence. Adopt the behaviour-law table as a review checklist: every habit
  maps to typed state or is declared decoration, and its meaning is also said in text.

### Round 1 (kept for the record)

Recommended then: **C · Star atlas as the map, framed by A · Courtyard as the persistent identity.**
Keep B's interaction law (*the telescope turns to what you select*), but put it in the courtyard
dome rather than in a separate instrument panel.

| | A · Courtyard | B · Instrument | C · Atlas |
|---|---|---|---|
| Reading the work | ★★★ board, as today | ★★ recency field is fast for "what moved", but harder for "where" | ★★ needs the list as an equal partner on small screens |
| Observatory identity | ★★ ambient | ★★ strong, but busy in the sidebar | ★★★ the map *is* the observatory's work |
| Art ↔ state coupling | ★★ window and dome turn | ★★★ aim → eyepiece | ★★ cartouche dome mirrors state |
| Risk of decoration creep | low | medium (eyepiece duplicates the inspector) | medium (decorative stars near data) |
| Build cost on top of slices 2–3 | low | medium | medium–high (layout and labels) |
| Replay fit | table | table | **plots onto the same chart** |

## Why this combination

1. **The atlas earns its metaphor.** Mapping a field of stars is literally what the product
   does with a project. Stable lane regions and area clusters follow the scene-grammar rule that
   order carries meaning and placement never moves because of activity. Replay reuses the same
   chart, so learning one picture covers two features.
2. **The courtyard carries the feeling without crowding the data.** The small dome, the warm
   window and the quiet sky sit in the sidebar's empty space. The working surface stays crisp.
   This is the "calm composition, warm light in a cool world" the owner described.
3. **The window and telescope laws work in every direction.** A lit window means a conversation
   is needed. The telescope points at the lane of what you selected. Both are cheap, honest,
   stated in text, and never imply live collection.
4. **B's eyepiece is the first thing to cut.** It is the most charming element and also the most
   redundant one, because it repeats inspector facts. Keep it as a later enhancement if the
   inspector header looks bare.

## Trade-offs accepted

- The atlas needs more layout work: label collision, cluster sizing for 1 to 40 areas, and
  sideways scrolling on mobile. The study handles 7 areas. Large projects need a tested packing
  rule, or a fallback to the board above a threshold.
- The night theme is the study default. The existing Project Map is light-first, so this is a
  product decision (see below), not something the study settles.
- Pixel art at 3× in a 248px sidebar is small. The dome reads well, but the telescope tube is
  only a few art pixels. Templates may call for a larger scene band.

## New decisions raised by D

1. **Scan button.** The owner's sketch includes "ring a bell → it scans". A static Pages site
   cannot start the Action without a browser GitHub token, which the rewrite plan rules out. The
   study's bell therefore explains instead of scanning. A real scan needs a decision on a
   trigger path, for example a `workflow_dispatch` link that opens GitHub's own UI.
2. **Milestone comets and CI lamps.** The sketch maps releases to comets and failing tests to a
   lamp. Observstory does not observe releases or CI today (CI state is a v3 candidate), so
   neither is drawn. Adding them is a collector scope change, not a design change.
3. **Attention colour.** In D the accent shifts to signal orange `#ff9550` to stay distinct from
   the amber lamp and the copper dome. The existing UI language keeps `#f09a45`/`#b4530a`.
   Choose one.
4. **Sound.** The sketch mentions small mechanism sounds. None are in the study. Sound would need
   to be opt-in and carry no information.

## Decisions awaiting owner templates

1. **Palette:** the night tones (blue-grey charcoal), the warmth of the window, and whether the
   accent stays `#f09a45`/`#b4530a` or follows the templates.
2. **Default theme:** night-first (this study), paper-first (the existing map), or follow the
   system setting.
3. **Composition:** where the scene lives (sidebar foot, a top band, or both) and how big it is.
   The study uses a sidebar foot and a 36px horizon.
4. **Art style:** pixel scale (2×, 3× or 4×), outline versus no-outline sprites, the level of
   dithering, and whether trees and landscape belong at all.
5. **Telescope type:** a dome with an internal telescope (A/C) or a visible refractor (B).
6. **Atlas grammar:** rectangular lane regions (study) or irregular constellation boundaries.
   Also whether graticule lines stay.
7. **Licensing:** the provided reference images are not assumed licensed for shipping. Every
   asset here is drawn procedurally from `src/pixels.js` and can be redrawn to match the
   templates.
8. **Starter:** the "TanStack starter v1" is still unidentified (see the plan). This study does
   not depend on it.

## Not decided here (and why)

- Whether B's coordinate addresses (`BLD 2·1`) should become a shared short reference for people
  and agents. It is attractive, but it is a vocabulary change that touches agent queries. That
  is a separate decision, and it is not part of a visual study.
- How a durable Observatory state-history store would be designed. The replay view only shows
  that feed as unavailable.
