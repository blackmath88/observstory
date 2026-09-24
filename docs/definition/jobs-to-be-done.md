# Jobs to be done

## Primary JTBD

> **When** I (or my agent) am about to start or continue a change in a shared repository,
> **I want** to see what other unmerged work already touches the same part of the project,
> **so that** we can coordinate while it's still cheap, instead of discovering the collision in review.

## Secondary JTBDs

1. **When** I come back to a project after hours or days away, **I want** to see what changed and what is now in flight, **so that** I can re-orient without reading every PR.
2. **When** I maintain a repository with many open PRs and branches, **I want** open loops (stale work, branches with no PR, PRs waiting on other PRs) surfaced together, **so that** nothing rots silently.
3. **When** I lead a small team, **I want** a view of which areas are moving and where coordination is needed that nobody has to maintain, **so that** I don't need a status meeting or a hand-kept board.
4. **When** a coding agent plans a task, **I want** it to query project state with evidence, **so that** it avoids duplicating or colliding with work it can't see from its worktree.
5. **When** I join mid-project, **I want** to see the project's areas and where activity is concentrated, **so that** I can pick a place to start that doesn't collide with others.

## Explicitly not a job we serve

> When I manage people, I want to compare their output.

This is a real demand (S4) and serving it is the path to surveillance. Observstory declines it.
