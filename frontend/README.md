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
