# Scenarios (interviews by proxy)

> Phase: DISCOVER. These are **synthetic** scenarios built from the failure catalogue and
> practitioner reports, not transcripts of real interviews. Treat them as hypotheses to test
> with real teams.

---

## S1: Five-person hackathon team (36 h)

**Context.** Five people, each using a coding agent in their own worktree. There's a whiteboard
plan from hour 0. By hour 6 there are 9 branches.

- **Needs to know:** Is anyone else building the thing I'm about to build? Which areas are hot?
  Is anything sitting unmerged that I'm depending on?
- **GitHub already tells them:** the branch list and the PR list, each on its own.
- **Still hard to see:** that `feat/chat-ui` and `sofia/conversation` both rewrite
  `src/conversation/`; that 3 branches have no PR at all.
- **Observstory could show:** a radar with `src/conversation` lit by 2 in-flight work items and
  a link to the evidence; an "orphaned branches" open-loop list.
- **Overreach:** ranking team members by commits ("Sofia: 84 commits, Ben: 3") at a hackathon.

## S2: Two developers plus coding agents

**Context.** Two senior developers, each running 2–3 agents in parallel on a production service.

- **Needs to know:** before starting an agent task on `billing/`, what's in flight there?
- **GitHub already tells them:** open PRs, if they go and look.
- **Still hard to see:** agent branches pushed but not yet opened as PRs; commit bursts that
  make the activity feed unreadable.
- **Observstory could show:** an agent-readable `work_near(path)` answer: in-flight items,
  their paths, age and URL. Commit bursts are folded into one change stream.
- **Overreach:** inferring which developer "uses AI more".

## S3: Maintainer receiving parallel PRs

**Context.** An OSS maintainer; issue #214 attracts 3 PRs from different contributors within a week.

- **Needs to know:** which PRs address the same area; which are stale; which wait on another PR.
- **GitHub already tells them:** linked PRs on the issue, but only if contributors linked them.
- **Still hard to see:** unlinked PRs touching the same files; PR B stacked on PR A's branch.
- **Observstory could show:** an overlap signal grouping the 3 PRs with their shared paths;
  "waiting on #N" relations; a stale list.
- **Overreach:** labelling contributors as "low quality", or auto-closing PRs.

## S4: Product lead checking project state

**Context.** A non-coding lead wants to know "where are we?" without running a standup.

- **Needs to know:** which areas are moving, what's stuck, where people need to talk.
- **GitHub already tells them:** Pulse counts; a board that was last updated 4 days ago.
- **Still hard to see:** the gap between the board and the repository; the reason things are stuck.
- **Observstory could show:** lanes with in-flight counts, open loops, and coordination
  prompts ("2 changes overlap in Engine"), each backed by evidence.
- **Overreach:** individual activity leaderboards; "velocity per person"; any number the lead
  might use in a performance review.

## S5: Contributor joining midway

**Context.** A new team member on day 10 of a 3-week sprint.

- **Needs to know:** the project's shape, where it's active, where it's safe to start, and what was decided.
- **GitHub already tells them:** the README, commit history, closed PRs, all as separate lists.
- **Still hard to see:** the trajectory (which areas were hot when); the decisions made.
- **Observstory could show:** a timeline of snapshots (area heat over time), an index of
  declared decisions, and "quiet areas" with no work in flight.
- **Overreach:** a profile page per person.

## S6 (added): a coding agent before it acts

**Context.** An autonomous agent is about to implement "add retry to webhook sender".

- **Needs to know:** does in-flight work already touch `src/webhooks/`? Is there an open issue
  or PR with the same intent? What changed since its last run?
- **GitHub already tells it:** raw API or MCP access. The agent has to reconstruct relations
  itself, one call at a time, on every run.
- **Still hard to see:** the precomputed relations.
- **Observstory could show:** one structured answer with evidence URLs (see
  `prototypes/agent-surface/`).
- **Overreach:** the agent reporting teammates' activity back to a manager.

---

## Cross-scenario synthesis

| Need | S1 | S2 | S3 | S4 | S5 | S6 |
|---|---|---|---|---|---|---|
| In-flight overlap by area | ● | ● | ● | ● | | ● |
| Open loops (stale, orphaned, waiting) | ● | | ● | ● | | ● |
| Area heat / topology | ● | | | ● | ● | ● |
| History / trajectory | | | | ● | ● | |
| Changes since last check | | ● | | | | ● |
| Per-person metrics | ✗ | ✗ | ✗ | ✗ (asked for, harmful) | ✗ | ✗ |

The two needs in almost every column are **in-flight overlap by area** and **open loops**.
