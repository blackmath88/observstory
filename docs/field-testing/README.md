# Field testing Observstory in real repositories

Observstory's internal fixtures and precision studies test signal behavior. External installations test a different question:

> Does the typed project model remain useful, explainable and operationally reasonable in a real repository with its own topology and working style?

A consumer can therefore run a **slow field-evaluation loop** over the generated snapshot.

```text
real repository
   ↓
Observstory collect + derive
   ↓
snapshot.json
   ↓
consumer expectations
   ↓
field evaluation
   ↓
PASS / WARN / INFO / FAIL
   ↓
framework improvement candidates
   ↓
manual upstream review
```

## Boundary

Field evaluation is deliberately separate from the core signal engine.

A consumer may test:

- required/custom lanes are present;
- fallback/Other usage stays understandable;
- collection is not degraded;
- API-call cost stays inside a project budget;
- declared coordination is present when expected;
- every signal carries evidence and rule provenance;
- summary fields remain internally consistent;
- project-specific semantics remain understandable.

It should **not** automatically modify Observstory rules.

## Why this belongs outside the hourly/event loop

Repository state should reconcile quickly.

Framework quality does not need the same cadence.

Recommended consumer cadence:

- manual after integration/model changes;
- weekly for long-running dogfood repositories.

## Candidate pattern

A field evaluator can emit a typed candidate such as:

```json
{
  "status": "CANDIDATE",
  "title": "Distinguish unmerged work from active landed streams",
  "evidence": {
    "in_flight": 0,
    "direct_streams": ["direct:maintainer"],
    "burst": ["sig:burst:..."]
  },
  "suggested_upstream": "Expose active/recent work streams separately or clarify the in-flight label."
}
```

The candidate is evidence for an upstream discussion, not a self-authorizing change.

## First external dogfood

The first implementation of this pattern lives in:

https://github.com/blackmath88/accessibility-red-team

It runs Observstory as the repository-level build observatory and evaluates it weekly/manually against project-specific expectations.

See [accessibility-red-team.md](accessibility-red-team.md).
