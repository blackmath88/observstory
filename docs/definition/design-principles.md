# Design principles (operational)

The brief's seven principles, turned into rules that can be checked in code or review.

| Principle | Checkable rule |
|---|---|
| 1. Observe the project, not the person | `signal.subject.kind ∈ {area, work_item}`. No per-person numbers in the UI (no commit counts, no line counts). Actor lists are sorted alphabetically, never by activity. Enforced by `tests/test_principles.py` |
| 2. Evidence before inference | Every signal has ≥1 `evidence` entry, a `basis` and a `confidence`. Every work item and commit has a `url`. Enforced by the schema and tests |
| 3. State before dashboard | The renderer reads only `snapshot.json`. It can be re-run offline (`observstory render`). The agent CLI reads the same file |
| 4. Configuration is optional | With no config file, lanes fall back to defaults and areas come from paths. Test: `test_zero_config_produces_areas_and_signals` |
| 5. One source of truth | UI and agent queries are both pure functions of `snapshot.json`. No separate AI layer |
| 6. No PM maintenance | Nothing in v1 needs cards, statuses or labels to be updated. Declared inputs (depends-on text, agent trailers) are *enrichments* people write anyway |
| 7. Coordination needs, not judgments | Signal copy uses neutral nouns ("2 work items touch …"). Banned words in UI copy: *score, productivity, top contributor, slow, blocker (of a person)* |
