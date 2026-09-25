# Problem space

> Phase: DISCOVER · Status: complete (desk research + proxy scenarios, no live user interviews)

## The question

Not "what can we chart from GitHub?" but:

> **What collaboration state is still invisible while shared software work is happening?**

## Framing

Software collaboration used to leak intermediate state for free. Pairing, standups, small
pushes, half-finished branches and chat threads meant teammates could see that others were
working in their area before it mattered. AI-assisted development removes much of that leakage:

- One person with a coding agent can produce a large, coherent change in a single sitting.
- The reasoning ("why did we pick X?") stays inside a private LLM conversation.
- The first visible artifact is often a finished PR. By then two people may have built the same
  subsystem twice or chosen incompatible designs.

We call this **the legibility gap**: work runs in parallel faster than the team's shared picture
of it updates.

## Who feels it

| Actor | Symptom |
|---|---|
| Hackathon team (3–6 people, 24–48 h) | Two people build the same feature; integration happens in the last 3 hours |
| Small product team | "I didn't know you were touching auth" found in code review, not before |
| Developer running several agents | Agents working in separate worktrees collide on shared hotspot files (routes, configs, registries) |
| OSS maintainer | Several parallel PRs for the same issue; stale PRs that nobody owns |
| Project lead | Board says one thing, repository says another; the board is updated by hand, the repo is not |
| Mid-project joiner | Cannot reconstruct "how we got here" or where it is safe to start |

## What we think the problem is (and isn't)

It **is**:
- *Late discovery of overlap.* Collisions show up at merge time instead of at start time.
- *Invisible in-flight work.* Branches and draft PRs exist, but nobody sees them as one picture.
- *Unowned open loops.* Stale branches, PRs with no reviewer, work waiting on other work.
- *Lost trajectory.* Nobody can reconstruct how the project got to its current shape.

It **is not**:
- A lack of task tracking. Linear, Jira and GitHub Projects cover that well.
- A lack of individual productivity metrics. These are harmful; see [risks.md](risks.md).
- A lack of AI summaries. A summary with no evidence behind it adds to the legibility problem.

## Key discovery finding about the current MVP

The v0 collector builds its view from `GET /repos/{o}/{r}/commits`, which lists commits on the
**default branch only**. So v0 overlap detection only sees work *after it has merged*, which is
exactly when coordination is too late to help.

The evidence that matters for coordination is **in-flight**: open PR file lists, and branches
that have diverged from the default branch. This doesn't make the architecture wrong
(collector → typed state → projections still holds), but it does change which evidence the
collector must gather. See [observable-signals.md](observable-signals.md) and ADR-003 in
`DECISIONS.md`.

## Assumptions recorded

- A1. Teams in scope push work-in-progress to GitHub (branches or draft PRs) at least a few times a day. If people only push finished work, Observstory can't see anything earlier than GitHub already shows.
- A2. Shared path prefixes (directories) are a usable proxy for "the same subsystem" in most repos. Monorepos with generated files weaken this.
- A3. Teams will accept a tool that names **changes and areas**, and names people only as the authors of evidence, never as a subject of scoring.
- A4. A static, periodically regenerated artifact is useful even without real-time updates. This has not been tested with users.

## Rejected framings

- **"Dashboard for GitHub activity"** is a crowded space (Pulse, Insights, LinearB, Swarmia) and doesn't address the legibility gap.
- **"MCP server for repos"** is a delivery channel, not a problem. GitHub's own MCP server already exposes raw data.
- **"AI project manager"** puts inference in place of evidence and leans towards judging people.

## What remains uncertain

- Whether WIP branches are pushed often enough in real AI-assisted teams (A1). This is the biggest risk to the thesis.
- Whether directory-level overlap has good enough precision. Hunk- or symbol-level analysis may be needed later.
