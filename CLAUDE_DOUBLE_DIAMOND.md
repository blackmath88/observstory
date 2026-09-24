# Claude Production Task — Observstory Double Diamond

## Role

You are acting as a **product designer + service designer + systems architect + senior prototyper**.

Your task is to develop **Observstory** using a Double Diamond design-thinking process while preserving the current architectural claim:

> Observstory turns repository activity into a typed shared project-state model that humans and coding agents can use as a common coordination surface.

Do not reduce this to a generic GitHub dashboard.

Do not start from UI features.

Do not assume MCP is the product.

The current architecture is:

```text
GitHub events + scheduled reconciliation
                |
                v
            collector
                |
                v
        typed project state
                |
        +-------+--------+
        |                |
        v                v
   human UI          API / MCP
```

The current MVP is a reusable GitHub Action which generates:

- repository health summary
- contributor activity
- recent commits
- pull requests
- issues
- typed project lanes
- shared-path overlap signals
- a versioned JSON snapshot
- a generated static dashboard

The intended product evolution is:

1. GitHub Action
2. GitHub App + hosted state service
3. MCP/API interfaces for agents
4. richer collaboration intelligence

The core problem is **making parallel creation legible again**, especially in AI-assisted development where multiple humans may each be working inside private coding-agent loops.

---

# Working method

Use the Double Diamond:

```text
DISCOVER  →  DEFINE  →  DEVELOP  →  DELIVER
diverge       converge     diverge       converge
```

You are expected to produce concrete repository artifacts, not only prose.

At the end of every phase:

1. record findings,
2. record assumptions,
3. record rejected alternatives,
4. state the decision,
5. state what evidence supports it,
6. identify what remains uncertain.

Prefer small proof-producing experiments over large speculative builds.

Do not rewrite the existing system unless evidence shows that the current architecture is wrong.

---

# DIAMOND 1 — PROBLEM

# Phase 1 — DISCOVER

## Goal

Understand the real collaboration problem Observstory should solve.

Research from the perspective of:

- hackathon teams
- small software teams
- AI-assisted development teams
- teams using multiple coding agents
- open-source maintainers
- project leads
- individual contributors

Investigate:

### A. Current coordination surfaces

Study what existing tools expose well or poorly:

- GitHub activity feeds
- GitHub Projects
- pull request dashboards
- Linear
- Jira
- GitHub Pulse / Insights
- Graphite / stacked PR tools
- GitHub Actions
- development analytics / engineering intelligence products
- agent orchestration tools
- coding-agent task dashboards
- multi-agent coding systems

The question is not:

> What features do these products have?

The question is:

> What collaboration state is still invisible?

### B. AI-era collaboration breakdowns

Look specifically for patterns such as:

- two people independently building the same thing
- finished monolithic contributions arriving without shared intermediate state
- architectural divergence
- duplicated agent work
- branches that represent conflicting interpretations
- decisions made inside private LLM conversations
- lack of awareness of who is changing which subsystem
- unclear ownership
- stale tasks
- orphaned work
- hidden dependencies
- late discovery of integration conflict
- difficulty reconstructing “how we got here”

### C. Observable signals

Determine what GitHub can actually tell us reliably.

Classify every candidate signal as:

- DIRECTLY OBSERVABLE
- DERIVED / INFERRED
- REQUIRES EXPLICIT USER INPUT
- NOT SAFELY KNOWABLE

Examples:

- commit
- changed path
- PR state
- branch
- issue
- CI status
- author
- reviewer
- timestamp
- label
- code ownership
- file co-editing
- likely overlap
- task intent
- active work
- dependency
- blocking relationship
- architectural decision
- handoff readiness

Do not silently promote inference into fact.

### D. Interviews-by-proxy / scenario analysis

Create at least 5 realistic user scenarios.

At minimum include:

1. 5-person hackathon team
2. two developers + coding agents
3. maintainer receiving parallel PRs
4. product lead trying to understand project state
5. contributor joining midway through a project

For each:

- what they need to know
- what GitHub already tells them
- what remains hard to see
- what Observstory could make visible
- what would become surveillance / overreach

### E. Product risks

Investigate:

- productivity scoring risk
- employee surveillance
- false inference
- gaming metrics
- API rate limits
- private repo concerns
- data retention
- contributor identity
- bots vs humans
- generated commits
- mono-repos
- squash merges
- rebases
- force-pushes
- branch-heavy teams
- GitHub Actions schedule reliability

## Discover deliverables

Create:

```text
docs/discovery/
  problem-space.md
  competitive-landscape.md
  ai-collaboration-failures.md
  observable-signals.md
  scenarios.md
  risks.md
```

And:

```text
docs/discovery/opportunity-map.json
```

The JSON should be machine-readable and rank **problems**, not proposed features.

---

# Phase 2 — DEFINE

## Goal

Converge on the smallest valuable product.

Do not proceed directly from “things GitHub exposes” to “dashboard cards”.

Synthesize the discovery work into:

## A. Core job to be done

Write one primary JTBD.

Format:

> When ________, I want ________, so that ________.

Then write 3–5 secondary JTBDs.

## B. Product thesis

Produce:

- one-sentence problem
- one-sentence product claim
- one-sentence non-goal
- one-sentence proof requirement

Example structure:

> Shared software work is difficult to coordinate because ...
>
> Observstory ...
>
> Observstory does not ...
>
> We know it works when ...

Do not copy this wording mechanically.

## C. System boundary

Explicitly decide what belongs in:

- GitHub ingestion
- deterministic derivation
- heuristics
- human-authored project configuration
- optional LLM interpretation
- UI
- MCP/API

For every LLM use, justify why deterministic code is insufficient.

## D. Typed project model

Review and evolve the current snapshot schema.

Ask whether the project model should include concepts such as:

- Observation
- Actor
- Workstream
- Lane
- Change
- Artifact
- Branch
- PullRequest
- Issue
- Decision
- Dependency
- Overlap
- OpenLoop
- Handoff
- Evidence
- Confidence

Do not add types merely because they sound elegant.

Produce a minimal schema capable of supporting the defined product claim.

## E. Core signals

Define no more than 5 high-value derived signals for v1.

Each signal must include:

- name
- user question answered
- input evidence
- deterministic or heuristic logic
- false-positive risk
- UI representation
- API/MCP representation
- test method

Possible examples to evaluate, not automatically accept:

- overlap
- divergence
- stale work
- orphaned work
- unresolved integration
- dependency risk
- handoff readiness

## F. MVP decision

State exactly what v1 is.

Use:

```text
MUST
SHOULD
NOT YET
NEVER / ANTI-GOAL
```

## Define deliverables

Create:

```text
docs/definition/
  product-thesis.md
  jobs-to-be-done.md
  system-boundary.md
  v1-scope.md
  signal-specs.md
  design-principles.md
```

Create/update:

```text
schema/
  snapshot-v1.json
```

Create:

```text
DECISIONS.md
```

with ADR-style entries for major product decisions.

---

# DIAMOND 2 — SOLUTION

# Phase 3 — DEVELOP

## Goal

Explore several ways to make the defined project state understandable and useful.

Do not build only one UI immediately.

## A. Generate 3 distinct product directions

At minimum:

### Direction 1 — Project Radar

A glanceable control center focused on:

- current state
- hot areas
- active workstreams
- collisions
- open loops

### Direction 2 — Project Timeline / Playback

A historical view answering:

> What changed in the project over time?

Show snapshots, state transitions, and emergence of overlap/divergence.

### Direction 3 — Agent Coordination Surface

A machine-first interface where coding agents can query project state before acting.

Example interaction:

```text
agent asks:
"What is active around src/conversation?"

Observstory answers:
- active contributors
- recent changes
- open PRs
- relevant lane
- overlap evidence
- unresolved integration
```

You may propose a fourth direction if discovery supports it.

## B. Prototype cheaply

For each direction create a lightweight prototype or representation.

Possible formats:

- static HTML
- JSON interaction examples
- diagrams
- screenshots generated from HTML
- mock API responses
- CLI output
- MCP tool contract examples

Do not build full production infrastructure for all directions.

## C. Compare directions

Evaluate each against:

- usefulness in under 10 seconds
- explainability
- evidence traceability
- cognitive load
- install friction
- project-manager burden
- agent usefulness
- privacy
- ability to work without manual maintenance
- feasibility

Do **not** simply score and choose by arithmetic.

Explain tradeoffs.

## D. Test the strongest signals

Implement small experiments that falsify or support the v1 signals.

At minimum test:

1. two contributors touching the same subsystem
2. parallel non-overlapping work
3. stale branch / inactive work
4. PR waiting on another change
5. agent-generated rapid commit activity

Create fixtures if needed.

## E. UI language

Develop a design language that feels like:

- observatory
- instrument panel
- project topology
- radar
- evidence
- temporal state

Avoid:

- generic SaaS dashboard aesthetics
- productivity leaderboards
- gamification
- excessive traffic-light scoring
- giant “AI insight” cards

The system should feel calm, precise and evidence-first.

## Develop deliverables

Create:

```text
prototypes/
  radar/
  timeline/
  agent-surface/
```

Create:

```text
docs/development/
  concept-comparison.md
  experiment-results.md
  ui-language.md
```

Add fixtures/tests for derived signals.

---

# Phase 4 — DELIVER

## Goal

Ship one coherent Observstory v1 that can be added to another repository with minimal effort.

## A. Installation experience

Target:

> I add Observstory to a repository and get a useful control center without manually maintaining a project board.

Support the simplest viable install.

For the current architecture this likely means:

```yaml
- uses: blackmath88/observstory@<version>
```

If configuration is absent, useful defaults must exist.

If configuration is present, the repo can define its own lanes.

## B. Production implementation

Harden:

- collector
- typed state
- schema validation
- lane derivation
- signal derivation
- static dashboard
- error handling
- rate-limit awareness
- tests
- example repository configuration

Do not prematurely build the hosted GitHub App unless the Action architecture fundamentally blocks the v1 proof.

## C. Self-observation

Observstory must run against its own repository.

Its own dashboard should demonstrate:

- typed lanes
- activity
- contributor state
- signal derivation
- provenance
- machine-readable snapshot

## D. Demo scenario

Create one convincing end-to-end demonstration.

Suggested scenario:

### Before

Two contributors appear to be working normally.

### Development

Both independently begin changing the same subsystem.

### Observstory

The project radar surfaces a shared-path / workstream overlap with evidence.

### Resolution

One contributor moves to evaluation or integration work.

### Result

The tool does not judge who is right; it makes coordination necessary earlier.

## E. Agent proof

Create an MCP/API contract proof — not necessarily a hosted MCP server yet.

Show how an agent could ask:

- what changed since my last run?
- who is active in this subsystem?
- what work overlaps my proposed task?
- what open loops exist?
- what is ready for handoff?

Return evidence-backed structured data.

## F. Documentation

The README should communicate within 30 seconds:

1. problem
2. product
3. architecture
4. install
5. screenshot/demo
6. what makes this different from GitHub Projects
7. what MCP does and does not do

## Deliver deliverables

Required:

```text
README.md
ARCHITECTURE.md
DECISIONS.md
ROADMAP.md

docs/
  discovery/
  definition/
  development/
  demo/

schema/
  snapshot-v1.json

tests/
fixtures/
```

Plus working v1 implementation.

---

# Product principles

Use these as guardrails.

## 1. Observe the project, not the person

Observstory must not become employee monitoring.

Prefer:

> “Three active changes touch the same subsystem.”

over:

> “Patrick has a low collaboration score.”

## 2. Evidence before inference

Every derived signal should be inspectable back to GitHub evidence.

## 3. State before dashboard

The typed project-state model is more important than any specific UI.

## 4. Configuration is optional

Zero-config should be useful.

Configuration should improve semantics.

## 5. Human and agent views share one source of truth

Do not create a separate “AI interpretation layer” with incompatible state.

## 6. Project management without project-management maintenance

Do not require people to constantly update cards merely so the tool knows what is happening.

## 7. Surface coordination needs, not management judgments

Observstory identifies places that deserve human attention.

It does not decide who is productive, who owns the project, or whose approach is correct.

---

# Collaboration protocol

You are working in parallel with other coding agents.

Therefore:

1. Read the current repository before changing architecture.
2. Prefer self-contained execution objects.
3. Avoid large rewrites across unrelated files.
4. Commit coherent chunks.
5. Record major decisions in `DECISIONS.md`.
6. Leave the repository in a runnable state after each chunk.
7. Do not delete existing work merely because you prefer another implementation.
8. If you encounter architectural uncertainty, document it instead of silently deciding.
9. Use clear commit messages prefixed with the phase:
   - `discover:`
   - `define:`
   - `develop:`
   - `deliver:`

---

# Execution order

Work in this order:

## Chunk 1
DISCOVER only.

Commit the discovery artifacts.

## Checkpoint 1

Before implementation, summarize:

- strongest user problem
- strongest evidence
- surprising finding
- what existing tools already solve
- what remains unsolved
- your proposed problem definition

Then continue unless discovery invalidates the Observstory thesis.

## Chunk 2
DEFINE.

Commit definition, system boundary, v1 signal specs, schema proposal and ADRs.

## Checkpoint 2

State the exact v1 product in 5–10 lines.

## Chunk 3
DEVELOP.

Build the three lightweight product directions and signal experiments.

Commit them separately where practical.

## Checkpoint 3

Select the coherent direction and explain the tradeoff.

## Chunk 4
DELIVER.

Implement and harden the selected v1.

Run tests.

Dogfood the tool against Observstory itself.

Produce demo artifacts.

---

# Final acceptance criteria

The work is complete only if a new person can answer all of these from the repository:

1. What collaboration problem does Observstory solve?
2. Why does GitHub itself not already solve it?
3. What is directly observed vs inferred?
4. What is the typed project model?
5. Which signals matter in v1?
6. How do I install it?
7. What useful thing appears without manual configuration?
8. How does the UI expose evidence?
9. How would a coding agent use the same state?
10. How does the design avoid becoming surveillance?
11. What experiment shows that Observstory provides value?
12. What should be built next?

The final result should feel less like a dashboard bolted onto GitHub and more like a **shared situational-awareness layer for AI-assisted software work**.
