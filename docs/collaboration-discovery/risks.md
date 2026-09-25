# Risks: collaboration state

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| K1 | **Surveillance**: per-person commitment scorecards | High | Commitments show *work* state, never a person's rate. No per-person views. The owner appears only as the name on the commitment |
| K2 | **Recording consent** | High | No recording in v1. When added later: opt-in per session, visible recording state, consent confirmation stored, audio never in the repo |
| K3 | **Over-automation**: extracted items treated as truth | High | Extraction output is always `proposed`. Only a confirmation with the confirmer's name promotes it |
| K4 | **Wrong task extraction** | Medium | The deterministic extractor is conservative (explicit markers only). The LLM extractor, if added, is labelled, and its items still need confirmation |
| K5 | **False ownership attribution** | High | Owners are declared by the confirmer, never inferred from speakers or commit authors (R8 anti-goal) |
| K6 | **People trusting inferred decisions** | Medium | Declared and proposed look different. Proposed items never appear on the timeline or map |
| K7 | **PM bloat** | High | Only four types (session, decision, commitment, gate). No statuses to maintain beyond what the repository shows. No sprints, estimates or priorities |
| K8 | **Notification fatigue** | Medium | No notifications in v1. Cues appear in the existing attention column |
| K9 | **Stale planning data** | Medium | Declarations are dated and the timeline shows their age. Gates that have passed recede. Nothing claims to be current beyond what the repository shows |
| K10 | **Duplicated truth** with trackers | Medium | Links can point to a tracker issue URL. Observstory doesn't track task status (R5 rejected) |
| K11 | **Becoming a generic task manager** | High | No task list UI, no assignment workflow, no due-date nagging. The v1 scope has an explicit NEVER list |
| K12 | **Public repositories expose plans** | Low–Medium | The declaration file is visible to repo readers; say so in the docs. Private repos are unaffected |
