# System Map v0

> Architecture is modeled as semantic project knowledge, not as pixel coordinates.

System Map is an experimental Observstory module for projects that need a living architecture artifact that is both easy to review in Git and pleasant to explore interactively.

It deliberately does **not** change Observstory's snapshot boundary:

```text
DECLARED / INFERRED SYSTEM MODEL              OBSERVED REPOSITORY STATE
architecture/system.json                      observstory.snapshot/v1
        │                                              │
        ├────────────── separate evidence kinds ───────┤
        │                                              │
        ▼                                              ▼
   architecture view                         repository project map
```

A future reconciliation layer may compare the two, but declared architecture never becomes observed truth merely because it is rendered by Observstory.

## Canonical artifact

```text
architecture/
├── system.json    canonical semantic model
├── system.mmd     generated GitHub/README-friendly Mermaid
└── system.html    generated interactive explorer/editor
```

The canonical file has **no coordinates**. Renderers own placement.

Minimal example:

```json
{
  "schema": "observstory.system-map/v0",
  "title": "Example",
  "purpose": "Show the flow from source to interpretation.",
  "groups": [
    { "id": "input", "label": "Input", "order": 1 },
    { "id": "core", "label": "Core", "order": 2 }
  ],
  "nodes": [
    {
      "id": "specimen",
      "kind": "domain",
      "label": "Specimen",
      "group": "input",
      "status": "established",
      "basis": "human-declared"
    },
    {
      "id": "observation",
      "kind": "domain",
      "label": "Observation",
      "group": "core",
      "status": "candidate",
      "basis": "research",
      "evidence": [
        { "ref": "docs/research.md", "kind": "research" }
      ]
    }
  ],
  "edges": [
    {
      "from": "specimen",
      "to": "observation",
      "kind": "produces",
      "status": "candidate",
      "basis": "research"
    }
  ]
}
```

## Epistemic state

Nodes and edges can carry:

### Status

- `observed` — directly supported by repository or runtime evidence.
- `established` — accepted project architecture.
- `candidate` — plausible but not yet accepted.
- `questioned` — intentionally under challenge.
- `deprecated` — retained for history but no longer current.

### Basis

- `human-declared`
- `repository-evidence`
- `research`
- `experiment`
- `inference`

This is the important difference from a normal diagram. A box can say not only **what** it represents, but **how we know** that it belongs in the current model.

## One model, many views

A System Map can declare views:

```json
{
  "id": "evidence-flow",
  "label": "Evidence flow",
  "include": ["specimen", "raw-ooxml", "observation", "semantic-diff"],
  "focus": "data_flow"
}
```

Views do not duplicate architecture. They select a lens over one semantic model.

## Interactive HTML

The generated HTML is intentionally dependency-free and local-first.

It supports:

- semantic status filters;
- declared views;
- click-to-inspect relationships and evidence;
- an **Edit semantics** mode for label/description/status/basis;
- export of the edited semantic JSON.

The editor does not persist node positions. Moving boxes is not architecture.

## Build

From an Observstory checkout:

```bash
python3 -m src.observstory.system_map architecture/system.json --out architecture
```

This writes `system.mmd` and `system.html`.

## README use

GitHub renders Mermaid natively, so the generated `system.mmd` can be copied into a Mermaid code block when a fully inline README view is desired.

Alternatively, link the interactive artifact:

```markdown
[Open the interactive architecture map](architecture/system.html)
```

## Future reconciliation

The valuable next step is not automatic architecture discovery. It is **declared vs observed reconciliation**.

Examples:

```text
DECLARED
UI → Adapter Registry → Observation

OBSERVED
UI imports parser directly

ARCHITECTURE CUE
Declared adapter boundary may be bypassed.
```

or:

```text
DECLARED
Observation Store

OBSERVED
No matching package/module exists yet.

STATUS
Declared, not yet materialized.
```

Those must remain evidence-backed cues, not assertions that the declared model is correct.

## Product boundary

System Map may help people reason about architecture. It does not:

- route providers;
- dispatch Missions;
- decide what implementation is allowed;
- convert architecture questions into authority;
- make Weavr policy decisions.

The standing boundary remains:

> **Observstory observes and visualizes evidence; Weavr decides; runtimes act.**
