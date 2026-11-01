# NUC window — Observatory UI and memory

31 October 2026 · ChatGPT (assistant) · execution handoff, not runtime evidence.

Read the [complete dated execution contract](https://github.com/blackmath88/baselhack26-open-presence/blob/34b096716e0df49f2de30abc961263edb3ecc242/docs/build/NUC-WINDOW-2026-10-31.md) before work. It contains the user's scope, local timer arming requirements, packet queue, supervision/cutoff and cross-repository ownership. The preparation branch is docs/nuc-build-window-2026-10-31; it need not merge to be used as a handoff.

Window: 2026-10-31 20:10–23:00 Europe/Zurich; checkpoint 22:45. ChatGPT on NUC arms the actual local runtime; this document arms nothing. No new paid API spend, merge or deployment.

## UI packet O (explicit user priority)

Continue PR #24 / feat/observatory-visual-workspace, planning head 84c3c0a4e1d870f0aa56e47db9ee59fcfd1ee844, stacked on feat/frontend-tanstack-start @ af5b2d725301f46ee1796b3d215fd90694fb8c12. Re-fetch exact bases. Open Presence PR #12 has merged and pins this producer; coordinate a separate consumer pin update after producer checks, without touching Commons or PDF worker ownership.

Write frontend/** and directly necessary workspace projection/schema/tests only. Continue the cool-clean real workspace: workstreams, research/concepts/planning/implementation relationships, truthful timeline, board and shared accessible detail drawer. Improve the running interface rather than writing another specification. Preserve evidence links and unknown states; do not invent dates, owners, progress or human approval. Inspect frontend/docs/visual-workspace/REVIEW.md and use real Open Presence data. Required checks plus a focused phone/desktop/keyboard pass for changed interactions; avoid repeating an entire test matrix without reason.

## Memory packet M (separate slot and ownership)

Inspect PR #20 @ c63091613c206dc50dac06a85cc608a88596e0e3 and replay-fix PR #23 @ c23c35ac8447d2f84bec89e5a9b9e4ee68efb61d. Knowledge Lab #1 pins the older producer. Reconcile the fix and exact host pin on a coherent integration branch without merging PRs. Preserve separate visual frontend and memory branch worktrees. System Map #17 is not tonight's target.

## Return

Exact input base, head/PR, changed behavior, focused checks and any self-review limits. Report running/possibly-live workers and observed settlement. Put the combined window result in the Open Presence results handoff named by the canonical contract. The window's two-worker ceiling is global across repos; no recursive delegation.
