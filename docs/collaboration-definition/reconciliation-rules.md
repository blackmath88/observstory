# Reconciliation rules (v1)

Each rule compares one **declared** fact with **observed** repository evidence. Every cue names
both sides. None of them mentions a person as its subject.

| Rule | Question answered | Declared side | Observed side | Logic | False-positive risk | v1 |
|---|---|---|---|---|---|---|
| **C-linked** (R2) | Is there work behind this commitment? | commitment with links | work items matching a link: `pr` = number, `branch` = head name, `path` = any changed path under it (in flight, or landed after the commitment) | any match → state `in_progress` (open work) or `landed` (all matching work merged or landed) | Low: the links are declared | ✅ |
| **C-unlinked** (R1) | Has this commitment started? | commitment with links and a `due` | no matching work | state `not_started`. It becomes a **cue** only once `due` has passed, or once 50% of the time from confirmation to due has elapsed | Low–medium: the work may live elsewhere (local only) | ✅ |
| **G-freeze** (R3) | Did a frozen area change after the freeze? | freeze gate: `at` + `areas` | work items with commits **after** `at` that touch an area path. Direct pushes are checked per commit (exact); PRs and branches by their overall paths (approximate) | cue per gate, listing the work items; `high` for exact per-commit evidence, `medium` for PR-level paths | Medium: fixes after a freeze are legitimate. Wording: "changed after the freeze" | ✅ |
| **G-open** (R4) | Did a gate pass with committed work still open? | gate + commitments with `due` ≤ gate | the commitment's linked work still in flight | cue per commitment | Low | ✅ |
| Decision-area (R7) | Did a decided area change later? | decision with areas | changes after the decision | shown only in the decision's inspector, never as a cue | Medium | shown, not cued |
| R5, R6, R8, R9 | — | — | — | rejected (see [declared-vs-observed](../collaboration-discovery/declared-vs-observed.md)) | — | ❌ |

Cues appear in the Project Map's attention column under **Declared vs observed**, in neutral
wording. For example:

- *Freeze 23:00 on `web/`: 1 change afterwards (#50).*
- *"Eval harness for memory" (due 14:00): no linked work yet.*
