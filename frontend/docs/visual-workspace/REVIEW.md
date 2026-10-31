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
