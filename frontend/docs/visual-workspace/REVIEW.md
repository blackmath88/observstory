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


## NUC turn 2 — locate a record in its workspace

Continues from `4d107c6cd8b045dce38f2c412712307fd4e25c3c` on the same stacked draft.
The shared drawer now displays published root-to-record containment routes, retaining
multiple memberships and each record's declared/derived/observed basis. Top-level records
say no containing record is published. Relations and filesystem paths never create parents.
Traversal is bounded to 12 routes and 512 visits; omitted/cyclic locations are disclosed.

**Reveal in Overview** closes the drawer, temporarily opens existing ancestors, highlights
and focuses the record, and scrolls it into view. The hash `reveal` parameter preserves this
across reload/history. Search/category and saved expansion stay unchanged. A banner explicitly
qualifies records outside the filters; match counts exclude that temporary exception.
End reveal returns focus to search and restores normal filtered visibility. Switching to Board
ends reveal. Breadcrumb buttons open containing records without losing the drawer's origin;
a direct-linked drawer can close safely after following a breadcrumb.

The captured Open Presence inputs and their limitations remain those recorded above at
`b1af0128bfd48e5d6e8b8579f790858636b7d087`. No source-owned lifecycle, owner, progress or date
was added. Real declared containment (PDF claim ledger → optional module) and derived containment
(observed artifact → area → Repository implementation) were exercised through the actual release.

Checks for this increment:

- Typecheck and lint pass (existing Biome configuration deprecation notice only).
- `npm test`: 32 tests pass, one opt-in live-data test skipped. Three new model tests cover
  outside-filter reveal without changing counts, multiple membership routes/evidence basis,
  unavailable records, cycles and bounded traversal. Earlier live input validation was not
  repeated; real release browser checks below load the same captured inputs.
- `npm run release`: passes; updated `frontend/release/` contains no project data.
- Five Python release-packaging checks pass against the final release.
- Initial focused prebuilt-release browser run: 12 pass at 390, 768 and 1440px. Covers existing
  category/search interaction plus new multiple membership, breadcrumb/direct-link close,
  reveal/reload/history and real declared/derived source navigation.
- Additional focus/highlight checks exposed a Browser Back focus regression (three widths).
  One focused repair distinguishes restoring a reveal from closing a drawer. Final command:
  `OBSERVSTORY_PREBUILT=1 OBSERVSTORY_LIVE_DATA=/tmp/observatory-20261031-live/data npm run e2e -- --grep 'drawer reveal|real Open Presence drawer locations'`:
  **6/6 pass** against the final release, including returning focus to another opened record,
  selected highlight outside filters, direct reload, End reveal, Browser Back state,
  source URLs and no page overflow/browser exceptions in the real-input scenarios.
- `membership-1440.png`, `membership-390.png`, `reveal-1440.png` are captured real-input views.
  Drawer captures were visually inspected on phone and desktop.

Final standalone local release/data copy: `/tmp/observatory-20261031-turn2/preview/`.
Use the loopback serving command above with this directory. The coordinator still owns the
consumer pin update; no consumer, memory reducer, System Map, accepted decision or human review
was edited. Self-reviewed only. No deployment or preview server is left running.

Next concrete increment: a useful timeline range control (recent window / fit evidence), with
hour-level labels where supported, clear out-of-range observations and undated rows retained.
Do not turn the available latest-activity points into a complete event ledger or durations.


## NUC turn 3 — readable, precision-aware timeline

Continues from `f45775c2e163c1b3a097ed2569765f3977cba7d3` on the same stacked draft.
The existing Overview timeline now has Recent window (last six hours / next two hours) and
Fit evidence controls. Fit uses available dates for results and containing records, including
collapsed members. `range=fit` is preserved with filters, view and selection through reload.
UTC axis ticks expose hours for short ranges and calendar dates for long ranges; the full
range remains visible on phones. Summaries count dated/undated records and dates outside the
window. Empty date evidence is explicitly clock-based. A fitted window can omit Now from its
plot and states when the clock is before/after it; moving the clock never refreshes evidence.

Out-of-range observed timestamps retain labelled captions without fake points at plot edges.
Partially visible planned targets use clipped/dashed outlines and explicit captions. Planned
day/month/year targets occupy their whole UTC calendar precision (including the declared end
period), not a guessed instant or observed duration. Milestones keep a ◇ caption, without a
midnight/midday diamond implying an exact time. Points and captions open the same shared
drawer with keyboard access and return focus. Separate caption lines support independent
planned and observed evidence. Raw timestamp strings remain in titles/the detail drawer.

Real inputs remain the captured Open Presence publication at `b1af012`, not refreshed this
turn. The implementation filter contains 10 records (9 dated, 1 undated). Screenshots use a
**controlled browser clock at 2026-10-31T19:30:00Z** for reproducibility, not a live runtime claim.
`timeline-fit-1440.png`, `timeline-fit-390.png`, `timeline-recent-1440.png` show the actual prebuilt
release with real inputs. Desktop/phone fit views were visually inspected. A separate test
clock on 3 November checks old observations outside the recent window; it is not new source data.

Checks:

- Typecheck and lint pass (existing Biome configuration deprecation notice only).
- `npm test`: 37 pass, one opt-in live-data test skipped. Five new timeline model tests cover
  calendar/leap-month precision, invalid dates, out-of-range observations without clamping,
  fit independent of the current clock, unknown dates, independent evidence channels, explicit
  clipping, stable UTC labels and record immutability.
- `npm run release`: final static frontend rebuilt into `frontend/release/`, with no project data.
- Five Python release-packaging checks pass against the final release.
- Initial targeted browser run: six pass (real timeline and prior reveal behavior); three
  synthetic reload tests raced Escape before the drawer mounted. One focused test repair waits
  for the dialog to become visible, then verifies it closes. No product workaround was added.
- Final command: `OBSERVSTORY_PREBUILT=1 OBSERVSTORY_LIVE_DATA=/tmp/observatory-20261031-live/data npm run e2e -- --grep 'timeline preserves|real Open Presence timeline'`:
  **6/6 pass** at 390, 768 and 1440px against the final release. Includes future calendar targets,
  no fabricated milestone/observation points, unknown dates, range persistence through drawer
  reload and Board/Overview, fit/clock separation, marker keyboard activation/focus restoration,
  aligned nested tracks, real old-observation captions without edge points, Fit recovery,
  no real-input browser errors and no page horizontal overflow.

Standalone final release/data copy: `/tmp/observatory-20261031-turn3/preview/` (14 release files
byte-match `frontend/release/`). Serve only with loopback binding. No server is left running.
Self-reviewed only; no consumer source, reducer/System Map, schema, accepted decision or human
review changed. Coordinator report now records consumer pin draft #19 at older producer
`4d107c6`; that pin needs a separate coordinator update to this PR's new exact head.
Next increment: useful Board grouping by record kind versus explicit lifecycle, retaining
Undeclared status and the shared filters/drawer. No task-state inference is needed.


## NUC turn 4 — Board by kind or declared lifecycle

Continues from `4cd35f395e848a3298e9e77553905d28f49ef449` on the same stacked draft.
Board now defaults to parallel record-kind columns: Research, Concepts, Planning,
Implementation and Other context. An explicit By lifecycle control retains the original
source-owned lifecycle view, including Undeclared. Columns omit empty buckets, preserve
source order inside each bucket and never convert document/artifact state into lifecycle.
Cards show original kind, lifecycle, bounded context and unchanged evidence basis.

`group=lifecycle` persists with filters, selection, timeline range and views through reload
and browser history. Named column jump buttons focus their heading; Tab moves into the cards.
Return controls restore focus to the navigator. Desktop keeps locally scrollable columns with
sticky headings; phones stack columns vertically. Single-column results use a responsive grid.
Changing grouping or matching record IDs resets local Board scroll to the first card; selection
and clock updates keep the current position. The same drawer, sources and resume material remain.

Real captured Open Presence data at `b1af012` still projects 39 records: Research 7, Concepts 2,
Planning 4, Implementation 10, Other context 16. **All 39 remain lifecycle undeclared**. Document/artifact states do not populate lifecycle;
separate synthetic regressions exercise completed-document and landed-artifact labels. Screenshot evidence:
`board-kinds-1440.png`, `board-kinds-390.png`, `board-lifecycle-1440.png`. The phone screenshot is
scrolled to the Board controls; no source content or lifecycle was fabricated for the capture.
Desktop kind/lifecycle and phone kind layouts were visually inspected.

Checks:

- Typecheck and lint pass on the final source (existing Biome deprecation notice only).
- `npm test`: 40 pass, one opt-in live-data test skipped. Three new projection tests assert
  exact partition/source order, preserved material and immutability, no document/artifact-to-
  lifecycle inference, explicit status handling, empty results and safe navigation fallback.
- `npm run release`: final production bundle rebuilt and checked in; no project data shipped.
- Five Python release-packaging checks pass against the final release.
- Initial targeted prebuilt-release run: **12/12 pass** at 390/768/1440px. Covers the prior paused
  resume/focus/expansion flow plus new grouping, filters, search, selection/reload, view/range/
  browser history, column jumps, keyboard return, phone stacking and real source links/counts.
- Visual self-review found inherited local scroll could hide the first cards after changing
  grouping. One focused repair compares prior grouping/result IDs and resets only that scroll.
  Final command: `OBSERVSTORY_PREBUILT=1 OBSERVSTORY_LIVE_DATA=/tmp/observatory-20261031-live/data npm run e2e -- --grep 'board grouping|real Open Presence board'`:
  **6/6 pass** on the final prebuilt release at the same three widths, including a new explicit
  top/left reset assertion, drawer focus/history, real 39-record kind/lifecycle partitions,
  source URLs, no real-input browser errors and no page horizontal overflow.

Final local release/data preview: `/tmp/observatory-20261031-turn4/preview/`; all 14 release
files byte-match `frontend/release/`. No preview server remains running. Consumer draft #19's
producer pin was reported by the coordinator as `f45775c`; the coordinator owns its next pin
update to this PR's exact new head. No consumer, Python/schema, memory reducer/System Map,
accepted decision or human review changed. Self-reviewed only; no deployment.

Next concrete increment: inspect and surface the existing published knowledge relationships
in the shared detail drawer, separately from containment, with source basis and unavailable
endpoints visible. Do not derive conceptual links from these Board categories or file paths.
