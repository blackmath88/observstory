# Vision: Observstory as a Semantic UI Compiler

Observstory began as repository observability for AI-assisted software work.

Its deeper architectural direction is broader:

> **State belongs to the project. Form belongs to the projection.**

The repository, its in-flight work, declarations, relationships, and evidence form the underlying state. The Project Map, Radar, agent queries, mission rail, and future views are projections over that state.

This means Observstory should not become a fixed dashboard with more widgets.

It should become a **semantic UI system**.

---

## 1. Current architecture

Observstory already follows this chain:

```text
GitHub evidence
      ↓
observations
      ↓
typed snapshot
      ↓
semantic scene
      ↓
Project Map
```

The important boundary is the typed snapshot.

The Project Map does not render GitHub objects directly. A compiler first derives visual semantics:

- zones
- groups
- nodes
- edges
- attention
- evidence
- declared collaboration state

The renderer then decides how those semantics become visible.

The scene deliberately contains no hand-authored coordinates.

That separation is the beginning of a semantic UI compiler.

---

## 2. From dashboard to projection

A conventional dashboard assumes a stable frame and fills it with current data.

Observstory should move in the opposite direction:

```text
project state
      ↓
semantic relations
      ↓
frame selection
      ↓
constrained composition
```

The shape of the interface should follow the shape of the project.

A software repository may naturally compose as:

```text
Intent → Build → Verify → Ship
```

A machine-learning repository may instead become:

```text
Data → Pipeline → Model → Eval → API → Docs
```

A hackathon may add:

- gates
- freezes
- commitments
- check-ins
- deadlines

The renderer remains the same. The semantic scene changes.

That is the product idea:

> **Do not design every screen by hand. Compile a useful frame from typed project state.**

---

## 3. Semantic UI compiler

A semantic UI compiler consumes project semantics and emits a constrained visual intermediate representation.

```text
typed project state
      ↓
semantic UI compiler
      ↓
scene IR
      ↓
HTML/CSS + SVG renderer
      ↓
interface
```

The scene grammar should remain deliberately small.

Current and likely primitives include:

```text
ZONE
GROUP
NODE
EDGE
ATTENTION
EVIDENCE
GATE
COMMITMENT
```

The semantic layer decides:

- what exists;
- what belongs together;
- what relation is meaningful;
- what needs attention;
- what is observed versus declared;
- what evidence supports the claim.

The renderer decides:

- placement;
- spacing;
- responsive composition;
- connector geometry;
- progressive disclosure;
- interaction.

This keeps product meaning out of the rendering layer.

---

## 4. Why this matters for AI-assisted development

AI-assisted software work creates more activity than a chronological feed or pull-request list can explain.

The useful state is not only a list of objects.

It is the relations between them:

- two work items change the same file;
- one change depends on another;
- a declared freeze conflicts with observed activity;
- a commitment has not started;
- a burst of machine-paced work is occurring;
- a project area is quiet while another becomes crowded.

These relations are semantic.

Once represented explicitly, they can support many views without creating multiple sources of truth.

```text
                    typed project state
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Project Map      Radar      Agent query
              │            │            │
              └──── same underlying state ────┘
```

Future views should follow the same rule.

---

## 5. The Delta connection

A snapshot explains current state.

A richer future system may also preserve finer-grained change semantics.

Instead of only:

```text
PR #12 touches store.py
PR #14 touches store.py
```

a delta-aware substrate could preserve:

```text
operation A changes persistence contract
operation B changes the same function
test fails
part of B is reverted
an alternate implementation appears
```

That would let Observstory compile interfaces not only from objects, but from the meaning of change over time.

The useful primitive set may therefore eventually become:

```text
ENTITY
RELATION
OPERATION
EVIDENCE
PROVENANCE
```

This is a longer-term direction, not a requirement for the current product.

---

## 6. Role of AI

A semantic UI system does not require an LLM to generate arbitrary HTML or frontend code.

A safer architecture is:

```text
messy project context
      ↓
deterministic rules and/or model interpretation
      ↓
typed frame intent
      ↓
semantic UI compiler
      ↓
bounded visual grammar
```

AI may help:

- identify emerging relations;
- suggest a useful frame;
- classify ambiguous intent;
- propose organization;
- summarize evidence.

But the resulting UI should remain:

- typed;
- inspectable;
- reversible;
- provenance-backed;
- bounded by a known grammar.

The model may suggest **what deserves a frame**.

It should not need unrestricted ownership of the frame itself.

---

## 7. Design principle

Dynamic does not mean unstable.

Generated interfaces must preserve:

- stable object identity;
- provenance;
- source links;
- predictable interaction;
- a way back to raw evidence;
- the distinction between observed, derived, inferred, proposed, and declared state.

Users should be able to understand why the interface looks the way it does.

The more adaptive the frame becomes, the stronger the audit model must become.

---

## 8. Working thesis

Observstory's long-term UI thesis is:

> **The project should own its semantic state, not a fixed dashboard. Observstory should compile task-appropriate, evidence-backed projections from that state.**

Or more compactly:

> **Semantic compiler:** intent → action  
> **Semantic UI compiler:** state → perception

Observstory is an experiment in the second half of that pair.

Its Project Map is not only a dashboard.

It is the first concrete proof that a project interface can be **compiled from semantics**.
