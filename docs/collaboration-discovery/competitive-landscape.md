# Competitive landscape: collaboration state

| Surface | Captures well | Loses |
|---|---|---|
| **Linear / Jira / GitHub Projects** | tasks, owners, status; Linear syncs status from linked PRs ([docs](https://linear.app/docs/github-integration)) | anything not typed into a card; time-scoped *rules* (freezes); decisions; fast teams that don't keep a board |
| **Notion / docs** | decisions, plans, meeting notes | the link to code; staleness is invisible |
| **Slack / Teams** | the actual conversation | structure; everything scrolls away |
| **AI note-takers** (Granola, Circleback, Otter, Fathom…) | transcripts, summaries, drafted action items | reliability of extracted items (D2); consent burden (D3); items go to email or tracker, never compared with code |
| **GitHub issues / discussions** | decisions and tasks close to the code | the same staleness as trackers; no gates |
| **Hackathon platforms** (Devpost, MLH tooling) | submission deadlines, judging schedules | nothing about the team's own internal gates or commitments |
| **Standup / check-in bots** | periodic self-reports | self-reports without repository evidence; they risk feeling like surveillance |
| **Decision logs / ADRs** | durable decisions | only for decisions someone bothers to write down; no time or gate semantics |

## Synthesis

1. **Evaporation is solved; reconciliation isn't.** Note-takers and trackers stop decisions from being lost. None of them compares a declared, time-scoped constraint with what the repository did afterwards.
2. **Trackers already solve PR ↔ task status sync**, so Observstory shouldn't rebuild it (R5 rejected).
3. **AI extraction is a drafting aid, not a source of truth.** Every serious product keeps a human review step, and the error rates justify it.
4. **Observstory's opening is narrow:** a *small set of declared gates and commitments*, stored where the code lives, compared deterministically with observed repository state, and shown next to the Project Map.
