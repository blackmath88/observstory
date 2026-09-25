# Collaboration discovery: phase record and Checkpoint 1

Documents: [problem-space](problem-space.md) · [meeting-capture](meeting-capture.md) ·
[planning-and-milestones](planning-and-milestones.md) · [declared-vs-observed](declared-vs-observed.md) ·
[competitive-landscape](competitive-landscape.md) · [scenarios](scenarios.md) · [risks](risks.md) ·
[opportunity-map.json](opportunity-map.json)

## Phase record

- **Findings:**
  - The unit that matters is a *time-bound declaration* (a gate, commitment or decision), not a task.
  - Deterministic reconciliation is possible for four relations (R1–R4), provided a human declares the link target.
  - A freeze compared with repository activity (R3) is uncovered by any tool surveyed.
  - Extraction from transcripts is unreliable enough that it must stay *proposed*.
- **Assumptions:** A1–A3 in [problem-space.md](problem-space.md). The weakest is A1: will people confirm items after a check-in?
- **Rejected:** "AI meeting assistant"; "lightweight Jira"; inferred ownership; flagging undeclared work (R6); done-status sync (R5).
- **Evidence:** tracker PR-sync documentation; vendor-reported extraction error rates; recording-consent law summaries; hackathon organiser guides. No user interviews.
- **Uncertain:** whether teams will declare link targets (A2); whether R3 cues feel useful or feel like policing.

## Checkpoint 1

- **Strongest problem:** declared, time-scoped constraints (freezes, gates) are crossed silently, and check-in commitments evaporate. Both surface too late.
- **Strongest evidence:** hackathon guides organise the event around a few hard gates, while trackers and note-takers have no notion of an area-scoped rule compared with code.
- **Already solved elsewhere:** capturing tasks, and syncing PR ↔ task status (Linear); drafting meeting notes (AI note-takers); hackathon-level deadlines (platforms).
- **Unsolved:** reconciling *the team's own declarations* with what the repository did afterwards, without upkeep and without judging people.
- **Should Observstory expand?** **Yes, narrowly:** a small declared layer (gates, commitments, decisions from confirmed check-ins) plus deterministic reconciliation against repository state. Not a task manager, and not a meeting recorder.
