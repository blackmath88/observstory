# Collaboration state: problem space

> Phase: DISCOVER (issue #7). Desk research plus proxy scenarios; **no user interviews**. Every
> finding says whether it rests on external evidence or on reasoning.

## The question

> **What coordination state gets lost between conversation, planning, and repository activity?**

Observstory already makes *repository* state legible: work in flight, overlap, waiting and stale
work. The issue's hypothesis is that it gets more valuable if it can reconcile **declared intent**
(what the team said it would do) with **observed reality** (what the repository shows).

## What gets lost

In fast, intense projects (hackathons, small AI-assisted teams), coordination happens by voice:
a morning stand-up, a 23:00 "let's freeze the architecture", "Patrick, can you own the evals?".
That state has three failure modes:

| Failure | What happens | Who notices, and when |
|---|---|---|
| **Evaporation** | The decision or commitment is never written down, and survives only in memory | Nobody, until two people remember it differently |
| **Drift** | It was written down (chat, doc, board), then the repository moved on | Whoever next reads the old note, if anyone |
| **Silent breach** | A declared constraint ("freeze at 20:00", "submission at 12:00") is crossed | Usually at the demo or in the post-mortem |

Existing tools address evaporation reasonably well (meeting notes, trackers). **Drift and silent
breach are where declared state and repository state have to be compared**, and nothing does
that comparison for teams that don't keep a tracker current.

## Discovery finding: the unit is a *time-bound declaration*, not a task

The most valuable declared objects in a 48-hour project aren't tasks. Tasks are cheap, plentiful
and quickly out of date. They are:

- **gates**: fixed times that change what's allowed (feature freeze, submission, judging);
- **commitments**: a short, named promise ("evals for the memory API, Sofia, by 09:00");
- **decisions**: a choice that constrains an area of the code ("store stays SQLite until the demo").

Each of these can be compared with repository evidence cheaply and deterministically, provided
a human has declared the link (an area, a path or a PR). That comparison is what Observstory is
built for.

## Findings (with evidence strength)

| # | Finding | Evidence |
|---|---|---|
| D1 | Teams with tracker integration already get PR ↔ task status sync | External: Linear moves issues In Progress → Done as linked PRs move ([Linear docs](https://linear.app/docs/github-integration)) |
| D2 | Automatic action-item extraction from meetings is unreliable | External, vendor-reported: action-item hallucination above 35% with default prompts; compounded STT and diarisation errors ([Circleback](https://circleback.ai/blog/how-ai-meeting-notes-work), [Lovex](https://lovex.dev/blog/ai-notetakers-action-items)) |
| D3 | Recording has legal weight | External: 11+ US states require all-party consent; under GDPR consent is a weak basis at work ([Circleback](https://circleback.ai/blog/recording-consent-for-ai-meeting-notes), [summarizemeeting](https://summarizemeeting.com/en/faq/meeting-recording-consent)) |
| D4 | Hackathons are organised around a few hard checkpoints | External: skeleton by hour 6, freeze by hour 30, no-extension submission ([DEV 36-hour timeline](https://dev.to/pranjulrathour/a-36-hour-hackathon-timeline-hour-by-hour-2l82), [MLH guide](https://guide.mlh.io/general-information/hackathon-timeline)) |
| D5 | In fast projects, declared state lives in chat and memory, not trackers | Reasoning plus scenarios; not measured |
| D6 | The comparison "declared constraint vs. repository activity" isn't offered by the tools surveyed | Competitive landscape; absence of evidence, not proof |

## Assumptions

- A1. Teams will spend about 2 minutes after a check-in confirming 3–8 items, if the items come pre-drafted.
- A2. Teams are willing to name the area or PR a commitment relates to, at least for the important ones.
- A3. A declaration file in the repository is acceptable (it's visible and reviewable, but public if the repo is).

## Rejected framings

- **"AI meeting assistant"**: crowded, legally loaded, and the output is unreliable (D2, D3).
- **"Lightweight Jira for hackathons"**: duplicates trackers (D1) and adds exactly the PM upkeep Observstory avoids.
- **"Automatic ownership detection"**: infers who owns what from activity, which is the surveillance anti-goal (ADR-004).
