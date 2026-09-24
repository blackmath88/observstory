# AI-era collaboration failures

> Phase: DISCOVER. A catalogue of breakdown patterns. For each: how it shows up, whether GitHub
> evidence can detect it, and how early.

**Evidence strength key:**
- **E**: supported by external evidence (sources below)
- **P**: plausible, from practitioner reports and proxy scenarios
- **H**: hypothesis

| # | Pattern | Mechanism | Detectable from GitHub? | Earliest detection point | Strength |
|---|---|---|---|---|---|
| F1 | **Duplicate build**: two people or agents build the same thing | Private agent loops, no shared WIP | Partly: overlapping paths in open PRs or branches; similar titles | First push of the second branch | E |
| F2 | **Monolithic arrival**: a finished 3k-line PR with no intermediate state | Agent generates everything in one sitting | Yes: one large first push, commit burst | When the PR opens (too late to prevent, but visible) | P |
| F3 | **Architectural divergence**: branches encode conflicting interpretations | Decisions made in private chats | Weakly: overlapping *areas*, not the semantics | Same as F1 | P |
| F4 | **Hotspot collision**: routes, config, registries, lockfiles | Every feature touches the shared registry | Yes: path overlap on known hotspot files | First push | E |
| F5 | **Private decisions**: "why X?" lives in an LLM transcript | Nothing written to the repo | Only if written down (DECISIONS.md, PR body) | Never, without explicit input | P |
| F6 | **Subsystem blindness**: nobody knows who is changing which area | No shared picture of work in flight | Yes: in-flight paths per area | Continuous | P |
| F7 | **Unclear ownership** | No CODEOWNERS, rapid churn | Partly: CODEOWNERS file; recent authorship is *not* ownership | n/a | P |
| F8 | **Stale tasks**: open PRs or branches nobody touches | Context switch, abandoned agent run | Yes: last-activity timestamps | Threshold crossing | E-ish (well known in OSS) |
| F9 | **Orphaned work**: branch with no PR, PR with no reviewer | Agent opened a branch, human moved on | Yes: branch without PR; PR with no reviewer requested | Threshold crossing | P |
| F10 | **Hidden dependency**: PR B needs PR A | Stacking, or "after #12 lands" in prose | Partly: base branch ≠ default (explicit); `depends on #n` text (declared) | When the PR opens | P |
| F11 | **Late integration conflict** | Worktree isolation delays discovery | Yes: path overlap between open PRs | First push after both touch the path | E |
| F12 | **Lost trajectory**: "how did we get here?" | No record of past state | Only if snapshots are kept over time | Needs history | H |
| F13 | **Agent churn**: dozens of commits per hour from one run | Agent loops commit continuously | Yes: commit rate and bot/agent markers | Continuous | P |

## Observations

- **F1, F4, F6, F11 share one mechanism, overlapping in-flight changes, and one piece of evidence,
  shared paths across unmerged work.** This is the densest cluster and the strongest candidate
  for the core signal.
- **F8, F9, F10 are "open loops"**: in-flight work that nobody is currently moving forward.
  These are cheap to detect and don't depend on the overlap heuristic.
- **F3 and F5 are not safely knowable from metadata.** Observstory can say "these two changes
  touch the same area" (F1/F3 evidence), but not "these designs conflict". Claiming the latter
  would require an LLM reading code, and would present inference as fact.
- **F12 needs persistence.** The Action MVP has none across runs. Snapshot artifacts or a
  committed history branch are the cheap fix.
- **F13 is not a failure in itself, but it distorts every activity-based signal.** Burst commits
  inflate counts and trigger false overlap. It needs to be handled as a *modifier*.

## Evidence

- AgenticFlict (AIware 2026, arXiv 2604.03551) reports a ~27.7% textual merge-conflict rate over
  142k+ agent PRs in 59k+ repos, with cross-agent pairs conflicting at about twice the rate of
  same-agent pairs. *Figures come from secondary summaries; arxiv.org was not reachable from this
  environment to verify them against the paper.*
- Practitioner guidance on parallel agents consistently names shared hotspot files (routes,
  configs, registries) as the collision point and recommends spec-scoped tasks plus worktree
  isolation ([Augment Code guide](https://www.augmentcode.com/guides/how-to-run-a-multi-agent-coding-workspace)).
- "Clash predictor" posts use changed-path overlap between agent branches as the first-pass
  signal, with hunk or symbol overlap as the refinement
  ([Grass](https://codeongrass.com/blog/parallel-worktrees-conflict-prediction/)). This
  independently supports path overlap as a v1 signal.
