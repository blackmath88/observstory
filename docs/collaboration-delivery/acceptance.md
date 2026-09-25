# Acceptance: collaboration state (issue #7)

The issue's twelve questions, answered briefly, each with where to look.

**1. What collaboration problem are we solving?**
In fast projects, the agreements a team makes out loud (a freeze at 12:00, "Dana has the evals by
16:00") are never compared with what the repository then does, so crossed freezes and unstarted
commitments surface at the demo. → [product-thesis.md](../collaboration-definition/product-thesis.md), [problem-space.md](../collaboration-discovery/problem-space.md)

**2. Why isn't GitHub Projects / Linear / Notion enough?**
They store intent and some sync a task with its PR, but none has a time-scoped rule about an
*area of code* (a freeze, a gate) checked against activity, and all depend on someone keeping the
board current. Observstory needs no upkeep beyond a confirmed check-in, and a commitment can
link to a tracker issue. → [competitive-landscape.md](../collaboration-discovery/competitive-landscape.md)

**3. What is observed, proposed and declared?**
*Observed*: repository facts (work items, commits, paths, times). *Proposed*: items the extractor
found in check-in notes, with their source line. *Declared*: proposed items a named person
confirmed (`confirmed_by`, `confirmed_at`). Only declared items reach the rail and reconciliation.
→ [typed-model.md](../collaboration-definition/typed-model.md), ADR-029

**4. What new typed objects exist?**
Session, Gate (checkpoint, freeze, submission, demo, gate), Commitment (text, owner as declared,
due, links) and Decision (text, areas), plus open questions kept on the session and a Link
(pr, branch, path, url). → [`schema/coordination-v1.json`](../../schema/coordination-v1.json)

**5. How does a check-in become project state?**
`checkin propose` (notes → proposed items) → `checkin pending` (review) → `checkin confirm S --by NAME`
→ commit `.observstory/coordination.json` → the Action reconciles on its next run.
→ [README.md](README.md#the-flow), `tests/test_coordination.py::CheckinCli`

**6. What requires human confirmation?**
Every item. Nothing the extractor finds is shown or reconciled until a named person confirms it;
confirming without a name fails. Links are never inferred either: they are written in the notes.

**7. How are milestones represented?**
As gates on a mission rail above the Project Map: NOW, check-ins, gates (the next one
emphasised, in orange when it has a cue) and commitment due times as diamonds coloured by
observed state. It is a rail, not a calendar or Gantt chart. → ADR-032, [ui-integration.md](../collaboration-development/ui-integration.md)

**8. How does declared intent relate to repo state?**
Through explicit links (a PR, a branch, a path) and gate scopes (paths). `reconcile()` is pure and
deterministic: it sets each commitment's state from its linked work and compares gate times with
commit times. The result is `snapshot.coordination`, kept apart from `snapshot.signals`. → ADR-030

**9. What reconciliation cue is actually useful?**
`freeze.changed_after` ("Freeze src/core/ at 12:00: src/core/ changed afterwards in #12, a direct
push") is the one no surveyed tool gives. `commitment.unstarted` (half the time to due has passed
with no linked work) catches evaporated commitments. `gate.passed_with_open_work` covers the
rest. → [reconciliation-rules.md](../collaboration-definition/reconciliation-rules.md), [experiment-results.md](../collaboration-development/experiment-results.md)

**10. How is surveillance avoided?**
No recording or transcription; notes are text the team chose to write. Cues name work ("#12", "a
direct push"), never people; the owner is shown only as declared. There are no per-person rates,
counts or histories, and `tests/test_principles.py` still holds for every snapshot. The file lives
in the repository, where everyone can see and change it.

**11. Why is this still Observstory rather than a generic PM tool?**
It adds four small declared types and no statuses to maintain, boards, priorities or estimates.
Its value is only the comparison with observed repository state, which is what Observstory
already produces. → ADR-027, [system-boundary.md](../collaboration-definition/system-boundary.md)

**12. What should be built next?**
First run it with one real hackathon team, and check whether cues are acted on and whether marked
notes are written at all. Then, in order: an optional LLM extractor behind the same interface (it
still only proposes); a check-in review page once there is a write path (GitHub App, ADR-031);
and consent-first local transcription only if typing notes turns out to be the bottleneck.
→ [ROADMAP.md](../../ROADMAP.md)
