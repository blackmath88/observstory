# Observatory next — shared project memory
Architecture research and MVP delivery specification · 31 October 2026
Status: proposed implementation architecture, ready for a full delivery slice; not implemented by this document.

## Product thesis
The project owns its memory. People and agents receive dated, task-specific views and return evidence-backed proposals.
Observatory makes the current picture, its evolution, and the origin of changes inspectable.
The target is a useful release, not a collection of disconnected experiments.

## Research and reuse decision
Primary sources inspected on 31 October 2026. Capabilities below describe upstream documentation, not verified behavior on our NUC. Pin exact dependency versions during implementation.

| Source | Useful architecture | MVP decision |
| --- | --- | --- |
| [Graphiti](https://github.com/getzep/graphiti) and [episodes](https://help.getzep.com/v2/graphiti/core-concepts/adding-episodes) | Temporal graph, source episodes, incremental extraction and relationship invalidation | Adapt episode/provenance separation. Do not deploy a second extraction engine alongside LightRAG for this release. Automatic invalidation must never approve or supersede our declared decisions. |
| [AgentMemory for .NET architecture](https://github.com/joslat/agent-memory-dotnet/blob/main/docs/architecture.md) | Shared context assembly and a surface-neutral projection consumed by different adapters | Adopt the projection boundary and context receipt; no .NET/Neo4j migration. Inspect the Python Neo4j alternative only if replacing the existing retrieval stack later. |
| [XTDB temporal concepts](https://docs.xtdb.com/concepts/key-concepts.html) | Separates system time from valid time, enabling historical corrections without pretending they were known earlier | Adopt two clocks and explicit unknown validity. No XTDB deployment required for this single-host MVP. |
| [Microsoft event sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) | Retained events support derived read views and reconstruction; schema/concurrency complexity is real | Use a narrowly scoped knowledge ledger and rebuildable projections. Do not event-source the whole application or add Kafka. |
| [LightRAG](https://github.com/HKUDS/LightRAG), [core operations](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md) | Existing graph-assisted retrieval, citations and document lifecycle operations | Retain Knowledge Lab as the retrieval adapter; it is not the canonical historical or approval store. Validate APIs against its installed version, not latest main. |
| [Achim's essay](https://bridge-work.ai/en/blog/maybe-the-agent-shouldnt-own-the-memory/) | Shared memory/capability, bounded projection, evidence and governed write-back | Product rationale. The uploaded English essay was read; its wider learning loop is a proposal, not a claim about shipped third-party behavior. |

Graphiti is the strongest alternative if temporal semantic relationship retrieval becomes the dominant requirement. It brings a graph backend and extraction operations; replacing LightRAG deserves an explicit migration decision. Running both now would add duplicate extraction, identity reconciliation and operational burden.

Recommendation: existing Observstory producer + SQLite knowledge ledger + immutable source payloads + LightRAG retrieval adapter + shared context projection + Observatory history UI.
SQLite stores explicit nodes/edges and historical versions; a graph visualization does not require another graph database. This is application-specific glue around existing tools, not a new general memory framework.

## Verified repository baseline
Observstory main inspected at 3e0dc7f24e490b6ee9cdb4795993a5cc12fa1964.
Existing Project Knowledge builds selected records from one Git commit, checks declarations, preserves logical IDs and emits first-parent changes. It has no retained store, semantic retrieval or MCP transport in that slice.
Open Presence enables the producer via .observstory/knowledge.json.
Knowledge Lab main config still lists older domain documents across four repos; that config is not evidence of the actual running NUC branch.
Open Observstory PR #17 (System Map v0) must be inspected before choosing UI/schema touchpoints; do not overwrite concurrent work.
Fresh implementation must check current heads and runtime, as this baseline can change.

## Release scope: five working journeys
1. CURRENT: return to the project and see current direction, decisions, open questions, evidence and ingestion freshness.
2. HISTORY: inspect an idea's versions and relationships; compare two revisions; view state as recorded at a chosen time.
3. CONTEXT: request a bounded task brief and download identical JSON/Markdown evidence for ChatGPT or Claude.
4. WRITE-BACK: submit an attributed finding/proposal, with conditions and evidence; track its reviewed acceptance, rejection or supersession.
5. REPLAY: replay actual knowledge changes, with a readable event log and inspectable sources.

Ship these as one coherent MVP. Basic correctness checks are acceptance gates within delivery, not separate exploratory products.

## Ownership and architecture
- Source repos: authored documents, knowledge manifests, coordination and accepted proposal records.
- Observstory: knowledge contract, deterministic version/delta/projection logic, history query surface and UI exports.
- Knowledge Lab: NUC source acquisition, durable store hosting, retry worker and LightRAG integration.
- Weavr, when present: orchestration/authorization decisions. Observstory records evidence and declared outcomes; it does not dispatch agents.
- GitHub Pages: public export only. No tokens, SQLite files, raw private logs or write endpoint.
- NUC: authoritative persisted observation/ingestion/receipt history; backups outside the checkout.

Flow:
Git commits / selected chat handoffs → exact-revision producer → durable ledger + source payloads → current/history/graph projections → context packet and human UI.
A committed ledger transaction enqueues retrieval work; a worker indexes it and records the outcome. Ledger ingestion success and LightRAG readiness are separate visible states.

## Durable data contract
Proposed tables; finalize names against existing schemas:
- sources: repo identity, allowlisted ref, remote check outcome and cursor.
- snapshots: source commit, producer version, manifest hash, completeness, first observed time, captured payload digest.
- record_versions: logical ID, immutable version ID, content digest, source path/section, status, evidence, audience.
- relation_versions: stable identity, endpoints, relation, basis, source evidence, asserted validity interval if known.
- events: unique ID, sequence, type, source snapshot, subject, before/after version, recorded_at, source timestamp, actor/producer and causal references.
- proposals and review_events: conditions, evidence, proposed change, base revision, authenticated reviewer outcome.
- indexing_jobs: version, backend/config generation, attempts, status, error and retry time.
- context_receipts: requested scope/time, selected version IDs, policy/projection version, packet hash, omissions and delivery acknowledgement where available.

Events include record_added, record_revised, selection_removed, status_changed, relation_added, relation_ended, proposal_recorded, proposal_reviewed, indexing_succeeded/failed and context_issued.
A file diff does not imply a semantic reason: reasons must come from cited declarations or be explicitly attributed interpretation.
Model-generated relations are suggestions, never silently promoted source declarations.

## Time semantics
Store recorded_at (when this system learned it) separately from source commit time and any explicitly asserted valid_from/valid_to.
Historical backfill records its true ingestion time; it must not claim the system knew that information earlier.
Offer two distinct controls: repository revision and system-as-known-at. Optional effective-at uses explicit validity, with unknown marked unknown.
Use per-repo commit ancestry for ordering, ledger sequence for observation order. Cross-repo commits have no invented global causal order.
First-parent replay is a deliberate branch view; merged changes and other branches need labels. Missing pre-manifest history is unavailable, not empty.
A corrected fact can refer to the past while only becoming known now.
Store supersession links without deleting earlier evidence. Selection removal is not proof a statement became false.

## Ingestion and resilience
Use the existing configured NUC poller as the first delivery mechanism; inspect its real branch/service and adapt it. A suggested 60–120 second interval is configuration, not a job installed by this plan.
Fetch allowlisted refs, resolve once, then process every newly reachable first-parent revision that affects selected knowledge. Do not ingest only the latest Pages JSON and lose intermediate revisions.
Regenerate knowledge with the manifest present at each revision; before a manifest exists, report the coverage boundary.
Persist snapshot, versions, events, cursor and outbox atomically. Deduplicate on source snapshot and deterministic change identity. Retry must not duplicate events or model work.
Missing sources create incomplete observations, never mass removal. Interrupted imports retain last complete state with visible lag.
Force-push/branch divergence creates a recorded lineage change; preserve observed history and avoid pretending it is still on current main.
Persist content needed to reconstruct records, not just links to Git objects that might later be garbage-collected.
Back up SQLite with a consistent backup mechanism plus referenced payloads; exercise restore once as release verification.

## Retrieval integration
Consume manifest-selected records rather than the old hand-maintained domain-file list. Preserve logical ID/version to backend-document mappings.
MVP semantic retrieval serves a clearly identified current index generation. Historical queries use ledger records and SQLite full-text/explicit relationship traversal; do not synthesize a historical answer using a current-only graph.
Changes/deletions must invalidate stale search membership. If the installed LightRAG version cannot guarantee a clean incremental update, rebuild a separate generation and switch only after completion. Do not mix retired and new versions silently.
Fail closed for authoritative semantic answers while indexing is stale; offer deterministic current records instead. Merely filtering citations after synthesis is insufficient.
Record model/provider/config and extraction generation for derived edges; reuse stored extraction results rather than re-running models during visual replay.
No LLM inference is needed for exact revision history, declared links or source-diff classification.

## Context and assistant access
One projection function returns JSON and Markdown: current direction, relevant records, decision status, unresolved contradictions, source evidence, version/cutoff, diagnostics and explicit omissions.
Persist the exact issued packet or a reproducible retained payload plus hash. “Issued” does not prove a model read or used it; acknowledgements are separate.
Candidate read-only operations: project_brief, record_history, changes_between, state_at, context_for_task, ingestion_status.
Implement CLI first and expose the same operations via a thin read-only MCP adapter using the official SDK. No independent MCP memory store.
NUC-local stdio supports Claude Code/Orca. Cloud ChatGPT/Claude require a compatible authenticated reachable transport; Tailscale-only service is not automatically reachable from hosted assistants.
Until remote transport is verified, both can consume the public static brief/JSON or GitHub sources. This is a supported MVP channel, with explicit freshness, not a claim of installed project-wide integration.
Scope/authorization filtering happens before retrieval and projection. MVP shared public project scope avoids pretending full multi-tenant support is built.

## Write-back without creating an orchestrator
Use a versioned proposal record in the source repo, normally through a PR. Include evidence, conditions, source context packet ID and expected base revision.
Existing human review or an explicit Weavr authorization supplies acceptance. A merged arbitrary document or model confidence alone cannot manufacture approval.
Concurrent or stale proposals retain their original bases; flag conflicts before applying status changes.
Store knowledge changes separately from accepted procedural lessons. Retain failed approaches and exceptions with their scope.
No automatic private-chat scraping, no hidden reasoning traces, and no automatic skill promotion.

## Interface and repository story
Working release label: Observatory — Project Memory.
One shell: Now / History / Graph / Context, with a persistent evidence inspector and optional proposal inbox.
Graph nodes represent records; solid declared links and distinct suggested links have textual labels. Stable positions across replay. Timeline displays revision/change events, not a productivity score.
Keep repository-file replay separate from knowledge replay and from retrieval-index job logs.
Pixel story: telescope = selected view; observation archive = preserved evidence; atlas = evolving relationships; reading desk = task context. Data freshness is explicit and decorative motion never pretends to be live collection.
Integrate the owner-selected pixel study when available, retaining a clean functional UI until then. Respect the existing frontend rewrite plan; framework migration must not block the history contract.

Repo narrative:
“The project remembers. Every collaborator gets the context they need.”
Show a real source-backed sequence: earlier business-presence direction → human-signal concept → photo-frame pilot, only where committed evidence establishes that sequence. Add PDF research and its qualifications without suggesting it changed decisions unless the sources say so.
End with two assistant context packets referencing the same accepted record versions. A real assistant run may demonstrate use; label any staged scene synthetic.

## Implementation work packages
A. Observstory: versioned ledger contract, pure event reducer, history/projection CLI, public export, fixtures and migrations.
B. Knowledge Lab: manifest adapter, exact-revision synchronization, SQLite persistence, transactional outbox, retrieval-generation integration and status.
C. Observstory UI: current/history/graph/context routes, event replay, evidence inspector and download.
D. Source repo: proposal format, selected content coverage and shared assistant instructions.
E. Delivery: restore/restart checks, browser QA, updated README/demo, deployment runbook and rollback.
Execute as a single release branch series with coordinated contract ownership. Do not independently change schemas in both repos. Inspect PR #17 and the visual branch first.

## Definition of done
- New selected source revision reaches durable history automatically; all intermediate supported revisions retained.
- Duplicate delivery and restart do not duplicate records or lose pending indexing.
- Historical query excludes later knowledge; late correction and supersession retain evidence.
- Incomplete collection cannot produce false removals; current graph cannot contaminate historical answers.
- Claude and ChatGPT receive reproducible packets via at least one actually verified read channel each; distinguish manual file handoff from live connector.
- Reviewed proposal influences subsequent context; unreviewed proposal remains labelled.
- Public export contains only allowed material; hostile source text cannot execute as HTML or instruction.
- Now/history/graph/context work at desktop/mobile with keyboard and reduced motion; tests cover meaningful state failures.
- Existing snapshot/query contracts and consumer tests still pass; backup restore and rollback documented.
- README tells the real project story and labels unavailable features.

## Limits
This release is project memory with a controlled return path. It is not universal autonomous learning, a full temporal semantic reasoning engine, a new agent orchestrator or a guarantee of truth.
No new graph database, parallel extraction framework or model provider is required.
Code is not implemented or deployed by this specification. Host state, compatible provider access and active branches must be established by the NUC implementation session.
