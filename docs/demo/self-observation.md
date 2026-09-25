# Self-observation

Observstory was run against **its own live repository** while this v1 work was in progress,
reading the real GitHub API.

- Command: `OBSERVSTORY_REPOSITORY=blackmath88/observstory python3 scripts/observstory.py build`
- Config: [`observstory.config.json`](../../observstory.config.json) (5 lanes: Model, Engine, Evidence, Integration, Contract)
- Output: [`self/index.html`](self/index.html), [`self/data/snapshot.json`](self/data/snapshot.json), [`self/data/observations.json`](self/data/observations.json)
- Cost: 16 API calls, no degradation

![self-observation](img/self.png)

## What it saw

| Snapshot fact | Is it true? |
|---|---|
| 1 work item in flight: `branch:claude/blissful-brahmagupta-xtddua`, state **unproposed** (no PR) | Yes. The v1 work was pushed to a branch with no PR open |
| `direct:blackmath88`: the maintainer's direct pushes to `main` in the window | Yes. The v0 commits |
| **9 overlaps**, high confidence, between the branch and those pushes: README, ARCHITECTURE, ROADMAP, action.yml, the dogfood workflow, scripts, config, schema | **No. This was a false positive, and this page originally said it was true.** The branch was created from `9cced7c`, *after* every one of those pushes, so they were its baseline, not parallel work. Found in issue #2 and fixed by base-aware overlap (ADR-018). Re-derived with the branch's merge base, the same snapshot has **0 overlaps** |
| `burst` on `direct:blackmath88`: 10 commits within 10 min | Yes. The v0 history landed as a rapid sequence of commits |
| The branch is marked **agent-assisted (declared)** | Yes, from the `Co-Authored-By: Claude` trailers |
| Open loops: none | Correct. Nothing is idle for more than 72 h, and nothing is stacked |

> **Correction (issue #2).** The archived snapshot in `self/` has been re-derived with the current
> model. Commit parents and the branch's merge base were added to `self/data/observations.json`
> afterwards from local git (`git rev-list --parents`, `git merge-base`, which equal what the API's
> compare returns); nothing else in the observations changed. The screenshot above has been
> re-rendered from the corrected snapshot: the branch and the pushes are both active, with no overlap.

## What dogfooding found (and fixed)

1. **A real bug.** The default ignore entry for the output folder (`observstory/`) matched *any*
   directory with that name, so `src/observstory/` (the whole engine) was silently dropped from
   the model. Fixed with gitignore-style anchoring (`/observstory/`). Regression test:
   `test_anchored_ignore_does_not_hide_nested_dirs`.
2. **Radar legibility on real timing.** All real activity was less than an hour old, so a linear
   recency axis stacked every mark at the centre. Changed to a log scale with an inner band,
   labels only on overlap or busy areas, and collision nudging.
3. **Signal fatigue.** One relationship (branch × push stream) produced 9 per-area signals.
   (That relationship later turned out to be baseline, not parallel work; see the correction above.
   The grouping is still useful: in the precision study, crowded areas hold up to 47 pairs.) The
   dashboard now groups overlaps with the same work-item set into one entry. The snapshot keeps
   per-area signals, so agents can still query by path.

## Reproduce

```bash
OBSERVSTORY_REPOSITORY=blackmath88/observstory OBSERVSTORY_OUTPUT=/tmp/obs \
  python3 scripts/observstory.py build        # token optional for public repos (60 req/h)
python3 scripts/observstory.py query work-near README.md --snapshot /tmp/obs/data/snapshot.json
```

In CI, `.github/workflows/observstory.yml` runs the same thing on every push, PR and issue event,
and hourly, after running the test suite.
