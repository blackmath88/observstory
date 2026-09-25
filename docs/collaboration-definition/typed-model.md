# Typed model: collaboration state

Schema: [`schema/coordination-v1.json`](../../schema/coordination-v1.json). The file is
`.observstory/coordination.json` in the observed repository.

## Types that earn their place

| Type | Why it exists | Key fields |
|---|---|---|
| **Session** | Where declarations come from: a check-in, with its time and provenance | `id`, `kind` (check-in / review / kickoff), `label`, `at`, `recorded` (false in v1), `open_questions[]` |
| **Gate** | A hard time that changes what's allowed; the only thing that can be *passed* | `id`, `kind` (freeze / submission / demo / checkpoint), `label`, `at`, `areas[]` (freeze scope) |
| **Commitment** | A short named promise with an optional due time and **declared** link targets | `id`, `text`, `owner` (as declared), `due`, `links[]` (`pr` / `branch` / `path` / `url`) |
| **Decision** | A choice that may constrain an area | `id`, `text`, `areas[]` |

Every declaration carries `status` (`proposed` | `declared`) and `source` (the session, the
extractor, the source line), plus `confirmed_by` and `confirmed_at` once declared.

## Rejected types

| Type | Why not |
|---|---|
| OpenQuestion | Useful in the check-in, but it has no observable counterpart in the repository; kept as `Session.open_questions` |
| Plan / Milestone hierarchy | Gates plus commitments cover the 48-hour case; hierarchies need upkeep |
| Transcript | Not stored as state (consent, retention). A short excerpt can live in `source.excerpt` |
| Evidence / Link as top-level types | Links are fields on a commitment. Evidence reuses the existing evidence shape in snapshot cues |
| Task status (todo / doing / done) | Status upkeep is PM bloat; the observed state comes from the repository instead (R5 rejected) |

## Status is never silently promoted
`proposed` items are ignored by reconciliation, the timeline and the map. They exist only so a
check-in can be reviewed (and optionally committed) before confirmation. Only `observstory
checkin confirm --by NAME` sets `declared`.
