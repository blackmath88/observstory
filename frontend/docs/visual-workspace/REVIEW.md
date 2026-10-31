# Observatory visual workspace — review evidence

Implementation base: `af5b2d725301f46ee1796b3d215fd90694fb8c12`, branch
`feat/frontend-tanstack-start`. Isolated branch: `feat/observatory-visual-workspace`.
Producer PR targets the existing frontend branch; it does not replace Claude's memory work.
Consumer declaration initially committed at `8acdf7b` in Open Presence. The consumer PR pins
the exact producer commit containing this release. No merge or deployment was performed.

## Observed inputs

Fetched hosted Open Presence knowledge, snapshot, scene and event schedule on 31 October 2026.
Knowledge: resolved commit `0281da86fd4c07739d1dea2800ce514b29b7c094`, generated
`2026-10-31T16:13:40Z`, complete=true, zero diagnostics. Snapshot: same trigger commit,
generated `2026-10-31T16:13:14Z`; partial collection: PR #8 has 100+ files and only the first
100 are used. The local consumer main was `220dd95` at checkout. The preview combines those
hosted observations with the new declaration at `8acdf7b`; the mismatch warning is intentional.
No lifecycle, owner, progress, dates, human approval or resume content was invented for the
consumer. Its only conceptual relationship is the explicitly optional PDF module supporting
Human Signal. Source links remain inspectable.

## Verification

- Frontend typecheck and lint pass (existing Biome configuration deprecation notice).
- 28 Vitest tests pass, including opt-in validation of the four real hosted inputs.
- 151 Python tests pass, including public workspace Git-object projection and all five
  release-packaging checks. Dirty working-tree content cannot replace the declared revision.
- `npm run release` generates the checked-in release; release contains no project data.
- Nine Playwright checks pass at 390, 768 and 1440px under project subpaths: missing and invalid
  inputs, keyboard navigation, reduced motion, expansion persistence, drawer Escape/focus,
  Board selection and direct-link reload.
- Real consumer preview inspected at the same three widths: no page horizontal overflow or
  uncaught browser exceptions. Overview, Board and drawer screenshots are alongside this file.
- `synthetic-workspace.png` is explicitly synthetic: paused branch, stopping point, next action,
  parent relationship, proposed concept, undated research and milestone target. These fixtures
  are never copied to the producer release or consumer publication.

## Preview and limits

Run `npm ci && npm run build` in `frontend`, then `node tests/e2e/serve.mjs` for fixture views at
`http://localhost:4319/workspace/`. For consumer input, copy `release/` to a folder beside the
consumer's `data/` and serve it with `python3 -m http.server 4318 --directory /path/to/preview`.
A runnable captured-data ZIP accompanies the task handoff; it needs no Node or API credentials.

The UI is read-only except local expansion and view/selection navigation. Resume authoring,
status updates, a full Map, multi-level graph editing and deployment are outside this slice.
Timeline marks represent only available observations or explicit planned targets; the source
snapshot does not provide a complete event ledger. Optional companion views remain linked only
when present. No NUC runtime, paid model or backend service was required. Physical touch devices,
screen readers, Safari and Firefox were not tested. No automated accessibility certification is
claimed. Consumer state should be refreshed by its Action after review, not represented by this
captured preview as current progress.


## NUC increment — 31 October, record navigation

Stack base: PR #24 at `84c3c0a4e1d870f0aa56e47db9ee59fcfd1ee844`.
This increment targets `feat/observatory-visual-workspace`; #24 still targets
`feat/frontend-tanstack-start` at `af5b2d725301f46ee1796b3d215fd90694fb8c12`.
Self-reviewed only; draft delivery does not accept source declarations.

Overview and Board now share category filters, text search and matching counts. Categories
use existing record kinds only (research, concept, plan, implementation, other context).
They do not create workstream membership or promote document/artifact status to lifecycle.
Search includes title, context, basis, source titles and declared resume/attention text.
Hash parameters `focus` and `q` preserve filters with view and selection through reload and
browser history. No results has a clear reset. Overview automatically reveals matching
nested members with their existing ancestor chain, without changing saved expansion choices.
Unfiltered expansion works at every membership level. Nested identity indentation keeps the
timeline columns aligned. The shared drawer restores record focus even after a reload.

### Current input evidence

Public Open Presence inputs fetched directly from its Pages `data/` directory during this
increment: snapshot `2026-10-31T18:38:42Z`, knowledge `2026-10-31T18:39:07Z`, scene
`2026-10-31T18:38:42Z`. Snapshot, complete knowledge and workspace all cite
`b1af0128bfd48e5d6e8b8579f790858636b7d087`. The supplied runtime capture at `77b1845`
was older. This captured preview is static evidence, not a statement about current progress.
The projection contains 39 records: research 7, concepts 2, planning 4, implementation 10,
other context 16. Sources, undeclared lifecycle and missing dates remain visible.
Raw consumer inputs stay outside the repository.

### Checks and local consumption

- `npm run typecheck`, `npm run lint`: pass (existing Biome configuration deprecation notice).
- `OBSERVSTORY_LIVE_DATA=/tmp/observatory-20261031-live/data npm test`: 30 tests pass,
  including real published source contract validation.
- `npm run release`: production frontend rebuilt into `frontend/release/`, with no project data.
- `python -m unittest discover -s tests -p test_frontend_release.py`: five packaging checks pass.
- `OBSERVSTORY_PREBUILT=1 OBSERVSTORY_LIVE_DATA=/tmp/observatory-20261031-live/data npm run e2e -- --grep 'category and search|nested membership|real Open Presence'`:
  nine focused Chromium checks pass at 390, 768 and 1440px against the actual prebuilt release.
  Includes keyboard filter selection, search, Overview/Board consistency, selection/reload,
  drawer Escape/focus, empty results/reset, deep membership, saved expansion, real source
  links, timeline alignment, page overflow and browser errors.
- Initial broader run: 15 passed, three copies of the same reload-focus failure. One focused
  repair added a record-based focus fallback; the nine relevant release checks above passed.
- `navigation-1440.png` and `navigation-390.png` show the captured real implementation view.

The local test host binds only `127.0.0.1` and is owned/stopped by Playwright. `OBSERVSTORY_PREBUILT=1`
selects `release/`; `OBSERVSTORY_LIVE_DATA` supplies an external data directory at `/live/`.
A standalone copy is also available locally at `/tmp/observatory-20261031-live/preview/`.
The coordinator must update the consumer pin separately; no consumer source, deployment,
provider/auth, memory reducer, System Map or accepted decision was changed.
Next increment: make selected records easier to locate in long workstreams, including
containing-workstream breadcrumbs in the shared detail drawer. No new dates/owners needed.
