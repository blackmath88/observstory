# Product thesis: collaboration state

> **Problem.** In fast projects, the team's own declarations (a freeze at 23:00, "Sofia owns the
> evals by 14:00") live in conversation. Nobody compares them with what the repository then does,
> so breaches and evaporated commitments show up at the demo.
>
> **Claim.** Observstory keeps a *small, human-confirmed* set of declarations (gates,
> commitments, decisions from check-ins) next to the code. It compares them deterministically
> with observed repository state, and shows the result on a mission rail beside the Project Map.
>
> **Non-goal.** Observstory doesn't manage tasks, record meetings, assign owners, or judge
> whether people keep their word. Declared intent and observed reality stay visibly separate.
>
> **Proof requirement.** A confirmed check-in yields declarations. The Project Map then shows
> NOW, the next gate and each commitment's observed state. At least one reconciliation cue (for
> example "freeze passed; `web/` changed afterwards in #50") appears with evidence from both sides,
> with no inference about people.

## Why GitHub Projects, Linear or Notion aren't enough

They store declared intent well, and Linear even moves a task's status when its PR moves. But
they have no notion of a **time-scoped rule about an area of the code** (freezes, gates), and they
only know what someone typed in. In a 36-hour project, the board is the first thing to go stale.
Observstory doesn't replace them: a commitment's link can simply point at a tracker issue.
