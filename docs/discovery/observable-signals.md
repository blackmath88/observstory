# Observable signals

> Phase: DISCOVER. Every candidate signal is classified. **Inference is never promoted to fact.**

## Classification key

| Class | Meaning | How it appears in the snapshot |
|---|---|---|
| **OBSERVED** | Returned directly by the GitHub API | Plain fields, with a `url` wherever GitHub provides one |
| **DERIVED** | Deterministic function of observed data (same input gives same output, no thresholds) | Computed fields; the formula is documented |
| **HEURISTIC** | Inferred using thresholds or proxies; can be wrong | `signals[]` entries with `basis: "heuristic"`, `confidence`, `evidence[]` |
| **DECLARED** | Needs explicit human input (config, labels, text markers) | Carries `source: "config"` / `"label"` / `"text"` |
| **UNKNOWABLE** | Not safely knowable from metadata | Not emitted |

## Signal table

| Candidate | Class | Source / method | Notes and caveats |
|---|---|---|---|
| Commit (sha, message, timestamp) | OBSERVED | `GET /commits`, `/commits/{sha}` | Author date can be forged; committer date changes on rebase |
| Changed paths per commit | OBSERVED | `/commits/{sha}` `.files` | Capped at 300 files per commit by the API |
| Changed paths per open PR | OBSERVED | `GET /pulls/{n}/files` | **Key in-flight evidence.** Capped at 3000 files |
| PR state, draft, base/head, reviewers | OBSERVED | `GET /pulls` | `requested_reviewers` is cleared once they review |
| Branch list, head sha | OBSERVED | `GET /branches` | No "created at"; there is no push timestamp without extra calls |
| Branch divergence from default | OBSERVED | `GET /compare/{base}...{head}` | Returns ahead/behind counts and changed files; one call per branch |
| Issue state, labels, assignees | OBSERVED | `GET /issues` | Includes PRs, which must be filtered out |
| CI status | OBSERVED | `GET /commits/{sha}/check-runs` | One call per sha; deferred to v1.x |
| Author login | OBSERVED | `.author.login` | `null` when the email isn't linked; fall back to the git name, marked `unlinked` |
| Actor kind (human / bot) | OBSERVED + DERIVED | `.type == "Bot"` or login ends with `[bot]` | Agents acting under a human's token look like the human. **Agent-authored work is only DECLARED** (trailers such as `Co-Authored-By: Claude`, labels) |
| Timestamp of last activity on work | DERIVED | max(PR `updated_at`, head commit date) | `updated_at` also moves on comments and label changes |
| Area / lane of a path | DERIVED (DECLARED when configured) | Prefix match against lane config, or the first N path segments | Zero-config falls back to top-level directory |
| **Shared-area overlap** | HEURISTIC | ≥2 distinct in-flight work items touching the same area | False positives: lockfiles, generated files, broad directories |
| **Shared-file overlap** | DERIVED | ≥2 work items change the same path | Deterministic, but a shared file is not necessarily a conflict |
| Likely textual conflict | HEURISTIC (weak) | Same file plus overlapping hunks | Needs patch parsing; deferred |
| **Stale work** | HEURISTIC | Open work, no activity for more than N days | The threshold is a guess; "parked" can be intentional |
| **Orphaned branch** | DERIVED | Branch ahead of default, no open PR | Deterministic once the branch list is known |
| **Waiting on other work** | DERIVED / DECLARED | base ≠ default (stacked), or `depends on #n` / `blocked by #n` in the PR body | Only explicit or declared; implicit dependencies are UNKNOWABLE |
| **Burst activity** | HEURISTIC | ≥K commits by one actor within M minutes | Describes a change stream, not a person; used to damp other signals |
| Task intent | DECLARED | PR/issue title and body, verbatim | Never summarised in v1 |
| Architectural decision | DECLARED | DECISIONS.md, `adr/` files, `decision` label | Observstory can *index* these, not *detect* them |
| Handoff readiness | DECLARED + DERIVED | Non-draft PR, reviewers requested, CI green | "Ready" is the author's claim; Observstory reports the declared state |
| Code ownership | DECLARED | CODEOWNERS | Recent authorship is **not** ownership and must never be shown as such |
| File co-editing (same file, same time) | DERIVED | Overlap restricted to one window | |
| Active work | DERIVED | Open PR or branch with activity within the window | |
| Semantic conflict between designs | UNKNOWABLE | n/a | Would need code understanding; never asserted |
| Person's productivity, focus, effort | UNKNOWABLE and anti-goal | n/a | Never emitted, even when computable |

## Rules adopted

1. OBSERVED fields keep GitHub URLs so every row can be traced back.
2. HEURISTIC outputs always carry `basis`, `confidence`, and at least one `evidence` item.
3. Thresholds live in config with documented defaults and are echoed into the snapshot, so any
   consumer can see which rule produced a signal.
4. People appear as `actors` on evidence, **never as the subject of a signal**. Signals are about
   areas and work items.

## API budget (GITHUB_TOKEN = 1,000 req/h/repo)

| Call | Count per run (typical small repo) |
|---|---|
| repo, commits, pulls, issues, branches | 5 |
| commit detail | ≤ `max_commits` (default 60) |
| PR files | ≤ open PRs (cap 30) |
| branch compare | ≤ unmerged branches without a PR (cap 20) |
| **Total** | ~50–115 |

At an hourly schedule plus event triggers, this stays well inside the limit. v0's `*/10` cron
(6 runs an hour × ~65 calls ≈ 390 calls/h) was also inside the limit, but it scales badly as
`max_commits` grows. The collector must read `X-RateLimit-Remaining` and degrade (drop commit
detail first) instead of failing.
