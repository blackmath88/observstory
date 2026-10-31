# Frontend migration checklist

Tracks `OBSERVATORY-REWRITE.md` against the typed frontend in `frontend/`. The vision: the
existing Project Map, polished toward GitHub's cleanliness (owner, 31 Oct 2026). Stack and
serving: ADR-038.

## Slice 0: baseline and foundation (done on `feat/frontend-tanstack-start`)
- [x] Baseline: `python3 -m unittest discover -s tests` passes 143 tests on `f91e9eb`; unchanged by this branch.
- [x] Starter identified: `blackmath88/start-kit` ADR 0001 (a build brief, not yet implemented upstream); followed at `3907ab5ab429`.
- [x] Static strategy proven: SPA shell plus relative assets plus hash routing. Verified under a project subpath with live consumer data (locally, not committed).
- [x] ADR-038 recorded.

## Slice 1/2: shell and data boundary (first pass done)
- [x] One adapter validates snapshot, scene and knowledge against `schema/*.json`; event schedule v0 identity-only.
- [x] Per-input states: ok, missing, unsupported, invalid, unreadable, unreachable. Required inputs block activity; optional ones degrade per panel.
- [x] Repository header, tabs, freshness from the snapshot's timestamp (stale after 2 h), static/not-live label.
- [x] Light and dark themes; 390 px and 1440 px checked; keyboard-reachable tabs.
- [ ] Event clock and project knowledge panels (HACKATHON-PROJECT-VIEW.md).

## Slice 3: map, list and coordination (next)
- [ ] Mission strip with full labels (no truncation), declared versus observed, "No confirmed checkpoints yet".
- [ ] Lane board: active lanes as GitHub-style boxes; quiet lanes collapsed to one line.
- [ ] Work-item rows: state icon, title, #ref, authors · time · reviewer · areas, labels.
- [ ] Inspector with evidence; focus returns to its trigger; a headless library chosen (Radix or Base UI).
- [ ] List view equivalent to the map.

## Slice 4: replay
- [ ] Repository file history only; separate selected time from the present deadline.

## Slice 5: verification and opt-in integration
- [ ] Decide how the Action ships `dist/client` (prebuilt in the repo vs built in CI).
- [ ] Action input to choose the frontend; the old renderer stays selectable.
- [ ] Contrast audit, reduced motion, untrusted-text review, supported data sizes.
