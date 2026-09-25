# Concept comparison and Checkpoint 3

Three directions, all fed by the real engine on the synthetic 36-hour hackathon
(`fixtures/collab_lab.py`):

| Direction | Prototype |
|---|---|
| 1. Check-in capture | [`prototypes/collaboration/checkin/`](../../prototypes/collaboration/checkin/index.html): notes → proposed items with their source line → keep, drop or edit → confirm with a name → the exact CLI command. Plus a mock record control with a consent prompt |
| 2. Mission timeline | [`prototypes/collaboration/mission-timeline/`](../../prototypes/collaboration/mission-timeline/index.html): a rail with NOW, gates (next one emphasised), check-ins and commitment due times coloured by observed state, at four moments |
| 3. Declared vs observed | [`prototypes/collaboration/declared-vs-observed/`](../../prototypes/collaboration/declared-vs-observed/index.html): one card per cue, declared on the left and observed on the right, with the relation in the middle |
| 4. Operating surface | not prototyped (see below) |

## Evaluation (judgements with reasons, not scores)

| | 1 Check-in | 2 Timeline | 3 Declared vs observed |
|---|---|---|---|
| Useful in < 10 s | No, it's a task you do, not a view | **Yes**: "Next: feature freeze in 7 h" plus orange marks | Yes, once there are cues; empty most of the time |
| Maintenance | Two minutes per check-in (the core bet, A1) | none beyond declarations | none |
| Duplication with PM tools | Partial: note-takers draft items too | **Low**: no tool surveyed shows freezes against code | **None found** |
| Evidence quality | Source line for every proposal | Observed state per commitment | Both sides spelled out |
| False-inference risk | Contained, since everything is proposed | Low | Medium for freeze cues on PR-level paths (labelled `medium`) |
| Hackathon usefulness | High at kickoff and check-ins | **High all the time** | High at freezes |
| Agent usefulness | Low | Medium (next gate, frozen areas) | **High**: "is this path frozen?" |
| Complexity | A static page can't write to the repository: it needs auth or a GitHub App | Small; fits the scene and renderer | Small; fits the attention list and inspector |
| Privacy | Recording is the risky part, and it's deferred | Neutral | Neutral; names work, not people |

## Findings from running the prototypes (fed back into the engine)
- **F1:** a scoped freeze flagged commitments outside its areas. Fixed with scope matching.
- **F2:** cue text named a person ("direct:alice"). Cues now name the change ("a direct push").
- **F3:** early moments saw later check-ins. Fixed with `as_of`.
- **F4:** at Saturday 15:00, three cues concerned one PR. Open-work cues already covered by the same gate's freeze cue are now dropped.
- Timeline labels for commitments due close together overlap. The delivered rail stacks them.

## Checkpoint 3: selected direction

**Integrate 2 and 3 into the Project Map, and deliver 1 as the CLI flow.**

- **The mission rail becomes a band above the lanes**, shown only when the repository declares something. It holds NOW, gates, check-ins and commitment due times.
- **Cues join the existing "Needs attention" column** under a *declared vs observed* heading. The inspector shows the two-sided evidence from Direction 3.
- **Check-in is `observstory checkin propose` / `confirm`.** The review page stays a prototype until there's a safe write path (NOT YET, ADR-031).
- **Direction 4 (a separate operating surface) is rejected.** One page with a band is simpler than a new navigation layer, and the map stays the hero.

**The tradeoff:** v1 check-in capture is a terminal step, not a friendly page. We accept that
because the value we're testing is the *reconciliation*, and a browser write path would need
authentication we don't have.
