# Scenarios (synthetic, proxy)

These scenarios are written from the research, not observed. The format for each: what
happened, what's invisible, what state matters, what to observe, what to declare, and what
would be overreach.

## C1: Five-person hackathon, 36 hours
- **What happened:** the kickoff sets a skeleton at hour 6, an architecture freeze at hour 20, a feature freeze at hour 30 and submission at hour 36. Six people, several coding agents.
- **What's invisible:** at hour 22 nobody knows that two branches are still reshaping `src/core/` after the architecture freeze.
- **What matters:** the gates, with their times and scopes, and each area's activity after them.
- **Observe:** commits and paths per work item, with timestamps.
- **Declare:** the gates (time, and optionally the areas they apply to).
- **Overreach:** naming "who broke the freeze", or ranking teams by commits after the freeze.

## C2: Morning alignment meeting
- **What happened:** a 15-minute check-in at 09:00. "Sofia takes the eval harness, done by 14:00", "we keep SQLite", "Ben: is the search API stable?"
- **What's invisible:** by 16:00 nobody remembers whether the eval harness exists.
- **What matters:** one commitment (owner, due time, link target `evals/`), one decision, one open question.
- **Observe:** whether any work in `evals/` is in flight or has landed since 09:00.
- **Declare:** the three items, confirmed after the meeting.
- **Overreach:** transcribing without consent; auto-assigning owners from who spoke.

## C3: Late-night scope freeze
- **What happened:** at 23:00: "feature freeze, only fixes from now". At 01:40 a new PR adds a settings screen in `web/`.
- **What's invisible:** that the new PR postdates the freeze.
- **What matters:** the freeze time and its scope (`web/`, `src/`).
- **Observe:** the PR's commits after 23:00 in `web/`.
- **Declare:** the freeze.
- **Overreach:** blocking the merge, or labelling it a violation. The cue is "changed after the freeze: intentional?"

## C4: A team working mostly through coding agents
- **What happened:** three humans run eight agent sessions. Commitments are made to people, but the work is done by agents under those people's accounts.
- **What's invisible:** which agent PR fulfils which commitment.
- **What matters:** commitments linked to a PR number or branch once the agent opens it.
- **Observe:** PR state, burst (already a signal).
- **Declare:** the link (the PR description can carry `Fulfils: C-3`, or the owner adds it when confirming).
- **Overreach:** guessing the link from title similarity (a false attribution).

## C5: Project lead joining midway
- **What happened:** the lead arrives at hour 18 and asks "where are we against the plan?"
- **What's invisible:** the plan itself: which commitments are open or unstarted, and what the next gate is.
- **What matters:** the mission rail (NOW, next gate) plus commitments with their observed state.
- **Observe:** linked work per commitment.
- **Declare:** nothing new; it reads existing declarations.
- **Overreach:** a per-person progress view.

## C6: A decision made verbally, then activity diverges
- **What happened:** "we won't touch the auth flow before the demo." Two hours later a PR changes `src/auth/`.
- **What's invisible:** the connection between the decision and the PR.
- **What matters:** the decision, with its declared area.
- **Observe:** work in `src/auth/` after the decision time.
- **Declare:** the decision and the area.
- **Overreach:** calling it a breach. Decisions change for good reasons, so the cue is "for context".
