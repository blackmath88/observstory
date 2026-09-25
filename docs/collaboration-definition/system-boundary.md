# System boundary: collaboration state

**Chosen:** option 2, *repo observability + declared collaboration state*. Not option 3 (a
project operating surface / PM suite).

```text
check-in notes / transcript text
        │  extractor (deterministic by default; an LLM adapter may be added)   → PROPOSED items
        ▼
human review + confirm (a named confirmer)                                     → DECLARED items
        ▼
.observstory/coordination.json   (in the repository: versioned, reviewable)
        ▼  read by the Action, next to observations.json
derive: reconcile DECLARED with OBSERVED work items and commits              → snapshot.coordination
        ▼
scene: mission rail + commitments + cues          → Project Map (index.html)   · agents: query
```

| Layer | Owns | Must not |
|---|---|---|
| Extractor | notes → proposed items, each with the source line | write declared state; infer owners from speakers; run without being asked |
| Confirmation | promoting proposed → declared, recording who confirmed it and when | happen implicitly |
| Coordination file | the declared record | hold audio or full transcripts; hold statuses that need upkeep |
| Reconciliation (derive) | deterministic relations R1–R4 | infer links; judge people; alter repository signals |
| Scene / renderer | rail, commitment states, cues, inspector | compute anything; show proposed items as fact |

### What Observstory will not become
Not a task manager (no board, no assignments, no status upkeep, no priorities or estimates). Not
a meeting recorder in v1. Not a calendar. Not a notification system. Not a place that scores people.
