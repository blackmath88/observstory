# Observatory frontend rewrite — build plan
Date: 31 October 2026
Status: planned; visual studies and owner-provided templates pending. This document is not a release approval.
Target: blackmath88/observstory. First consumer: baselhack26-open-presence.
Execution: Claude through Orca on the NUC; inspect the actual checkout and runtime before working.

## Outcome and use case
During a hackathon, several people and agents change code, concepts, research and plans. People need to see what is moving, where work intersects, what needs conversation, and the evidence behind it. Agents need the same trustworthy project state.
Make the existing Observatory a polished working tool with an observatory identity: precise navigation, map/list views, evidence inspection, coordination and honest replay.
The first real consumer is Photo Frame Commons / Open Presence, investigating human experience, provenance and community in an agent-mediated web. Knowledge Lab is its separate graph/retrieval experiment. Neither a graph service nor a cross-repo feed is assumed connected.

## Existing boundaries to preserve
Read AGENTS.md, ARCHITECTURE.md, docs/ui/design-language.md, docs/ui/scene-grammar.md and docs/integrations/weavr.md at the current checkout.
Keep GitHub → observations → snapshot → scene/query separation. Snapshot is the product boundary.
Preserve collector, pure derivation, signal evidence, CLI and agent queries. Observstory observes; Weavr decides; runtimes act.
Keep observed, derived, heuristic and declared labels; proposed coordination remains proposed. No person rankings, productivity scores or inferred acceptance.
Metadata collection stays metadata-only. A frontend rewrite does not authorize ingesting research document contents or private conversations.

## Development practice
Apply blackmath88/development-practice PRACTICE.md and profiles/product.md: proportionate architecture, inspect first, versioned explicit state, intentional design, meaningful verification.
The requested “TanStack starter v1” has not yet been identified. Do not invent a repository/version or assume development-practice contains it.

## Proposed architecture
Retain the Python producer and introduce an opt-in typed frontend, provisionally under frontend/.
Use React + TypeScript with TanStack Router as the candidate static application shell. Verify the owner's exact starter before scaffolding; record any departure in an ADR.
TanStack Start/SSR is not required by the current static snapshot use case. Add Query only if actual remote-refresh behavior earns it; do not add a backend just for the framework.
Consume versioned snapshot and scene contracts through one validated adapter. Generate TS types from schemas if suitable; runtime validation must reject unsupported schemas and explain failures.
Keep the current renderer available as fallback throughout migration.
The distributable must work under a GitHub Pages project subpath without secrets or server routes. Decide hash routing versus static fallback explicitly. Test direct entry and reload.
Preserve downloadable artifact use: bundle snapshot data safely or provide a local-file import path. Do not assume file:// fetch works.
Choose an Action packaging strategy in the ADR: ship tested prebuilt assets with a pinned action release, or build in CI with pinned dependencies. Do not quietly require every consumer to install Node.
No new model calls, accounts, databases, runners or paid services.

## Visual direction — proposal, not final
A restrained observatory beneath a quiet sky; precise charcoal/blue-grey interface surfaces, readable typography and compact rows with clear separators. GitHub-familiar interaction conventions with an independent identity.
Pixel scenery lives in margins, sidebar and empty space. No pixel body font, busy stars behind reading surfaces or fullscreen decorative hero.
Study three treatments with identical synthetic data: observatory courtyard; telescope instrument; star atlas. Include quiet, overlap and replay states.
Potential law: every meaningful mark leads to evidence. Distinguish decorative stars from selectable data, and distinguish overlap from dependency connections.
Telescope orientation may follow selected area. Instrument state must not imply collection is occurring when only an old snapshot is loaded.
Owner templates are coming separately. Produce studies now; settle final palette, composition and assets after reviewing them. No claim that the provided reference images are licensed shipping assets.
See CLAUDE-PIXEL-DESIGN-HANDOFF.md for the design-only slice.

## Delivery slices and acceptance
### 0 — Inspect and establish baseline (45–90 minutes indicative)
Inspect git status, active branches, instructions, current snapshot and existing tests. Preserve concurrent changes; use an isolated branch/worktree when necessary.
Inventory current map, inspector, radar, coordination and agent-facing contracts. Run existing tests and record baseline failures separately.
Locate exact starter/template or record it as unresolved. Deliver short architecture ADR and migration checklist.
Acceptance: confirmed source paths, known baseline and explicit static distribution strategy.

### 1 — Visual studies (separate Claude design task)
Deliver self-contained study page, deterministic pixel assets, token proposal and real state mappings. All study data synthetic and labelled.
Owner selects direction after supplying templates. Functional contract work may proceed meanwhile; final visual implementation depends on selection.

### 2 — Typed shell and data boundary (2–3 hours indicative)
Implement adapter, shell, navigation, selection state and load/error/empty/degraded states. Keep data URLs configurable and repository-subpath safe.
First complete journey: open snapshot → select work item → inspect evidence → open GitHub source.
Acceptance: same fixture semantics as existing renderer; malformed and unsupported data fails visibly; no secrets/browser GitHub token.

### 3 — Map, list and coordination (3–5 hours indicative)
Implement stable project-area grouping, work items, overlap/waiting evidence and a full equivalent list view. Stable placement prevents rearrangement being mistaken for change.
Add coordination rail preserving declared-versus-observed distinctions. Show collection time, window, degradation and missing coverage.
Keyboard navigation, visible focus, inspector dismissal/focus return and small-screen navigation are part of this slice.
Acceptance: each signal can be explained from source evidence; absent data is not rendered as zero or healthy.

### 4 — Replay (2–4 hours indicative)
Treat three feeds separately:
1. Repository file history: existing consumer prototype at baselhack26-open-presence/scripts/build_replay.py and replay/index.html; last 200 first-parent commits, explicit baseline, additions/edits/removals.
2. Observatory state history: actual stored observation bundles/snapshots; current stateless Action does not retain this history. Existing Demo Lab is synthetic.
3. Knowledge graph events: future adapter, currently disconnected.
Do not reconstruct historic PR/coordination state from commit timestamps alone. Offer only available modes, with clear labels.
Implement play/pause, scrub, speed, selected-event evidence, deterministic reconstruction and reduced motion. Preserve deletions and corrections.
Acceptance: same event position always yields same state; missing history is stated; no fabricated growth.
Durable state-history capture is a separately scoped follow-up, not an incidental storage service.

### 5 — Verification and opt-in integration (2–3 hours indicative)
Run existing Python/contract tests, TS typecheck/build, focused adapter/replay tests and browser journey tests.
Check 390/768/1440 viewports, keyboard, reduced motion, contrast, empty/stale/degraded/error states, unsafe text/URLs and supported data sizes.
Treat all source text as untrusted: no raw HTML interpolation; allow only intended URL protocols.
Verify built output under repository subpath and downloadable artifact mode.
Deliver reviewable branch/PR, screenshots, test evidence, limitations and exact rollback.
Only after selected design and review: trial in Open Presence with a pinned upstream revision. Keep old renderer selectable. Do not deploy or change the consumer as part of this planning/design assignment.

## Time and scope
Estimates are planning ranges, not promises: roughly 11–18 engineering hours plus visual selection. For the two-day hackathon, ship slices 0–3 first, then repository replay if time permits.
Cut advanced sky effects, cross-repo aggregation, live streaming, graph ingestion and all service migrations before cutting evidence inspection or accessibility.
A polished static inspector and map is a complete useful first release.

## Handoff requirements
Report actual branch, commits, changed paths, commands/results, screenshots, open decisions and what has not been verified.
Do not mark planned work complete because files or a PR exist. No production deployment, merging or upstream consumer changes are authorized by this document.
