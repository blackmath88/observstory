# Competitive landscape: what collaboration state is still invisible?

> Phase: DISCOVER. The question for each tool is not "what features?" but "what remains invisible?".
> Sources are listed at the bottom. Claims about third-party tools come from their public
> positioning, not from hands-on evaluation.

| Surface | What it makes visible well | What stays invisible |
|---|---|---|
| **GitHub activity feed / notifications** | Individual events (push, comment, review) | Relationships *between* events; that two branches touch the same area; anything not addressed to you |
| **GitHub Projects** | Intent, as people type it into cards | Anything nobody typed; drift between the board and the code; work with no card |
| **PR list / dashboards** | Each PR's state, reviewers, CI | Cross-PR relations: shared paths, stacking/waiting, duplicate intent |
| **GitHub Pulse / Insights** | Aggregate counts over time (commits, PRs merged, contributors) | Current in-flight state; overlap; anything branch-level. Also frames activity as per-person counts |
| **Linear / Jira** | Planned work, status and assignment, managed by people | Actual code movement; overlap not declared in the tracker; maintaining it costs the team effort |
| **Graphite / stacked-PR tools** | Explicit dependencies inside *one author's* stack | Implicit dependencies *between* authors; overlap outside the stack |
| **GitHub Actions** | Whether a build or check passed | Anything about coordination; runs are per event and have no memory |
| **Engineering intelligence (LinearB, Swarmia, DX, Waydev)** | Team flow metrics (cycle time, DORA), aggregated after the fact | Real-time "who is about to collide". Many drift into per-person metrics, which is the surveillance risk |
| **Early-conflict tools (GitKraken Conflict Prevention, GitLive)** | File or line overlap between *your* branch and the target, inside an IDE | Project-wide picture; shared artifact for non-IDE users; agent-readable state |
| **Agent orchestration (GitHub Agent HQ / mission control, worktree managers, Claude Code agent view)** | Sessions of *one* orchestrator: logs, their PRs | Work done by *other people's* agents and orchestrators; the project as a whole. Worktree isolation hides collisions until merge rather than preventing them |
| **"Clash predictor" patterns (blogs, scripts)** | Changed-path overlap between agent branches | Packaging, shared state for humans, evidence UI, history |

## Synthesis

1. **Every tool shows either intent (boards) or events (feeds), and none reconciles them from
   the repository alone.** Boards need someone to keep them up to date. Feeds have no model of
   the project.
2. **Cross-actor relations are the gap.** Stacked-PR tools see dependencies inside one person's
   stack. Conflict tools see your own branch against main. Orchestrators see their own agents.
   **Nothing shows the relations between several authors' in-flight work at project level**,
   let alone in a form both humans and agents can read.
3. **Engineering-intelligence products show both the value and the danger.** They prove people
   want derived signals, and they show how quickly derived signals become per-person scorecards.
4. **Worktree isolation is now the default for parallel agents, and it moves collisions later.**
   Isolation prevents tool interference, but it pushes the moment of discovering overlap to
   merge time. That makes a shared overlap view more valuable, not less.

## What existing tools already solve (do not rebuild)

- Task definition and assignment (Projects, Linear, Jira)
- Per-PR review and CI state (GitHub)
- Line-level conflict resolution (IDEs, GitKraken)
- Agent session management (Agent HQ, orchestrators)
- DORA-style team flow metrics (engineering-intelligence products)

## What remains unsolved (Observstory's space)

- A **project-level, zero-maintenance picture of in-flight work across all authors and agents**
- **Overlap, staleness and waiting relations** between pieces of in-flight work, each with the evidence behind it
- **One shared state** that both a human UI and a coding agent can read *before acting*
- **History**: how the project's areas of activity changed over time

## Sources

- GitHub Docs: [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- GitHub Blog: [Introducing Agent HQ](https://github.blog/news-insights/company-news/welcome-home-agents/) · [How to orchestrate agents using mission control](https://github.blog/ai-and-ml/github-copilot/how-to-orchestrate-agents-using-mission-control/)
- GitKraken: [Merge conflict / conflict prevention](https://gitkraken.com/features/merge-conflict-resolution-tool)
- GitLive: [Early merge conflict detection across all branches](https://dev.to/gitlive/early-merge-conflict-detection-across-all-branches-in-vs-code-43mc)
- Grass: [Parallel worktrees + clash-style conflict prediction](https://codeongrass.com/blog/parallel-worktrees-conflict-prediction/)
- Augment Code: [How to run a multi-agent coding workspace](https://www.augmentcode.com/guides/how-to-run-a-multi-agent-coding-workspace)
- Swarmia: [Comparing DORA, SPACE and DX Core 4](https://www.swarmia.com/blog/comparing-developer-productivity-frameworks/)
