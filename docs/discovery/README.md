# Discovery: phase record and Checkpoint 1

| Doc | Purpose |
|---|---|
| [problem-space.md](problem-space.md) | Framing, the legibility gap, the key finding about the MVP |
| [competitive-landscape.md](competitive-landscape.md) | What collaboration state is still invisible in existing tools |
| [ai-collaboration-failures.md](ai-collaboration-failures.md) | 13 failure patterns and how detectable each one is |
| [observable-signals.md](observable-signals.md) | Every signal classified OBSERVED / DERIVED / HEURISTIC / DECLARED / UNKNOWABLE |
| [scenarios.md](scenarios.md) | 6 proxy scenarios (5 required plus the agent itself) |
| [risks.md](risks.md) | 17 risks with mitigations |
| [opportunity-map.json](opportunity-map.json) | Problems ranked by severity × frequency × observability |

## Phase record

**Findings**
1. The strongest problem is **late discovery of overlapping in-flight work** (P1). Four failure patterns share one mechanism and one kind of evidence: shared paths across unmerged work.
2. **Open loops** (stale, orphaned, waiting) come second. They are less severe but frequent and fully deterministic.
3. **The v0 collector only reads the default branch**, so it only sees overlap after merge, which is too late to help. The fix is to read in-flight evidence: open PR files and diverged branches.
4. The v0 UI sorts contributors by commit count, which is a leaderboard. That goes against the surveillance principle.
5. The v0 lane classifier uses substring matching (`"test/" in "latest/x"`), which causes silent misclassification.

**Assumptions:** A1–A4 in [problem-space.md](problem-space.md). The biggest is A1: teams push WIP often enough to be seen.

**Rejected alternatives:** "GitHub analytics dashboard", "MCP-first product", "AI project manager", "per-person activity insights".

**Decision:** Continue. Discovery **supports** the Observstory thesis and **sharpens** it: the product is about in-flight work, not repository history.

**Evidence:** agent-PR conflict studies (secondary summaries), practitioner hotspot reports, the existence of IDE-local conflict tools (which validates path overlap as a signal), GitHub API documentation.

**Uncertain:** whether A1 holds for real teams; precision of path-level overlap; whether a static artifact is checked often enough to matter.

## Checkpoint 1

- **Strongest user problem:** people and agents working in parallel find out they overlap only at merge time.
- **Strongest evidence:** reported ~28% conflict rate on agent PRs, with cross-agent pairs about 2× same-agent. Also, several tools independently use changed-path overlap as the first signal.
- **Surprising finding:** the MVP's own overlap signal is structurally too late (default branch only). Worktree isolation, now the default for parallel agents, *hides* collisions rather than preventing them.
- **What existing tools already solve:** tasks (Projects/Linear), per-PR review and CI, your-branch-vs-main conflicts (IDEs), single-orchestrator agent sessions, team DORA metrics.
- **What remains unsolved:** a zero-maintenance, project-wide, evidence-backed picture of *everyone's* in-flight work and how the pieces relate, readable by both humans and agents.
- **Proposed problem definition:** *In AI-assisted teams, work runs in parallel faster than the shared picture of it updates, so overlaps and open loops are found at merge time. Observstory should show in-flight overlap and open loops from repository evidence alone, early enough to prompt a conversation.*
