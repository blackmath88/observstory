# System boundary

Each layer is listed with what it owns and what it must not do.

```text
┌──────────────────────── GitHub (source of truth) ────────────────────────┐
│ commits · PRs · PR files · PR commits · branches · compare · issues      │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │  1. INGESTION (impure, rate-limited)
                                   ▼
                     observations.json  (normalised facts)
                                   │  2. DERIVATION (pure, deterministic)
                                   │  3. HEURISTICS  (pure, thresholded, labelled)
                                   │  4. CONFIG      (lanes, thresholds, ignore)
                                   ▼
                       snapshot.json  (typed project state v1)
                        │                        │
            5. UI (projection)        6. API / agent surface (projection)
            index.html radar          `observstory query …` → JSON
                                      (MCP adapter later, same queries)
```

| Layer | Owns | Must not |
|---|---|---|
| **1. GitHub ingestion** (`collect.py`, `github.py`) | API calls, pagination, rate-limit budget, normalising into `observations` | Compute relations; call models; store file contents |
| **2. Deterministic derivation** (`derive.py`) | Areas from paths; lane assignment; work items; activity timestamps; file-level overlap; stacked-PR waiting | Use thresholds without echoing them; depend on the clock except via `now`, which is passed in |
| **3. Heuristics** (`signals.py`) | Area overlap, staleness, burst detection, declared-dependency text parsing | Present output without `basis`, `confidence`, `evidence` |
| **4. Human-authored configuration** (`observstory.config.json`) | Lane names and paths, thresholds, ignore globs, area depth | Be *required*; zero-config must work |
| **5. UI** | Visual projection of the snapshot; evidence links | Compute anything not in the snapshot (no hidden logic in the renderer) |
| **6. API / MCP** | Query functions over the snapshot | Crawl GitHub on its own; hold state the UI can't see |
| **(7) Optional LLM interpretation** | *Nothing in v1* | n/a |

## LLM use: justification test

An LLM is only allowed where deterministic code *can't* do the job **and** the output is kept as
a clearly labelled interpretation with evidence attached. For each v1 need:

| Need | Deterministic enough? | Verdict |
|---|---|---|
| Which areas a change touches | Yes: paths | No LLM |
| Whether two changes overlap | Yes at path level | No LLM |
| Whether two changes *conflict in design* | No | **Not emitted at all in v1.** An LLM verdict here would be inference presented as fact (R3). Candidate for v2+ as an *opt-in, labelled* annotation |
| Summarising a PR | Title and body already exist | No LLM; show the author's words |
| Proposing lanes for an unconfigured repo | Top-level directories work | No LLM; possible v2 "suggest config" helper whose output is a config file for humans to review |
| Detecting duplicate intent from titles | Token overlap is crude but explainable | Deferred; no LLM |

Conclusion: **v1 has no LLM dependency.** This keeps the action free, deterministic, testable
and private.
