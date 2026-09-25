# Design language: Project Map

"Observatory, not office" still applies (see [ui-language.md](../development/ui-language.md)). For
the map, the reference is a **macOS-light architectural infographic**: calm, spacious and
editorial, generated from project state instead of drawn by hand.

## Rules

1. **One accent, reserved.** Orange (`--accent`) means "a conversation is needed": overlap connectors, the overlap pill, attention entries, refs of work in a relationship. Selection uses the system blue (`--select`), never orange.
2. **Tints mean "a lane", nothing more.** Six very low-chroma tints (sand, sage, mist, lilac, clay, stone) cycle by lane order. They separate lanes; they don't encode status. Tints restart for 7+ lanes.
3. **Cards are near-white, with 1px borders and 10–12px radii.** No shadows on the map; the inspector alone gets a whisper of shadow because it floats.
4. **Type:** the system sans (SF on macOS) for everything readable; monospace only for refs, paths, SHAs and ages. Lane names are small caps with letter spacing. There are no big numbers anywhere: the header status is one line of text.
5. **Receding, not hiding.** Stale and landed work fades to about 60% opacity. When something is selected, unrelated rows dim to 35%. Nothing disappears on selection.
6. **Connectors are thin (1.3–1.6px), with confidence in the dash, not in colour.** Labels ("overlap", "waits on") appear once per area and relationship kind, and only when there are six or fewer connectors on the page.
7. **Progressive disclosure.** The map shows *that* something is related. The inspector shows *why*, with evidence. The rule name and parameters are the last line, for anyone who wants to check the logic.
8. **Words stay neutral.** Subjects are work items and areas. There are no scores, rankings or health grades, and no per-person numbers.
9. **Dark mode** has its own token values (light remains the primary target).

## Tokens (light)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#f6f5f1` | warm off-white page |
| `--surface` | `#fdfcfa` | cards, inspector |
| `--ink` / `--ink2` / `--ink3` | `#1d1d1f` / `#515154` / `#8a8a8e` | text hierarchy |
| `--hair` / `--hair2` | `#e4e2dc` / `#d6d4cd` | 1px borders, flow arrows |
| `--accent` / `--accent-t` | `#b4530a` / `#fbefe4` | coordination only |
| `--select` | `#0a66d6` | selection and focus |
| `--wire` | `#6e6e73` | waiting connectors |
| `--t0`…`--t5` | `#f1efe8` `#ecf1ec` `#ecf0f5` `#f2eef4` `#f4efe7` `#eef1f0` | lane tints |
