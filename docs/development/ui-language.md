# UI language

**Observatory, not office.** The dashboard should feel like an instrument: calm until
something needs attention, precise in wording, with evidence one click away.

## Vocabulary

| Use | Avoid |
|---|---|
| work item, area, lane, in flight, overlap, open loop, change stream | score, productivity, top contributor, velocity, leaderboard, health grade |
| "2 work items touch src/conversation" | "Sofia and Alice are conflicting" |
| "idle for 5d (no pull request)" | "abandoned", "dead", "slow" |
| derived / heuristic / declared | "AI insight", "smart detection" |

Subjects of sentences are **areas and work items**. People appear as authors of evidence, listed
alphabetically.

## Visual system

| Token | Role | Light | Dark |
|---|---|---|---|
| `--bg` / `--panel` | Paper / instrument face | `#f3f2ee` / `#fbfaf7` | `#0e1113` / `#14191c` |
| `--ink` / `--muted` / `--faint` | Text hierarchy | `#1c1d1f` / `#66686b` / `#a9a8a2` | `#e5e3dd` / `#8d9295` / `#4a5155` |
| `--mark` | Neutral data mark (work in flight) | `#2f5467` | `#8db5c9` |
| `--accent` | **Reserved for coordination signals only** | `#b4530a` | `#f09a45` |

Rules:
1. **One accent.** Only something that needs a human conversation gets colour. Everything else is
   ink or slate. No traffic-light red, amber and green.
2. **Confidence is shape, not colour.** On the radar: solid, dashed or dotted rings. In lists:
   ●, ◐, ○, plus the word in the rule line. This works in greyscale and for colour-blind readers.
3. **Monospace for evidence** (ids, paths, shas, counts). Sans-serif for prose.
4. **Recency is distance.** Radar centre = now; the outer ring = the edge of the window. Things
   that just moved sit close to the observer.
5. **Numbers describe the project.** The readout row counts work items, areas, overlaps, open
   loops and commits. It never shows a number per person.
6. **Evidence is one click away.** Each signal is a `<details>` element whose body lists
   evidence (work item, file, timestamp, text) with links, then the rule name and its parameters.
7. **Quiet empty states.** "Nothing here." is a good outcome, not a failure.
8. **Dark mode** is its own set of token values under `prefers-color-scheme`, not an inversion.

## Radar anatomy

```text
           INTENT
        ·   48h ring (window edge)
     ·    ·   36h
   ·   ◉ src/conversation     ◉ = filled mark (in-flight) + accent ring (overlap)
  ·  ○    · now ·            ○ = hollow mark (recent commits only)
   ·    ● src/search         ● size = number of in-flight work items (capped at 4)
BUILD ────────── VERIFY      sectors = lanes, labelled at the rim
```
