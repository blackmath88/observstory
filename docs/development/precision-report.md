# Precision report: overlap on real repositories

> Issue #2 follow-up. Observstory run against six active open-source repositories, 2026-09-25.
> Raw data, scripts and labels: [`evals/precision/`](../../evals/precision/).

## Summary

| | Overlap signals (6 repos) | Useful (labelled) |
|---|---|---|
| v1 as merged | **141** | not labelled in full; most pairs trace to stale or area-only work (below) |
| after the evidence-driven changes | **27** | **16 / 27 (59%)** |

Five changes to the overlap rule, each justified by the data below (ADR-018 to ADR-022):

1. **Base-aware** (issue #2): default-branch changes already in a work item's merge base are baseline, not parallel work.
2. **Stale work doesn't take part**: pairs involving work idle for more than `stale_hours` were **81%** of all pairs.
3. **A shared file is required** (default; can be turned off): area-only pairs were useful in **4 of 39** labelled cases.
4. **Bot-only work doesn't take part**, and `CHANGELOG*`, `.changeset/` and `*.api.md` are ignored by default (6 of the 52 sampled non-useful pairs came from these files).
5. **Stacks explain shared ground transitively**: two-level stacks produced 9 of the 20 non-useful signals before this fix.

No new signal types and no new infrastructure. The study scripts live under `evals/` and aren't
part of the Action.

---

## 1. Method

### Repositories
Chosen for sustained multi-author activity and a spread of layouts:

| Repo | Layout | Open PRs (merge refs) |
|---|---|---|
| astral-sh/uv | Rust workspace, `crates/*` | 584 |
| vitejs/vite | TS monorepo, `packages/*` + `playground/` | 330 |
| fastapi/fastapi | Python, docs-heavy (translations) | 178 |
| tldraw/tldraw | TS monorepo, `packages/*` + `apps/*` | 146 |
| withastro/astro | TS monorepo with changesets and release bots | 82 |
| pydantic/pydantic | Python package | 75 |

Everything ran on **zero config**: default lanes, ignores, thresholds and window (48 h). That's
the product claim being tested.

### Collection in git-only mode (a limitation of this environment)
This session could read public repos over git but not through the GitHub REST API.
[`git_study.py`](../../evals/precision/git_study.py) therefore builds the same observation bundles
from a local clone that has trees but no file contents, and runs them through the **unmodified**
`derive()`. How each input was substituted, and how the substitution was checked:

| Needed | Git stand-in | Check |
|---|---|---|
| Open PRs | `refs/pull/N/merge` exists | Merge refs linger on some closed PRs: 3 of the 4 *oldest* sampled were closed. The study inspects only the 30 PRs with the newest head commits, and **all 4 suspicious participants checked in the final signals were open** |
| "30 most recently updated" | newest head-commit date | Ignores comment activity; affects `stale`, not overlap |
| Merge base | `git merge-base` | Same as compare's `merge_base_commit` |
| PR files and commits | `git diff --name-only` / `git log` from the merge base | Same as the three-dot compare |
| PR base branch | inferred from ancestry (another open PR's head is inside this PR's history) | 4 of 6 checked correct, 1 partly right (right that it's stacked, wrong parent), 1 wrong (astro#18119 targets `next`) |
| Titles, authors | head-commit subject, git author name | Bots found by name pattern. astro's "Houston (Bot)" isn't matched in git mode |
| Recently merged PRs | not collected | Their squash commits appear as `direct:<author>` (landed on the default branch) |

API-mode tooling ([`run.py`](../../evals/precision/run.py)) is included for a rerun with a token.

### Line-level measurement
For every parallel pair, the unified diffs of each shared file were compared: each side's diff
against its own merge base, or the specific landed commits for default-branch pushes. A pair
**changes the same lines** if any hunk's old-side range comes within 3 lines of the other side's.
This is an objective proxy for "will conflict or needs coordination", not ground truth.

### Human labels
One annotator (the implementing agent). The rubric: **useful** means someone working on one side
should hear about the other *now*, because both change the same code region or the same feature
surface. Unrelated edits that merely share a directory, a registry list or a generated file are
**not useful**. Every label has a one-line rationale in
[`labels.json`](../../evals/precision/data/labels.json) and
[`final-labels.json`](../../evals/precision/data/final-labels.json). A second annotator would
strengthen this; see threats to validity.

---

## 2. What the v1 model surfaced (base-aware, before other changes)

137 signals made up of **5,903 parallel pairs**. Each pair was given its first matching noise
category:

| Category | Pairs | Share |
|---|---|---|
| a participant idle for more than 72 h (stale) | 4,808 | **81.4%** |
| a bot participant | 263 | 4.5% |
| a sweeping participant (≥ 50 files) | 301 | 5.1% |
| stacked PRs (git ancestry) | 32 | 0.5% |
| only generated files shared | 7 | 0.1% |
| clean: same lines | 23 | 0.4% |
| clean: same file, different lines | 61 | 1.0% |
| clean: area only | 408 | 6.9% |

Share of pairs changing the same lines, by what they involve (a pair can appear in several rows):

| Pairs involving | n | same lines |
|---|---|---|
| all pairs | 5,903 | 13.0% |
| stale work | 4,808 | 12.4% |
| a sweeping change | 2,246 | **23.6%** |
| a bot author | 1,417 | 8.4% |
| a landed default-branch change | 1,043 | 7.4% |

**Takeaways:**
- Stale work is where the volume comes from. It's already reported by the `stale` signal.
- Sweeping changes are *not* noise: they have the highest line-overlap rate, so they stay.
- The 4 signals removed by base-awareness alone (141 → 137) involved only baseline changes or sequential pushes to the default branch. On this
  repo's own history, base-awareness removes all **9** overlaps from the v1 self-observation; see
  [self-observation.md](../demo/self-observation.md).

## 3. After excluding stale work

59 signals, 1,095 pairs:

| Pair type | n | same lines | same file | area only |
|---|---|---|---|---|
| both unmerged | 618 | 23.5% | 15.2% | 61.3% |
| both unmerged, bot involved | 87 | **1.1%** | 17.2% | 81.6% |
| landed × unmerged | 214 | 9.8% | 16.4% | 73.8% |
| landed × unmerged, bot involved | 176 | 4.5% | 26.1% | 69.3% |

### Labelled sample (fixed seed, bot and stacked pairs excluded)

| Stratum | Pool | Sample | Useful |
|---|---|---|---|
| A: unmerged × unmerged, same lines | 61 | 20 | **15 (75%)** |
| B: unmerged × unmerged, same file, different lines | 94 | 20 | **9 (45%)** |
| C: unmerged × unmerged, area only | 379 | 25 | **4 (16%)** |
| D: landed × unmerged, shares a file | | 6 | **5** |
| D: landed × unmerged, area only | | 14 | **0** |

Why pairs weren't useful:

| Cause | Examples |
|---|---|
| Unrelated work in the same broad area | most of C and D-area-only |
| Registry and list files | `lib.rs` module lists, `env_vars.rs`, preview-flag registries, event-name registries |
| Large shared test files | independent test cases in the same file |
| Generated files | `uv.schema.json`, `api-report.api.md`, a generated preview-feature reference |
| Release automation | `CHANGELOG.md`, `.changeset/*`, version lines in `package.json` |

## 4. Changes made, and the evidence for each

| Change | Evidence | Effect (6 repos) |
|---|---|---|
| ADR-018 base-aware overlap (issue #2) | fixtures b1–b7; self-observation 9 → 0 | 141 → 137 |
| ADR-021 stale work doesn't take part | 81.4% of pairs; already in the `stale` signal | 137 → 59 |
| ADR-019 shared file required (default) | area-only pairs useful in 4/39; shared-file pairs in 29/46 | together with the next two rows: 59 → 47 (730 area-only pairs, 67% of the remaining pairs, no longer count) |
| ADR-019 bot-only work doesn't take part | unmerged pairs with a bot: 1.1% same lines | (in 59 → 47) |
| ADR-020 ignore `CHANGELOG*`, `.changeset/`, `*.api.md` | 6 of the 52 non-useful sampled pairs (3 of the 5 non-useful same-line pairs) | (in 59 → 47) |
| *git-mode correction, not a model change:* infer stacked PR bases from ancestry | the API would supply real base branches; 4 of 6 inferences verified | 47 → 36 |
| ADR-022 transitive stack explanation | 9 of the 20 non-useful signals came from two-level stacks (uv#21962 → #21961 → #21963; #21952 → #21944 → #21942) | 36 → 27 |

Ablation on the final model ([`ablation.json`](../../evals/precision/data/ablation.json)):

| Variant | Signals |
|---|---|
| final | **27** |
| final, but area-only pairs allowed | 45 |
| final, but stale work allowed | 97 |
| final, but both allowed | 112 |

## 5. Final result

| Repo | Signals | Useful | Not useful: why |
|---|---|---|---|
| astral-sh/uv | 14 | 9 | generated schema, generated preview reference, 3 registry files |
| tldraw/tldraw | 6 | 4 | comment/format churn; spec wording by the same people |
| vitejs/vite | 3 | 3 | none |
| withastro/astro | 4 | 0 | release PRs and version bumps (the release bot isn't recognised in git mode) |
| fastapi/fastapi | 0 | | every candidate pair involved stale work |
| pydantic/pydantic | 0 | | only area-only candidates |
| **Total** | **27** | **16 (59%)** | |

Useful signals found, for example:
- vite: three PRs changing how the bundled dev runtime is served (#23559, #23562, #23568).
- tldraw: paste handling changed in #10873 and #9396, and a broad simplify refactor (#10071) overlapping five focused fixes.
- uv: hash-precedence work in #21314 and #21930 on the same `hash.rs`.
- uv: a PR editing a security-review workflow that had just changed on `main`.

## 6. What this costs (recall)

- **Area-only relations** are no longer signals. About 10% of them were useful (4 of 39). With
  roughly 540 non-bot area-only pairs, that's on the order of 50 useful relations given up to
  remove about 490 unhelpful ones. They're still visible as area activity on the radar and in
  `work_near`. Small repos where directories really are subsystems can restore them with
  `signals.overlap_require_shared_file: false`.
- **Stale work's overlaps** are no longer reported as overlaps. 12% of those pairs changed the
  same lines, which is a real latent conflict. They surface through `stale` instead.
- **Bot-only work** that collides with humans (e.g. dependency bumps in a manifest a human is
  editing) is no longer flagged. Bots usually rebase automatically.

## 7. What was *not* changed, and why

- **Sweeping changes stay.** They have the highest line-overlap rate (23.6%).
- **Landed changes after divergence stay**, as issue #2 requires, but now only when they share a
  file: 5 of 6 such pairs were useful.
- **Confidence is still coarse.** Almost every remaining signal is `high`. The data shows a real
  split, same lines (75%) versus same file on different lines (45%), that only hunk-level data
  can express. That needs patch ranges in the collector: v1.x roadmap, now backed by evidence.
- **Registry and generated files** (e.g. `uv.schema.json`) are repo-specific. They belong in the
  repo's `ignore` config, not in defaults.
- **Large-area clutter.** Signals like `crates/uv` and `packages/vite` are correct but hold 16–47
  pairs. The dashboard already groups them. Ranking pairs inside a signal is a presentation
  question for later.

## 8. Threats to validity

- **Single annotator**, who is also the implementer. Labels and rationales are published so they
  can be re-labelled.
- **Git-mode stand-ins.** Open-PR detection, stack inference (4 of 6 correct) and bot detection
  by name are approximations of what the API provides. An API-mode rerun (`run.py`) is the
  natural next check.
- **One snapshot per repo, taken at one moment.** Precision will vary over time and between repos.
- **Large OSS repos, not hackathon teams.** Area-only overlap may be more useful in small repos
  where directories *are* subsystems. That's why it's a config switch and not deleted.
- **Line overlap is a proxy.** Changes on nearby lines can merge cleanly, and conflicting
  semantics can live far apart.

## 9. Reproduce

```bash
python3 evals/precision/git_study.py collect astral-sh/uv vitejs/vite pydantic/pydantic withastro/astro tldraw/tldraw fastapi/fastapi
python3 evals/precision/git_study.py stacks     # infer stacked PRs from ancestry
python3 evals/precision/git_study.py measure    # derive + line-level measurement (about 10 min, fetches file contents on demand)
python3 evals/precision/analyze.py              # pair-level breakdown
python3 evals/precision/sample.py               # fixed-seed labelling sample
```

The stored observations reproduce the exact numbers above with no network access, except for
`measure`, which reads file contents from the local clones.
