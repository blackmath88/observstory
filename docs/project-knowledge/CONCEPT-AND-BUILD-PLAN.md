# Project Knowledge — thesis, concept and build plan

31 October 2026 · **Proposal for sparring, not implemented functionality.**

## Thesis

In a fast-moving project, the repository accumulates more than code: concepts, research, experiments, decisions and handoffs. People and their agents repeatedly reconstruct that understanding from different documents and conversations. Access to the same files does not guarantee the same interpretation, branch context or knowledge of what changed.

**Working thesis:** a versioned, source-linked orientation layer can help humans and agents reconstruct a consistent project picture: what we are trying to do, what has been decided, why, what changed and what remains uncertain.

The graph is a means to connect evidence, not the goal or an authority. The benefit must beat a maintained README, decision log, direct Git search and a normal RAG baseline.

## Problem and first consumer

A teammate's agent starts implementing an old idea while the concept has changed in another chat and a newer repo document. Another agent knows the change but not the research behind it. Neither necessarily sees the other branch's ongoing work.

First consumer: [baselhack26-open-presence](https://github.com/blackmath88/baselhack26-open-presence). Its evolving concepts, research and chat handoffs are suitable real inputs. [Knowledge Lab](https://github.com/blackmath88/baselhack26-knowledge-lab) provides the experimental NUC backend.

This is broader than code navigation. A symbol/call graph can be added later; it cannot replace conceptual history or declared decisions.

## Proposed product boundary

Observstory already produces evidence-backed collaboration state. Project Knowledge extends orientation with opt-in document records. It does not dispatch agents, select providers, allocate missions, enforce team decisions or acquire merge authority.

| Component | Owns | Does not establish |
| --- | --- | --- |
| Existing Observstory | Current repository activity, overlap, waiting, declared coordination, human/agent projections | Semantic truth of documents |
| Optional Project Knowledge module | Explicit records, links, revisions, current-view selection and deterministic queries | Human agreement merely because a model says “accepted” |
| Knowledge Lab | Preserved sources, indexing jobs, LightRAG retrieval and extracted relationships | Authoritative project state or live coordination |
| Agents/humans | Interpret evidence and make decisions under existing governance | A common view without actually refreshing it |

The metadata-only/no-LLM v1 contract remains unchanged by default. Reading selected contents requires explicit configuration. LLM use remains external and optional. Use a separate producer-owned `observstory.knowledge/v1` artifact (proposed name), not an unreviewed breaking change to `observstory.snapshot/v1`. No renderer or MCP adapter invents state the other consumers cannot inspect.

## Two kinds of relationships

**Explicit:** a document declares its ID/type/status, references another record, or says it supersedes a decision. Parsing this is deterministic.

**Extracted:** a model suggests a conceptual relationship or apparent contradiction from passages. Retain source passages, model/version, extraction time and interpretation status. Do not upgrade it into an explicit team decision.

“Declared accepted by this record” is not independent proof that a human approved it. Preserve authorship/confirmation evidence when available. Never translate imported content into action permissions.

Example: research informs a concept; an experiment tests an assumption; a decision selects an option; a later decision supersedes it. “Related to” is not “supports”; missing support remains missing.

## Input convention

Accept ordinary Markdown first. Minimal optional front matter:

```yaml
---
id: concept-portable-context
type: concept
status: exploring
supersedes: []
related:
  - research-pdf-history
---
```

Initial types: concept, research, decision, experiment, handoff. Define status vocabulary per type before implementation; do not give research the same lifecycle as decisions. Add bounded evidence references and human-confirmation metadata as needed, not mandatory bureaucracy on every paragraph.

Plain Markdown appears as an unclassified document with a source-derived identifier, not as an automatically accepted concept. Handoffs preserve original text/JSON and are normalized through a versioned adapter. Knowledge Lab's existing chat schema and Observstory's coordination decisions must be mapped rather than silently duplicated.

Every record carries repository, source commit/ref, path, section/location, content hash and observation time. IDs are stable within a repository; cross-repo links use repository + ID. Renames preserve explicit IDs; duplicate IDs, invalid statuses, broken links and supersession cycles produce visible diagnostics.

## Currentness and branch context

Default-branch state and unmerged branch proposals remain separate. Return the requested ref, source commit, observation time and indexing watermark with every brief/query. Mixed-revision results are labelled. “Current” is scoped to a ref; it is not whichever document was ingested last.

A file's modification time or latest commit does not decide which competing concept wins. Explicit current/supersession declarations guide selection. Conflicting declarations yield “unresolved”, not an invented canonical answer.

Retain old revisions for history; default semantic queries must not silently use superseded content as current guidance. If the semantic index lags, show the new explicit state immediately and label retrieval stale.

## Interaction

Humans see a compact knowledge panel alongside existing work state: current concept candidates, decisions, open questions, research/evidence and changes. Selecting an item opens its declared/extracted basis and exact source.

Proposed deterministic queries:
- `project-brief`: explicit current picture with unresolved selection conflicts.
- `knowledge-changes-since`: additions, changes, removals, supersessions since an earlier snapshot/commit.
- `knowledge-record`: exact record plus evidence and relationships.

Optional `knowledge-search` delegates semantic retrieval to Knowledge Lab. Failure of that backend must not prevent the deterministic views. Ordinary HTTP/MCP is only transport; shared access is not guaranteed refresh or enforcement.

No credentials in generated Pages/HTML, no browser-to-private-NUC dependency for basic static views. Private source content must not leak into publicly published artifacts. Publish full-text passages only under an explicit audience/configuration decision.

## Build plan

### P0 — falsification and contract, before infrastructure

Create three fixture moments from a fictional project: an initial concept/decision, a revision on an unmerged branch, and an accepted successor on default branch. Preserve supporting research and one contradictory source.

Compare direct README/decision-log lookup with a hand-authored orientation view. Ask two fresh agents (or independent isolated sessions) to identify current direction, superseded choice, open question and evidence. Verify exact source answers manually.

Continue only if the added structure solves a demonstrated miss or reduces reconstruction work without lowering accuracy. If plain curated docs are sufficient, ship that plus an Observstory link panel.

### P1 — deterministic vertical slice in Observstory

Add disabled-by-default configuration for exact allowed Markdown/JSON paths, bounded file size and content exposure. Implement pure parsing/normalisation, schema validation and reference checking outside existing metadata ingestion. Parse YAML safely as data; choose a maintained parser or explicitly narrow supported syntax.

Produce separate knowledge artifact and queries. Extend UI with one accessible evidence panel using existing projection patterns. Avoid graph-canvas scope creep.

Acceptance: feature disabled reproduces existing behaviour; all existing tests/contracts pass; fixtures correctly separate branch proposals and declared decisions; cycles/duplicates/broken links are diagnosed; both human panel and query return the same IDs/status/source commits.

### P2 — useful live repo intake

Use the target repo's selected concept/research/plan files plus handoffs. Resolve contents at a consistent commit; keep explicit source selection and branch scope. Reuse pipeline refresh and API budgets where possible. No arbitrary repository crawling.

Persist snapshots externally when history queries need previous runs; current stateless GitHub Actions do not provide durable history automatically. Define retained snapshot IDs and compare endpoints before promising “changes since”.

Acceptance: push one concept update, rebuild, and retrieve the new state and its diff without a model. Missing/degraded intake stays visible. Do not edit target concepts simply to make parsing pass.

### P3 — optional Knowledge Lab bridge

Version a small ingest/query contract with repo/ref/commit/hash identifiers, source-to-passage references and a freshness watermark. Prefer idempotent polling/transfer of immutable artifacts initially; public webhooks are unnecessary.

NUC source store/indexing are consumer-owned. Exact original passages remain retrievable even if extracted relationships are poor. Test duplicate delivery, failed indexing, changed/deleted sources and old-index results.

Acceptance: explicit current view works with backend down; semantic answer links to the original revision; index watermark is shown; no claim of “latest” after a failed update. Actual live inference requires the existing user-authorized route/budget; fixtures do not prove live quality.

### P4 — two-agent alignment demonstration

Agent A proposes a change, a person explicitly confirms it, then it lands. Agent B refreshes its orientation and identifies the accepted decision, source and relevant current overlap.

Record what B knew before/after. Test a stale client and competing branch; it must disclose its stale/ref context. Do not claim read access guarantees obedience, conflict prevention or synchronized private contexts.

Completion: reproducible demo, brief setup, limitations and evidence. Read-only MCP can reuse these queries once HTTP/file contract works; no autonomous write-back needed.

## Non-goals and open decisions

No replacement of LightRAG, no mandatory second graph database, no generic orchestration platform, no automatic approval by model, no full-chat surveillance, no per-person scoring.

Questions to spar on: is front matter worth its maintenance cost? Could existing coordination + ADRs cover most needs? Should semantic integration stay entirely consumer-side? What is the smallest useful change/freshness contract? Does the concept belong in core Observstory, an optional module, or an adjacent adapter?

## Grounding

- [Existing architecture](../../ARCHITECTURE.md): typed snapshot boundary and pure derivation.
- [System boundary](../definition/system-boundary.md): metadata-only v1, optional interpretation justification.
- [Agent instructions](../../AGENTS.md): orientation without orchestration authority.
- [Weavr boundary](../integrations/weavr.md): producer-owned contracts; governance remains elsewhere.
- [Knowledge Lab](https://github.com/blackmath88/baselhack26-knowledge-lab): experimental storage/indexing consumer.
- [Open Presence](https://github.com/blackmath88/baselhack26-open-presence): first real use case.

These references establish existing intent, not completion of this proposed feature. No runtime or existing source behaviour is changed by this document.
