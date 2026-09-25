# Declared vs observed

The most important research area. For each candidate relation: what declared fact, what observed
fact, and how safely they can be compared.

| # | Relation | Declared side | Observed side | Class | Notes |
|---|---|---|---|---|---|
| R1 | Commitment has **no linked work yet** | commitment + due time + declared link target (PR number, branch, or area/path) | no in-flight or recently landed work matching the link | **DETERMINISTICALLY DERIVABLE** | Only when a link target is declared. Without one, nothing can be said |
| R2 | Commitment **has linked active work** | as above | a matching PR/branch in flight | **DETERMINISTICALLY DERIVABLE** | A positive confirmation, not a warning |
| R3 | **Freeze passed, area still changing** | freeze gate: time + scoped areas | work items with commits in those areas *after* the gate time | **DETERMINISTICALLY DERIVABLE** | Needs commit timestamps and paths, which the collector already has. Fixes after a freeze are legitimate, so the cue reads as a question |
| R4 | **Gate passed with linked work still open** | gate + commitments due before it | linked PR still open | **DETERMINISTICALLY DERIVABLE** | Same logic as R3, but at the commitment level |
| R5 | Commitment marked done, PR still open | a "done" declaration | PR open | **DETERMINISTICALLY DERIVABLE** | Needs a "done" status to be maintained, which is PM upkeep. Trackers already do this (D1) |
| R6 | Active work with **no declared commitment** | absence of any declaration | in-flight work | DERIVABLE, but **not useful** | In fast projects most work is undeclared by design. Flagging it would be nagging, and edges towards surveillance |
| R7 | Decision references an area that later changes | decision + declared area | changes in that area after the decision | HEURISTIC | A change isn't necessarily a violation. Only useful as a "for context" link |
| R8 | Owner "is working on" the commitment | declared owner | commits by that person | **NOT SAFELY KNOWABLE / anti-goal** | Authorship isn't ownership, and it drifts into judging people (ADR-004) |
| R9 | The decision was correct or followed | decision text | code semantics | **NOT SAFELY KNOWABLE** | Would need code understanding (ADR-007) |

## Findings

- R1–R4 are **deterministic** once a human has declared a link target, and they use data the collector already gathers.
- **R3 (freeze vs activity) is the most distinctive.** No tracker surveyed compares a *time-scoped declaration about an area* with *repository activity*.
- R5 duplicates trackers; R6 nags; R8 and R9 are off-limits.
- **Links are declared, never inferred.** Guessing which PR "is" a commitment from titles is exactly the false-attribution risk.
