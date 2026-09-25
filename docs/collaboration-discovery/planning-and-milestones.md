# Planning and milestones

## What a 48-hour project needs that a calendar doesn't

| Need | Calendar | What's missing |
|---|---|---|
| **Now**, and the next hard gate | shows events | no sense of "what is the next thing that changes the rules" |
| Hard vs soft times | all events look alike | a *gate* (submission, freeze) is different from a check-in |
| What remains before the gate | nothing | the connection between the gate and open work |
| Freeze semantics | nothing | "after 20:00, `src/` should only get fixes": a rule about an area, not a meeting |
| Check-ins as sources of decisions | an event | the decisions and commitments that came out of it |

## Representation options

| Option | Fits | Rejected because |
|---|---|---|
| Gantt / dependency plan | long projects | too much upkeep; 48 hours don't need critical-path maths |
| Calendar | meetings | flattens gates and check-ins into the same thing |
| State machine (phases) | "build → freeze → polish → submit" | too rigid: teams freeze areas, not whole projects |
| Checklist | commitments | has no time |
| **Mission rail (chosen for exploration)** | NOW, gates, check-ins, commitments with due times | a single horizontal line: glanceable, no upkeep beyond the declarations themselves |

## Milestone types that earn a place

- **gate**: a hard time. Kinds: `freeze` (optionally scoped to areas), `submission`, `demo`. Only gates can be *passed*.
- **checkpoint**: a check-in or expert review. Soft: it's where decisions and commitments come from.

Everything else (sprints, phases, estimates) is rejected for v1.
