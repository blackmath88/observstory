# Perplexity sparring brief — Observstory Project Knowledge

Copy the prompt below into Perplexity. Prepared 31 October 2026. This is a research task; no research execution or findings are implied by this file.

---

Act as a critical product/architecture sparring partner. Research the proposed feature below and improve or reject it before implementation. Do not simply endorse our preferred tools or produce another generic RAG overview.

## Read first

Proposal:
https://github.com/blackmath88/observstory/blob/docs/project-knowledge-concept/docs/project-knowledge/CONCEPT-AND-BUILD-PLAN.md

Existing boundaries:
https://github.com/blackmath88/observstory/blob/main/ARCHITECTURE.md
https://github.com/blackmath88/observstory/blob/main/AGENTS.md
https://github.com/blackmath88/observstory/blob/main/docs/definition/system-boundary.md
https://github.com/blackmath88/observstory/blob/main/docs/integrations/weavr.md

Consumer/backend:
https://github.com/blackmath88/baselhack26-knowledge-lab
Inspect feat/knowledge-lab-v1-nuc-continuation and its latest handoff, not only main's planning docs.

First target:
https://github.com/blackmath88/baselhack26-open-presence

If any source is inaccessible, state the gap. Never imply unread code was inspected.

## Thesis to challenge

A hackathon repo holds evolving concepts, research, decisions, experiments and code. Each person's agent reconstructs context independently. A versioned, source-linked shared orientation layer may reduce wrong assumptions and context rebuilding.

Observstory currently derives collaboration state from repository metadata without LLMs. Proposed opt-in Project Knowledge adds explicit document records and links plus shared human/agent views. Knowledge Lab/LightRAG remains an optional external semantic retrieval backend.

Preserve the difference between observed activity, declared decisions and model interpretations. Do not expand Observstory into an agent controller. “Everybody can query it” does not prove agents use the same revision or follow decisions.

## Investigate

1. Is the user problem supported by research/real practice on team situation awareness, knowledge decay, decision rationale and agent context? Identify evidence and uncertainty; do not invent measured benefits.
2. Compare the proposal with a good README + ADRs + Git history + ordinary search. What incremental value actually requires a graph or RAG?
3. Inspect relevant existing implementations. Candidates: GitNexus, CodeGraphContext, Graphiti, documentation/ADR systems or better alternatives. Distinguish code structure, temporal memory and project meaning.
4. Should this be an opt-in Observstory module, a separate plugin, or only a Knowledge Lab consumer? Identify the smallest boundary respecting metadata-only/no-LLM defaults.
5. Challenge metadata/front matter: adoption burden, duplicate records, malformed inputs, ID stability, status vocabularies, source-of-authority and explicit confirmation.
6. Specify what “current concept” means across branches, superseded decisions, contradictory declarations, stale indexes and absent history. Do not use latest timestamp as a substitute for authority.
7. Examine extract-vs-declare semantics: can model-discovered support/contradiction links be inspected without becoming accepted truth?
8. Design minimal import/query/freshness contracts without new infrastructure. Address updates/deletions, duplicate delivery, immutable source references and reproducible queries.
9. For static GitHub Pages, what can work entirely from artifacts? What must stay authenticated/private? Do not put service keys in static pages.
10. Define a realistic two-agent test and a baseline. How would we detect wrong confidence, stale context or no improvement? Shared facts are not the same as shared private model context.

Use primary sources for technical claims and original research for empirical assertions. Inspect actual repositories and specific files where useful. Cite exact URLs and dates. Distinguish implemented features from maintainer claims, proposals and your inference.

## Deliver

A. Strongest objection and concise go / modify / reject recommendation.
B. A clearer thesis in one paragraph, stating user, trigger, mechanism and falsifiable benefit.
C. Comparison of three architectures, including the simplest non-graph baseline.
D. Responsibility/contract table for Observstory, source repos, Knowledge Lab and agents.
E. Up to five high-impact changes to our proposal, each with rationale and evidence.
F. Revised build plan: a first 90-minute experiment, then small gated milestones with observable acceptance checks.
G. One concrete walkthrough: new research changes a concept, a human confirms a decision, two agents see branch-scoped current state and evidence.
H. What not to build this weekend.
I. Sources and unresolved evidence gaps.

Keep the answer selective and actionable. Rough effort estimates must be labelled assumptions. Do not install anything, change the architecture, launch agents, call paid model services or implement code.

## Delivery

If your available tools provide authenticated GitHub write access, write only:
docs/project-knowledge/PERPLEXITY-SPARRING.md
on branch docs/project-knowledge-concept of blackmath88/observstory.
Read any existing destination first and preserve human changes.
Return a verified commit/file link. Do not merge or deploy.

If writing is unavailable, complete the research and return the full Markdown report with that intended destination. Read access or push-permission metadata alone is not proof that a write occurred.

Execute the research now; do not return merely a plan to research.
