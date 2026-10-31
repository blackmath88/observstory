# Observatory frontend (preview)

A static TanStack Start v1 app that renders an Observstory snapshot in the browser. It is opt-in:
the Python renderer (`map_render.py`) remains the default output until this reaches parity.
Decisions are in [DECISIONS.md → ADR-038](../DECISIONS.md).

```bash
cd frontend
npm ci
npm run dev        # http://localhost:4317/  (synthetic fixture "hackathon")
npm test           # unit tests: data adapter, freshness
npm run typecheck
npm run lint       # Biome
npm run build      # dist/client: index.html + assets, relative URLs
npm run e2e        # Playwright: build served under /hackathon/, /quiet/, /broken/
```

## How it is served

- `npm run build` writes `dist/client/`.
  - Drop it into any folder (for example a GitHub Pages project path), next to the Action's
    `data/` directory. Asset URLs are relative and routes use the hash (`#/sources`), so any
    subpath, direct link and reload work without a server.
- The page fetches these at runtime:
  - `./data/snapshot.json` and `./data/scene.json`: required.
  - `./data/knowledge.json` and `./data/event.json`: optional.
- Each input is checked against `../schema/*.json`. Its state is shown on the Data sources tab:
  loaded, not published, unsupported version, invalid, unreadable or unreachable. Absent data is
  never shown as zero.
- `?data=<relative path>/` points the page at another data folder, for review or for fixtures.
  Only relative same-origin paths are accepted.

## Shipping through the Action

`npm run release` rebuilds `frontend/release/`. Commit it with the source change; Python's
`tests/test_frontend_release.py` checks it. A consumer opts in with:

```yaml
- uses: blackmath88/observstory@<sha>
  with:
    frontend: observatory   # default: classic
```

The new app becomes `index.html`, and the classic map moves to `map.html`.

## Fixtures

The fixtures in `fixtures/` are synthetic, built by `node scripts/make-fixtures.mjs`; see
`fixtures/README.md`. Real consumer data is never committed. To check it locally, download a
consumer's `data/` folder and run:

```bash
OBSERVSTORY_LIVE_DATA=/path/to/data npx vitest run src/data/live.test.ts
```

## Layout

| Path | What |
|---|---|
| `src/server.ts` | Prerender entry: rewrites asset URLs to relative |
| `src/router.tsx` | Hash-history router |
| `src/routes/_app.tsx` | Client-only layout: loads the data bundle, repository header, tabs, freshness |
| `src/routes/_app/index.tsx` | Overview: project summary, needs attention, lanes (compact), snapshot facts |
| `src/routes/_app/sources.tsx` | Data sources: every input and exactly what happened when it loaded |
| `src/data/` | Source specs, loading, schema validation, freshness |
| `src/styles/app.css` | Light-first tokens with a dark set; GitHub-familiar Box, UnderlineNav, Counter and Label patterns |

## Visual workspace

Overview and Board share one normalized projection in `src/view/workspace.ts`.
Optional `.observstory/workspace.json` is public, source-owned context, validated against
`schema/workspace-v1.json`. The Action reads it from the observed Git commit and publishes
`data/workspace.json` with `source_commit`. Unknown fields fail publication; absent declarations
produce no file. No write API, owner inference or lifecycle inference is added.

`records` are an ordered array with stable IDs, title and kind. Optional fields: context,
explicit lifecycle status, ordered member IDs (knowledge IDs may be referenced), HTTPS source
links, attention request, resume stopping point/next action, planned start/end/precision and
milestone flag. Relations explicitly name from/to workspace IDs and one of `supports`,
`explores_for`, `spawned_from`, `blocks`. Membership must be acyclic. No private paths or chats
belong in this public declaration. See `fixtures/workspace/data/workspace.json` for a **synthetic**
paused supporting exploration; it is never shipped as consumer state.

Without a declaration the view uses selected knowledge in source order plus area groups sorted
by ID. Area groupings are labelled derived; they never establish conceptual relationships.
Document status and observed artifact state are retained as evidence, not mapped to lifecycle.
Undated records stay visible. Timeline points mark observed activity, outlines mark declared
planned targets, diamonds mark milestone targets; no commit-to-commit duration is inferred.
Missing or mismatched inputs are qualified. Board uses an explicit Undeclared column.

Record category filters (Research, Concepts, Planning, Implementation, Other context) use
record kinds without inventing membership or lifecycle. Text search covers title, context,
evidence basis, source titles and declared resume/attention text. Both views show the same
matches. Overview keeps existing ancestors visible and reveals matching descendants at every
level; clearing filters restores saved expansion choices. Timeline columns stay aligned across
nesting levels. Category counts reflect the current search.

Expansion persists locally per data base. View, selection, category and search use hash query parameters, e.g.
`#/?view=board&focus=plan&q=checkpoint&item=ws-plan`. Drawer close restores focus and expansion;
direct selection links and reload work under arbitrary project subpaths. The event clock and
Data sources remain accessible, and companion classic/replay links are probed as before.

The shared detail drawer shows root-to-record membership routes and each record's evidence
basis. Multiple memberships remain separate routes; conceptual relations and filesystem paths
do not create parents. Missing containment is stated explicitly. Location traversal is bounded
to 12 routes / 512 visits and discloses omitted or cyclic paths.

**Reveal in Overview** closes the drawer, opens existing ancestors temporarily, highlights and
focuses the record, and scrolls it into view. `reveal=<record ID>` in the hash preserves this
location across reload/history. Search/category and saved expansion remain unchanged. A notice
qualifies any revealed record outside the filters; counts still describe matching records.
**End reveal** restores normal visibility and returns focus to search. Switching to Board also
ends the reveal. Drawer breadcrumbs can open containing records; direct-link close stays in
the workspace.

The local fixture host includes `/workspace/` for synthetic interaction checks. To preview
real consumer data, copy `release/` to a directory alongside that consumer's `data/`, then run
`python3 -m http.server 4318 --bind 127.0.0.1 --directory /path/to/preview`.

To verify the prebuilt release with captured real inputs, use
`OBSERVSTORY_PREBUILT=1 OBSERVSTORY_LIVE_DATA=/path/to/data npm run e2e -- --grep 'real Open Presence'`.
The Playwright-owned host serves it under `/live/` and binds only `127.0.0.1`.
