# Project Knowledge: sparring findings

Research date: 31 October 2026. Recommendation: **modify**. This report is research, not implementation or a completed agent experiment. No installation, agent launch, paid inference, service changes, merge or deployment was performed.

## A. Strongest objection and recommendation

The proposal risks building a second editorial system to repair an editorial problem. A graph cannot decide which idea the team has authorized, and a second status record can disagree with the README, ADRs and coordination declarations. Open Presence already names HUMAN-SIGNAL-CONCEPT.md as current, retires hotel/booking, places the pilot in Open Presence rather than Postack, and makes Knowledge Lab optional. A new layer must outperform that maintained baseline, not an artificially disorganized repository.

Proceed with a source-owned, revision-pinned orientation manifest and a deterministic artifact, initially as an adjacent producer/adapter. Observstory may link to or project that artifact through an explicitly enabled integration. Do not extend its metadata collector or snapshot/v1 by default. Keep semantic retrieval entirely consumer-side in Knowledge Lab until measured retrieval failures justify it.

The most valuable incremental feature is a reproducible answer to 'which declared direction applies at this exact revision, and what changed?', not a graph canvas. Supersession and evidence links form a graph mathematically; they do not require a graph database.

## B. Revised, falsifiable thesis

For a teammate or fresh coding agent entering a repository after a concept change, a small source-owned orientation manifest selects the current concept and decision records at a resolved Git commit, distinguishes branch proposals from accepted default-branch direction, and exposes exact evidence and changes. Compared with a maintained README, ADRs, Git history and ordinary search at the same revision, this should reduce reconstruction work or stale-direction errors without increasing confident unsupported answers. If it does neither, retain the documentation baseline and an Observstory link panel rather than building a knowledge subsystem.

## Evidence: plausible problem, unproven intervention

DeChurch and Mesmer-Magnus (2010) synthesize 23 independent studies of shared mental models: both content and structure relate to team performance, and measurement affects results. This supports evaluating shared understanding, not a causal claim that repository graphs improve agent teams. [web:5]

Parnas and Clements (1986) argue for maintaining intelligible design documentation despite a nonlinear development process. This is design-rationale motivation, not a measured knowledge-decay rate or proof of this feature. [web:3]

Liu et al. (2023; revised 20 November) demonstrate position-sensitive retrieval in long contexts on question-answering and key-value tasks. More accessible text is not the same as reliably used context. This does not establish failure rates for the agents/models used here in 2026. [web:18]

Nygard's original ADR practice (15 November 2011) already preserves context, decision, status, consequences and superseded records. Much of the proposal is therefore an ADR discovery/provenance improvement, not a novel memory architecture. [web:22]

No inspected evidence establishes a numerical knowledge-decay rate in this team, measured onboarding savings, improved two-agent alignment, or superiority of graph retrieval over ordinary search. Do not advertise these as findings.

## Repository inspection: findings that change the plan

Read the proposal and all four requested boundaries before technical comparison. Observstory's architecture defines a pure derivation and shared typed snapshot; system-boundary.md explicitly excludes file contents from ingestion; AGENTS.md requires fallbacks when orientation is stale; Weavr owns policy and legal action. An opt-in document reader is still a boundary addition, not merely another existing metadata field.

Inspected Knowledge Lab on feat/knowledge-lab-v1-nuc-continuation, whose head was e5af7441849759b32f97d7f6e637994c6fb026c6, including README, latest integrated NUC handoff, sync.py, ledger.py and engine.py. The handoff's final section supersedes earlier readiness statements: it reports 38 offline/mocked tests passing, loopback UI launch configuration implemented but not started/installed, inactive services, 17 pending production jobs and an empty production index. These are recorded host observations, not live checks performed by this research. The README's older 21-test/blocker summary is not the latest operational account.

Concrete static-code findings:

1. sync.py resolves a content commit, but records branch from local HEAD. When reading origin/HEAD or another configured ref, that branch label can be misleading. Record requested_ref and resolved_commit separately; do not infer scope from the checkout.
2. ledger.py deduplicates revisions by (source_id, sha256). sync.py skips set_current when add_revision returns None. In the visible A → B → A content-revert path, the pointer therefore remains B instead of returning to the existing A revision. This is a static-code finding requiring a regression test, not a reproduced runtime failure. Content identity and appearance at a particular commit must be separate concepts.
3. Source IDs are repo + path, while current_pointers has one row per source, not per ref. This cannot represent simultaneous branch-scoped current views without a new scope/membership layer.
4. Missing git-show content is reported unavailable_upstream and processing continues; the visible path does not withdraw its prior current pointer. Deletion, temporary fetch failure and access loss must not be conflated.
5. engine.query accepts question/mode/context-only, not repository/ref/commit scope. It asks for references but does not itself enforce current-only revision membership or return a corpus snapshot watermark. All-revision ingestion can therefore contaminate current-direction retrieval.
6. index_revision supplies revision_id to ainsert but returns a separately computed text-hash doc ID. Verify the actual pinned engine identifier before relying on indexed_doc_id for deletion or reconciliation.

These gaps do not make the learning backend useless. They make it unsuitable as the authoritative current-project-state service today.

Open Presence inspection covered README.md and HUMAN-SIGNAL-CONCEPT.md, not its complete implementation or external photo-frame threads. Its current concept explicitly treats public contribution reports as source claims, preserves local-draft review, and separates graph exploration from the deterministic pilot. Preserve those distinctions in the orientation layer.

## C. Three architectures and existing implementations

| Architecture | Incremental value | Cost / failure mode | Recommendation |
| --- | --- | --- | --- |
| 1. Maintained README + ADRs + Git + ordinary search | Explicit current pointers, rationale and history; no semantic infrastructure | Editorial upkeep; agents may overlook a pointer or use the wrong checkout | Required control; sufficient if it passes |
| 2. Source-owned manifest → deterministic orientation artifact → optional Observstory projection | Machine-checkable scope, completeness, conflicts, exact sources and reproducible diffs | One small schema and adapter; duplicated authority unless deliberately avoided | Smallest justified experiment |
| 3. Knowledge Lab semantic index alongside architecture 2 | Candidate evidence discovery across differently worded documents; possible relationship exploration | Paid/model-dependent ingestion, stale or mixed-revision retrieval, extraction errors and index lifecycle | Optional learning consumer, never authority |

Existing implementations inspected, with evidence limits:

- GitNexus: repository README documents symbols, calls, dependencies, execution flows and MCP/CLI access. Inspected gitnexus/src/core/index-freshness.ts: explicit incomplete reasons and a three-way healthy/collapsed/unmeasurable write verdict are implemented. Reuse the principle that unknown completeness is not healthy. This is code structure and index health, not team authorization. README currently identifies PolyForm Noncommercial licensing: review before reuse. No installation or performance benchmark was performed. [web:12]
- CodeGraphContext: README describes Tree-sitter/SCIP indexing, calls/imports/inheritance and local or external graph backends. Inspected core/graph_query.py: an abstract backend contract for connection/configuration, not proof that every backend or language works correctly. Useful if call-chain lookup becomes the problem; no evidence it solves concept authority. [web:17]
- Graphiti: inspected graphiti_core/edges.py. EntityEdge implements episodes, created_at, valid_at, invalid_at, expired_at and reference_time. This is useful temporal representation, not evidence that inferred invalidation equals a human decision. README says graph storage, model and surrounding service are consumer responsibilities and warns reference servers lack authentication/authorization. Do not add it beside LightRAG this weekend. Latency/quality claims were not independently tested. [web:10]
- ADRs: already provide the explicit decision/supersession model needed for the first experiment. A source-owned manifest can index them without copying their status. [web:22]
- LightRAG: upstream documents naive chunk/vector retrieval versus graph-oriented local/global and combined modes. Existing Knowledge Lab already exposes these modes. Compare naive against graph-assisted retrieval before adding another engine; mode availability is not demonstrated quality on this corpus. Upstream main documentation is not a compatibility audit of pinned 1.5.7. [web:26]

A graph adds practical value when repeated questions genuinely require relationship traversal, such as tracing an accepted decision through several experiments and evidence records. A small explicit edge list can do this deterministically. RAG adds value when wording mismatch defeats ordinary search. Neither is needed to follow README → current concept.

## D. Responsibility and minimal contracts

| Owner | Owns | Must not claim |
| --- | --- | --- |
| Source repository / humans | Concept and ADR text, authoritative selection policy, confirmation evidence, manifest and audience choice | A document saying accepted proves an authorized human approved it |
| Adjacent orientation producer | Allowlisted commit-consistent reading, validation, explicit links, deterministic current selection and diagnostics | Semantic truth, authorization or inferred consensus |
| Observstory | Existing metadata snapshot; optional projection/link to the separate artifact with matching human/agent IDs and provenance | Agent dispatch, policy enforcement, hidden renderer decisions |
| Knowledge Lab | Preserved source bytes, jobs, extraction and optional retrieval with provenance and freshness | Canonical decisions or currentness from ingestion order |
| Agents | Read/refresh receipt, verify scope, inspect evidence, disclose stale or unavailable inputs | Shared private context, compliance merely because a tool was available |
| Weavr where present | Policy, legal actions and review gates | Orientation metadata automatically grants permission |

### Source and import contract — proposed, not implemented

Start with one optional JSON manifest in the source repo, not mandatory YAML in every document. It selects concept/decision references and exact allowed paths. Ordinary Markdown remains ordinary Markdown. Use existing ADR/coordination IDs where available; do not create a second decision lifecycle. If status is not machine-readable, leave it unknown or make the reviewed manifest explicitly authoritative for selection under a stated policy.

Suggested envelope: schema/version, repository, requested_ref, resolved_commit, manifest_path/hash, parser_version, selection_policy_version, audience, complete, diagnostics, records, explicit_links. A record has repository-qualified logical_id, path, blob/content hash, commit and bounded location. A missing explicit ID can use a path-derived identity with a visible rename-stability limitation. A content hash identifies bytes, not a stable logical document or a branch occurrence.

Resolve the ref once, read every allowlisted path at that commit, and build an immutable content-addressed artifact. Deliver whole snapshots by file/artifact polling first. Snapshot membership keyed by repository + resolved commit + configuration identity is separate from deduplicated content. Re-delivery is idempotent and must not regress a ref head merely because an older snapshot arrived later. Never compare SHA strings or timestamps to infer ancestry.

Updates add new membership and bytes only when changed. A complete authoritative snapshot may remove membership; an incomplete scan cannot prove deletion. Retain old snapshots/bytes under an explicit retention policy. Record withdrawals/tombstones when exporting incremental changes later. Privacy deletion is a separate purge policy, not ordinary supersession. Validate paths, sizes, encodings, duplicate IDs, unknown statuses, dangling links and supersession cycles. Treat imported text as data, not executable agent instructions.

### Query and freshness contract — proposed

Start with project-brief(repository, snapshot_id) and record(snapshot_id, id). Add changes(base_snapshot_id, target_snapshot_id) only when both artifacts are retained; otherwise return history_unavailable. Include source changes, removals and status/supersession changes rather than only new files. Git can regenerate older artifacts if their source commits and producer/config versions remain available; an Actions workflow alone does not guarantee retention.

Every response echoes requested_ref, resolved_commit, snapshot_id, selection policy, diagnostics and completeness. Separate source resolution time, artifact generation time, last ref check and semantic index completion; a recent build timestamp does not prove a recent successful fetch. Semantic results must include the exact indexed corpus snapshot and returned passage revisions, with state current/stale/partial/unknown.

For reproducible deterministic queries, pin artifact, parser/policy versions and arguments. For semantic queries also record mode, corpus, engine/model/embedding configuration and retrieved passage IDs; archive the returned result. Matching inputs do not guarantee bit-identical model generation.

Current means selected by the declared policy at the requested commit. An accepted ADR remains applicable until explicitly superseded under that policy, not until a newer file mentions another idea. Two competing declarations yield unresolved. Missing history means unknown history, not evidence that nothing changed. An unmerged branch can have an approved proposal while remaining unapplied on default branch. A human's name in front matter is a claim; expose the review/confirmation event when verified, and show unverified when not. Merge alone is not universal approval.

For semantic integration initially use an isolated index for a bounded immutable corpus snapshot, or disable current-only answers until the pinned engine is shown to enforce revision membership. Post-filtering a generated answer is too late. Unknown/stale retrieval must never replace fresh explicit declarations.

### Extraction and static publication

A proposed support/contradiction link belongs in a separate suggestions collection with both passage revisions, extractor/model/prompt version, run time and review state. Show it in an inspector; do not use it for current selection. Human adoption creates a new explicit declaration referencing the suggestion; retain the original extraction. Related-to is not supports, and a source claiming X is not independent verification of X.

A static artifact can power the brief, record inspector, declared edges, diagnostics, retained-snapshot diffs and small local text search entirely offline. Its freshness is only as of its recorded successful source resolution. Credentials, private repository fetches, model calls, private NUC retrieval and authorization checks remain outside the static page. Public output must use an explicit publication allowlist: private titles, paths and excerpts can leak even without full text. Escape rendered content and do not execute embedded HTML/scripts. No service key or browser-to-private-NUC dependency is needed.

## E. Five high-impact changes

1. Move the first producer beside the source repo, not into metadata ingestion. This makes the opt-in content boundary real and lets Observstory remain a projection consumer. Promote a general plugin only after demonstrated reuse.
2. Replace per-document taxonomy work with a tiny manifest indexing existing concepts/ADRs/coordination. This tests the maintained-docs baseline fairly and avoids duplicate approval records. ADR practice already supplies the core lifecycle. [web:22]
3. Separate content identity, commit membership and decision authority. The inspected branch/current-pointer/revert paths demonstrate why one current pointer and a timestamp are insufficient.
4. Make deterministic scope/completeness a prerequisite for semantic current answers. Reuse LightRAG for optional evidence discovery; do not introduce Graphiti or a second graph database. [web:26][web:10]
5. Gate UI and retrieval expansion on measured errors/work, not a successful graph rendering. Human team-cognition research and long-context experiments motivate evaluation, not a promised benefit. [web:5][web:18]

## F. Revised build plan and two-agent test

The following are future experiment/build recommendations. Research above is completed; the proposed experiment was not executed here. Effort estimates are assumptions for one developer familiar with the repos, not commitments.

### First 90 minutes: falsify the extra structure

- 0–20 minutes: freeze real Open Presence source revisions and prepare a scored answer key: current photo-frame pilot; obsolete hotel scenario; correct delivery repo; optional Knowledge Lab; local-draft/no-upstream-write boundary. Preserve sources without editing them to fit a parser.
- 20–35: prepare a hand-authored orientation manifest/view plus branch-change and stale-input fixtures. Include an attractive but unmerged alternative, a contradiction and a deleted/missing source. Fixtures are labelled, not invented project history.
- 35–70: run two isolated agent sessions, with no shared conversation. Agent A and B each receive matched tasks under maintained-docs control and orientation treatment, using counterbalanced equivalent cases and fresh resets. Same model, tool access, time/token budget and source corpus; treatment adds only the orientation artifact. Do not reuse answers across conditions.
- 70–90: manually score correctness, exact evidence/revision, source opens, elapsed time/tokens, unsupported confident assertions and uncertainty disclosure. Ask each agent to state its snapshot/ref receipt before answering. Agent agreement is insufficient: both can agree on the obsolete hotel plan.

Proposed gate: zero treatment claims that a branch proposal is accepted default state; both agents disclose stale/ref context; at least one baseline miss is corrected or reconstruction work falls without lower accuracy. Two agents are a mechanism smoke test, not statistical proof. If the baseline already succeeds cheaply, stop at documentation plus a link panel. Do not invent a percentage improvement target after seeing outcomes.

### Gated milestones

| Milestone | Assumed effort | Observable acceptance |
| --- | --- | --- |
| M0: hand-authored orientation artifact | 90-minute experiment above | Baseline comparison and scored errors/work saved; explicit stop decision |
| M1: adjacent deterministic producer | 2–4 hours | Commit-consistent fixtures; duplicate/cycle diagnostics; A→B→A restores current; branch scopes independent; complete deletion removes membership; incomplete scan does not |
| M2: source repo + optional Observstory projection | 1–2 hours | Same IDs/commit/diagnostics in human and agent views; backend down still works; disabled integration leaves existing behavior/contracts unchanged |
| M3: optional Lab bridge | Half-day assumption; defer if weekend time is scarce | Duplicate delivery, old snapshot arrival, deletion, failed jobs and stale index tested; exact passage revision retrievable; no cross-ref contamination |
| M4: semantic comparison | Only after separate spend authorization | Same bounded corpus/questions: ordinary search vs naive vs graph-assisted modes; record retrieval accuracy, unsupported claims, latency and cost; stop if no useful gain |

Do not make a live semantic demo a dependency of the weekend pilot. Existing recorded offline tests are not a live model-quality result.

## G. Concrete change walkthrough

Illustrative fixture based on the actual photo-frame direction, not a claim that a new decision has occurred:

1. At default commit C0, manifest selects concept K and decision D0: pilot runs independently of Lab. Agent B records receipt C0.
2. On branch research/frame-context at C1, Agent A adds research R that similar USB symptoms have different hardware circumstances, and proposes K2/D1 to require an applicability field. R contains exact source passages and uncertainty; a model-suggested contradiction remains pending. No source report becomes a verified hardware result.
3. A human reviews and explicitly confirms D1 through the repo's chosen approval mechanism. The manifest links that confirmation evidence and D1's supersedes D0. Until integration, default C0 still selects D0; branch C1 shows the confirmed branch proposal, not a default-branch decision.
4. After integration at C2, a complete artifact selects D1/K2 with R and confirmation evidence. A query pinned to C0 still returns D0. A current-ref query resolving C2 returns D1. Competing declarations produce unresolved, not a timestamp winner.
5. Agent A refreshes to C2. B initially using C0 cannot honestly claim latest without a ref check; after checking, it reports stale and refreshes. Both receipts identify C2, D1 and R before implementation. Their private reasoning/context remains separate.
6. If semantic indexing remains at C0, deterministic C2 guidance still works. Optional search is labelled stale and cannot override D1. Observstory may show observed branch activity alongside the declaration; Weavr, if present, decides permitted actions.

## H. Do not build this weekend

No graph canvas, new graph database, generic ontology, automatic contradiction-to-decision promotion, controller, agent dispatch, model-based approval, full-chat ingestion, general crawler, webhook service, MCP-first server, automatic write-back, deployment or participant scoring. Do not retrofit every Markdown file or duplicate Knowledge Lab's ledger. Do not fix this proposal by weakening Observstory's metadata-only default.

## I. Audit sources and unresolved gaps

All repository inspections below were performed on 31 October 2026. URLs are an audit inventory; blob hashes identify the read bytes where branch links are mutable. They are not claims of runtime verification.

Requested proposal and boundaries:
- https://github.com/blackmath88/observstory/blob/docs/project-knowledge-concept/docs/project-knowledge/PERPLEXITY-PROMPT.md — blob 105f3c3f8ad0895879b2f15e25d6bfa23f2c8919.
- https://github.com/blackmath88/observstory/blob/docs/project-knowledge-concept/docs/project-knowledge/CONCEPT-AND-BUILD-PLAN.md — blob 537e65be704192a7fff883040d7c74c6182d8a70.
- https://github.com/blackmath88/observstory/blob/main/ARCHITECTURE.md — blob 86350c1660781d3d64f0c5068cc1d850c50ea96e.
- https://github.com/blackmath88/observstory/blob/main/AGENTS.md — blob b591ff2c2a18e0f62bf7d29c20323a77ae7c89a4.
- https://github.com/blackmath88/observstory/blob/main/docs/definition/system-boundary.md — blob 679d5b00dab177edfa931895d00ca2b077cdb166.
- https://github.com/blackmath88/observstory/blob/main/docs/integrations/weavr.md — blob 6ebf432f2becdddb4b25d2d7237167bf9337852e.

Consumer/backend, inspected on the requested continuation branch (head resolved above):
- https://github.com/blackmath88/baselhack26-knowledge-lab/blob/e5af7441849759b32f97d7f6e637994c6fb026c6/docs/NUC-SETUP-HANDOFF.md — blob b9074912256bdd4294f7e799195ca99d755806f8.
- https://github.com/blackmath88/baselhack26-knowledge-lab/blob/e5af7441849759b32f97d7f6e637994c6fb026c6/src/knowledge_lab/sync.py — blob 52fb11ccc295305492c0236522bcf8414ab92edf.
- https://github.com/blackmath88/baselhack26-knowledge-lab/blob/e5af7441849759b32f97d7f6e637994c6fb026c6/src/knowledge_lab/ledger.py — blob d2e1c30374c297bf41ee1e71e58267342e00b450.
- https://github.com/blackmath88/baselhack26-knowledge-lab/blob/e5af7441849759b32f97d7f6e637994c6fb026c6/src/knowledge_lab/engine.py — blob ca503f265ccfc86a8eb49cd06d47c3617635ea62.

First target:
- https://github.com/blackmath88/baselhack26-open-presence/blob/main/README.md — blob 2c3caeb34c2dcfef2706faaf95ddddace76c2abb.
- https://github.com/blackmath88/baselhack26-open-presence/blob/main/HUMAN-SIGNAL-CONCEPT.md — blob 35b4c5c3352b3a2c3770326bf7e7f1e53122dde0.

Implementation inspections:
- https://github.com/abhigyanpatwari/GitNexus/blob/main/gitnexus/src/core/index-freshness.ts — blob 52e62e8d852f5086127f96290d24dd8894f65d52; README also read.
- https://github.com/CodeGraphContext/CodeGraphContext/blob/main/src/codegraphcontext/core/graph_query.py — blob 447bdd55225ef9a2d20348ac8866cc910f645bc9; README also read.
- https://github.com/getzep/graphiti/blob/main/graphiti_core/edges.py — blob 6800438d9da1ea0f9d566a93bb4489c206726e2c; returned file was truncated after the relevant EntityEdge definitions; README also read.
- https://github.com/HKUDS/LightRAG/blob/main/README.md — upstream documentation retrieved through search, not a pinned-engine source audit.

Original research/practice sources:
- DeChurch & Mesmer-Magnus, 2010, Measuring Shared Team Mental Models: A Meta-Analysis, DOI 10.1037/a0017455: https://stars.library.ucf.edu/scopus2010/1219/
- Parnas & Clements, 1986, A Rational Design Process: How and Why to Fake It: https://www.cs.tufts.edu/~nr/cs257/archive/david-parnas/fake-it.pdf
- Liu et al., 2023, Lost in the Middle, version 3 dated 20 November 2023: https://arxiv.org/abs/2307.03172
- Michael Nygard, 15 November 2011, Documenting Architecture Decisions: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions

Gaps: GitHub browser fetch of the initial brief failed, but authenticated GitHub reads succeeded; no requested core document remained unread. No live NUC verification, full codebase audit, actual two-agent experiment, measured adoption burden, longitudinal community evaluation or graph-quality benchmark was performed. Research supports the motivation, not the proposed intervention's benefit. The team's exact approval policy remains to be declared. No verified GitHub write is implied by this report's preparation.
