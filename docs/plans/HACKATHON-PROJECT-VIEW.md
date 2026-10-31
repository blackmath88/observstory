# Hackathon project view — knowledge, time and remaining work

Status: **user-requested product goal**, 31 October 2026. This is the functional integration brief for Claude's existing redesign, not another visual direction or a claim of implementation.

## The job
When Achim opens the Observatory during the hackathon, he should immediately be able to answer:
- What are we building, and what is the current agreed direction?
- How much time remains until hands-off, and what event/checkpoint comes next?
- What still needs doing, what blocks it, and who has explicitly taken it?
- What actually works, what evidence demonstrates it, and what is still a proposal?
- What changed while I was away, and why?

The entry page at https://blackmath88.github.io/baselhack26-open-presence/ should answer these together. A quiet activity lane should still show the relevant project knowledge, deliverables and pending work. A small link to a separate knowledge page does not fulfill this requirement.

## Existing work to extend
- Visual study: `design/observatory-pixel-studies`, inspected at `f1ee81600701ec8dc840629551147a2bdd7d146b`.
- Read `design/observatory/README.md`, `RECOMMENDATION.md` and the existing rewrite handoff. The current study uses synthetic data and has not replaced the live renderer.
- Project Memory work: PR #20 / `feat/project-memory-mvp`, with Now / History / Graph / Context and an evidence inspector. Reconcile with that work instead of creating another state model.
- Production event-ref fix: main includes PR #21. Preserve stable requested ref + exact resolved commit when integrating older branches.
- First consumer: `blackmath88/baselhack26-open-presence`.
- Source-data integration: https://github.com/blackmath88/baselhack26-open-presence/pull/7
- The redesign branch remains owned by its current Claude session. Do not overwrite, reset or concurrently edit its files without coordinating ownership.

## A useful default overview
The reading order should be:

1. **Project now.** Current concept in a short source-backed excerpt; key declared decisions and the next demonstrable outcome. Expand into research, unresolved questions and historical directions.
2. **Event clock.** Absolute hands-off time and remaining elapsed hours/minutes, timezone, current/next event and the next internal checkpoint. Sunday 1 November 12:00 is hands-off; 13:00 is the start of presentations, not extra hacking time.
3. **Remaining work.** Must-have outcomes with owner (or unassigned), dependencies, proposed/declared due time and evidence links. Show blocked and awaiting-review work without inferring it from inactivity.
4. **Recent changes.** Source-backed changes to the plan, concept, knowledge and implementation, with an understandable “since I last looked” view.
5. **Activity and inspection.** Existing work lanes and signals, full timetable, history/context and evidence inspector remain available beneath or beside the overview.

Keep the current visual workbench and creature direction. This brief changes the functional content, not palette, composition or art.

## Data: one view, distinct evidence
| Input | Responsibility | Can establish |
| --- | --- | --- |
| `data/knowledge.json` / memory projection | Selected concept, research, decisions, questions, history | What the project declares; sources and epistemic status |
| `data/snapshot.json` + `data/scene.json` | Observed GitHub activity and derived signals | Open work, touched areas, overlap and activity freshness |
| `.observstory/coordination.json` | Source-owned commitments, gates, proposals and confirmations | Declared plans/owners; proposed timings stay visibly proposed |
| `.observstory/event.json` → `data/event.json` | User-supplied event programme | Event times and hard planning boundary, with source/precision |
| PR/test/demo evidence | Verified implementation outcomes | Only the behavior those checks actually demonstrate |

Do not merge these into an undifferentiated “truth” or silently change snapshot/v1. LightRAG is optional supporting retrieval; this planning view must work without it, NUC access or provider calls.

## Event data ready for integration
The consumer contains 17 events across 30 Oct–1 Nov, normalized to Europe/Zurich. Friday “after 20:30”, approximate snack/photo times and the uncertain Saturday midnight boundary preserve their qualifiers. Meal intervals are actual programme ranges; do not invent durations for opening/pitches.

The source is the timetable supplied by Achim, not independently verified with organisers. Submission/upload procedure and individual pitch slot are unknown.

The consumer's former Sunday 13:00 feature freeze and 15:00 rehearsal are superseded proposals. Revised proposals: integration checkpoint 10:00, internal freeze 10:30, rehearsal 11:15. No owner is assigned and these internal targets have not been confirmed as team commitments.

## Planning and task semantics
- An event having passed does not mean a task/gate passed.
- “No declared gates” must read **No confirmed checkpoints yet**, never “All declared gates have passed.”
- A merged PR is landed code, not necessarily a working/accepted deliverable.
- “No active PR” is not “Nothing to do”; concepts, unanswered questions, proposed tasks and unfinished deliverables still exist.
- Distinguish proposed, declared, implemented, tested and accepted. Use existing typed states/evidence where available; if explicit task-progress state is missing, show unknown rather than manufacturing a done percentage.
- Keep original IDs (M1–M6, G1–G6, C1–C6 and event IDs), basis and exact source links.
- Surface the 12 pending coordination proposals; do not silently confirm them. Source material and owners can be selected/revised deliberately.
- First version can use existing commitments plus GitHub issues for tasks. Any richer task-status file needs a documented companion contract and explicit edits; do not overload snapshot/v1.
- Static Pages cannot silently write shared state. Link to the real GitHub issue/source edit path or prepare an explicit patch/proposal export. A browser-only draft must be labelled local; a checkbox must not pretend to update the team.
- Time-budget display should distinguish wall-clock time from an explicitly declared work budget. Do not invent effort estimates or convert meal ranges into productive time claims.
- Refresh the current-time countdown in the browser using absolute timestamps. Keep repository data freshness visible. A moving clock does not mean fresh GitHub data.
- In historical replay, separate the selected historical time from the present deadline/countdown.
- Source strings must be escaped, controls keyboard usable, and reduced motion respected.

## First integrated slice and acceptance
Build the functional overview using the already selected design direction and real public consumer artifacts.

1. Add a small adapter/view model joining knowledge, coordination, event schedule and activity with receipt/freshness per input.
2. Show current direction, noon deadline/countdown, next event, pending proposals and remaining must-have outcomes on the default page.
3. Reuse the inspector for sources, status/basis and evidence. Keep activity and the full timetable accessible.
4. Make task updates lead to a real persistent source or an honestly labelled proposal export.
5. Exercise actual data first, then labelled fixtures for missing/incomplete/stale inputs and historical time.

Acceptance examples:
- Quiet GitHub activity still displays the concept, relevant research, unresolved questions and pending work.
- At 11:30 Sunday Zurich the page shows 30 minutes until hands-off and identifies the 13:00 presentation block separately.
- At/after noon it says hands-off has arrived; it does not mark tasks done.
- With no declared checkpoints it says none are confirmed.
- A planned but unassigned task stays proposed/unassigned despite recent commits in its area.
- Missing knowledge or schedule is visibly unavailable; activity remains usable.
- Noon timing, owner/status/basis and completion evidence agree between human view and agent-accessible data.
- Desktop and phone layout, keyboard and data escaping are checked using real consumer data; report untested behavior.

## Scope and delivery
Implement within the existing redesign/integration work, preserving other sessions. Do not start a second visual exploration or dispatch workers merely because this issue exists. No new backend, paid inference, automatic agent orchestration or private endpoint is required.

Publish only through the existing authorized public Pages pipeline after tests. Report the exact producer commit, consumer pin, deployed URL and observed behavior. A design-study link alone is not delivery.

## Selected repository handoff
New findings: the live map is activity-only; the design branch remains a synthetic study; Sunday planning was incompatible with the supplied noon deadline.
Agreed direction: the Observatory entry page is shared project knowledge + time and to-do management for the hackathon, extending Claude's existing redesign.
Proposals: revised internal Sunday checkpoints remain proposed; the overview reading order and implementation slice above are implementation recommendations.
Open: task ownership/confirmation, upload procedure, pitch slot, midnight interpretation and integration of the memory PR with the visual study.
Sources: user-supplied timetable, current Open Presence plan/coordination/artifacts, Observstory design README and PR #20.
Affected: this functional brief; Open Presence event timetable/JSON, plan, coordination, knowledge manifest and publishing workflow. No design/renderer source changed by this handoff.
