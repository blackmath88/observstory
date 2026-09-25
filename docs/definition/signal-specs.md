# v1 signal specifications

v1 ships **four signals**, plus one derived work-item state (review state) that answers the
handoff question. Every signal has the same shape:

```json
{
  "id": "overlap:src/conversation",
  "type": "overlap | stale | waiting | burst",
  "basis": "derived | heuristic | declared",
  "confidence": "high | medium | low",
  "subject": {"kind": "area | work_item", "id": "src/conversation"},
  "summary": "2 in-flight work items touch src/conversation",
  "work_items": ["pr:14", "branch:sofia/convo"],
  "actors": ["alice", "sofia"],
  "evidence": [{"kind": "file", "ref": "src/conversation/store.py", "work_items": ["pr:14","branch:sofia/convo"], "url": "…"}],
  "rule": {"name": "overlap.area", "params": {"min_work_items": 2}}
}
```

**Rule for every signal:** the subject is an **area** or a **work item**, never a person.
`actors` appears only as evidence of who authored the work.

Thresholds are set in `observstory.config.json → signals` and echoed into
`snapshot.config.signals`.

---

## S-1 Overlap

| | |
|---|---|
| **Question answered** | "Is other unmerged work changing the same files as mine, in parallel?" |
| **Input evidence** | Changed paths of each *active* work item: open PRs, unproposed branches, and default-branch commits grouped per author (`direct`). Each PR/branch's **merge base** (compare, or first-commit parent as a labelled fallback) and the parent links of default-branch commits |
| **Logic** | Per area, form **pairs** (ADR-018). Unmerged × unmerged is parallel unless one waits on the other, **transitively** (ADR-022). Unmerged × landed counts only default-branch commits **not** in the item's merge base. Landed × landed is never parallel (sequential). A pair counts only if both sides change a **common file** (default, ADR-019). **Stale** work (ADR-021) and **bot-only** work (ADR-019) don't take part. Emit when ≥ `overlap_min_work_items` distinct items are in counted pairs. **Confidence:** `high` with a shared file (`medium` for area-only when enabled); one level lower if everyone is the same single author, or if every pair relies on an unknown or first-parent merge base |
| **Evidence** | `file` (shared files and the pairs changing them), `base` (why a landed change counts: merge-base SHA, source, later commits), `work_item`; `rule.params` lists `parallel_pairs`, `baseline_pairs`, `explained_by_waiting`, `excluded_stale`, `excluded_bot_only`, `area_only_pairs_skipped` |
| **Precision (6 OSS repos)** | 16 of 27 final signals useful (59%). Same-line pairs 75% useful, same-file pairs 45%, area-only 10%. See [precision-report.md](../development/precision-report.md) |
| **False-positive risk** | Registry and list files, large shared test files, repo-specific generated files (configure `ignore`), release automation |
| **UI** | Radar: the area's mark gets an accent ring. The signal list groups overlaps with the same work-item set and opens to files, base evidence and pairs |
| **API** | `query overlaps [--path P]`, `query work-near P` |
| **Test** | `tests/test_base_aware.py`, `tests/test_signals.py::OverlapExperiments` |

## S-2 Stale

| | |
|---|---|
| **Question answered** | "Which in-flight work has stopped moving?" |
| **Input evidence** | `last_activity_at` of the work item: latest commit date on the PR or branch, or PR `updated_at`, whichever is later |
| **Logic** | Open PR or unmerged branch with `now − last_activity_at > stale_hours` (default 72). A branch with no PR gets the detail `"no pull request"`, which covers the *orphaned* case. Basis `heuristic`, confidence `medium` (`low` for drafts, which are often parked on purpose) |
| **False-positive risk** | Medium. Parked work, holidays, long reviews. The word is "stale", not "abandoned" |
| **UI** | An "Open loops" list, greyed, with age ("idle 5d"). No person-coloured markers |
| **API** | `query open-loops` |
| **Test** | `test_stale_branch_without_pr`, `test_recent_work_not_stale` |

## S-3 Waiting

| | |
|---|---|
| **Question answered** | "Which work can't land until other work lands?" |
| **Input evidence** | (a) PR `base.ref` equals the head branch of another open PR (**derived**, stacked). (b) PR body contains `depends on #N`, `blocked by #N`, `requires #N` or `after #N` where #N is open (**declared**) |
| **Logic** | Emit `waiting` with subject = the waiting PR and `work_items = [waiting, blocker]`. Confidence `high` for both: the relation is explicit, not guessed |
| **False-positive risk** | Low. Text markers in quoted or old text are possible |
| **UI** | Open loops list: "pr:15 waits on pr:14" with both links |
| **API** | `query open-loops`, and `waiting_on` on the work item |
| **Test** | `test_pr_waiting_on_stacked_base`, `test_pr_waiting_declared_in_body` |

## S-4 Burst

| | |
|---|---|
| **Question answered** | "Is this change stream machine-paced? Should I read it as one unit rather than 30 commits?" |
| **Input evidence** | Commit timestamps within one work item |
| **Logic** | ≥ `burst_min_commits` (default 8) commits in any sliding window of `burst_window_minutes` (default 30). Basis `heuristic`, confidence `medium`; `high` if commits carry a declared agent trailer (`Co-Authored-By: <agent>` or `Generated-By`). **Subject is the work item.** Used by the UI to fold the commit stream, not to flag anyone |
| **False-positive risk** | Rebases or cherry-picks that rewrite dates; a human committing quickly. Harmless, because the only consequence is folding |
| **UI** | The work item gets a small `burst` glyph; commits are collapsed as "23 commits in 40 min" |
| **API** | Returned on the work item (`burst: {...}`) and in `signals` |
| **Test** | `test_agent_rapid_commit_burst`, `test_human_paced_commits_no_burst` |

## Derived state: review_state (handoff)

Not a signal. It is a plain derived field on each PR work item:
`draft` → `no_reviewer` (open, not draft, no reviewer requested) → `review_requested`.
Answers "what is ready for handoff?" using the author's own declaration. Never inferred from
code.

## Rejected for v1

| Candidate | Why not yet |
|---|---|
| Divergence (conflicting designs) | Not knowable from metadata; would need an LLM (R3) |
| Ownership drift | Authorship ≠ ownership; surveillance-adjacent |
| Line or hunk-level conflict prediction | Needs patch parsing and more API calls; v1.x refinement of S-1 |
| Duplicate intent from titles | Precision unknown; needs its own experiment |
| CI status | One extra call per head sha; useful but not a coordination signal for v1 |
