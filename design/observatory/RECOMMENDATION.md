# Recommendation: Observatory pixel direction

Status: **provisional.** The owner's visual templates have not arrived yet. This is a leaning
with reasons. Final selection, palette and composition stay open until the templates have been
reviewed against these studies.

## Short version

Recommended: **C · Star atlas as the map, framed by A · Courtyard as the persistent identity.**
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
