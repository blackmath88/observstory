# Weavr integration

## Purpose

Observstory and Weavr are complementary.

The intended boundary is:

> **Observstory observes. Weavr decides. Agents act.**

Observstory remains the repository-observability system. Weavr may consume its typed snapshot as orchestration evidence.

## Product boundary

Observstory's public machine boundary remains:

    observstory.snapshot/v1

defined by:

    schema/snapshot-v1.json

No Weavr-specific fields are added to the snapshot just to satisfy orchestration.

If Weavr needs a smaller shape, it owns that projection in the Weavr repository.

## Responsibilities

### Observstory

Owns:

- GitHub/repository collection;
- normalized observations;
- pure derivation;
- work items;
- areas/lanes;
- overlap, stale, waiting and burst signals;
- declared collaboration state;
- evidence and provenance;
- human/agent projections over the snapshot.

Question:

> **What is happening, and what evidence supports it?**

### Weavr

Owns:

- project intent;
- missions;
- autonomy/continuation policy;
- provider routing;
- runtime projection;
- legal next actions;
- review/integration policy;
- evaluation and learning proposals.

Question:

> **Given intent + policy + observed state, what may happen next?**

### Execution systems

Herdr, native CLIs and provider clouds perform the work.

## Integration loop

    GitHub
      ↓
    Observstory collection + derivation
      ↓
    observstory/data/snapshot.json
      ↓
    Weavr Observstory adapter
      ↓
    mission / autonomy / decision compiler
      ↓
    agent or runner
      ↓
    GitHub changes
      ↓
    next Observstory run

## Optional by design

A repository should not need Weavr in order to use Observstory.

A repository should not need Observstory in order to use Weavr.

When both are present, Weavr gets richer repository-coordination evidence.

## Discovery conventions

Weavr may detect Observstory through:

- observstory/data/snapshot.json;
- .github/workflows/observstory.yml;
- .observstory/coordination.json.

The snapshot file is the authoritative machine-readable observation state when available.

The workflow file only proves configuration, not freshness.

## Consumption rules

A Weavr consumer should:

1. require schema == observstory.snapshot/v1;
2. treat generated_at and provenance/degraded state as part of evidence quality;
3. preserve signal IDs and evidence references;
4. never convert a heuristic signal into an unqualified fact;
5. preserve Observstory's observed/derived/heuristic/declared distinctions;
6. avoid per-person performance interpretation.

## Example orchestration use

Observstory might expose a high-confidence overlap signal affecting app/src/runtime.

Weavr may then deterministically compile:

    mission writes app/src/runtime
    + high-confidence overlap
    + autonomy policy says "no overlapping writes without review"
    → NEEDS_HUMAN

The orchestration decision belongs to Weavr.

The overlap claim and evidence belong to Observstory.

## Evaluation use

Weavr may attach references to Observstory state when recording a trial:

    trial outcome
    + provider
    + tests/review
    + observstory signal ids

This allows evaluation of coordination conditions without changing Observstory into an evaluator of people or agents.

Examples:

- repeated rework under overlap;
- long review cycles when stale branches touch mission paths;
- lower intervention rate when work is isolated.

Any optimization belongs to Weavr's policy-learning layer.

## What Observstory must not become

The integration does not expand Observstory into:

- mission routing;
- coding-agent control;
- provider selection;
- automatic merge policy;
- task scheduling;
- agent performance scoring.

That would violate the existing system boundary.

## Future delivery

The first integration can read the local snapshot file.

Later delivery options may include:

- observstory query ...;
- MCP over the same snapshot;
- REST from a hosted Observstory service.

Those are transport choices. The snapshot remains the product boundary.
