# Product thesis

> **Problem.** In AI-assisted teams, work runs in parallel faster than the shared picture of it
> updates, so people and agents find out they overlap, or that work has stalled, only at merge
> time.
>
> **Claim.** Observstory turns repository activity into a typed, evidence-backed model of
> *in-flight work*: which work items are open, which project areas they touch, and where they
> overlap, stall or wait on each other. Humans and coding agents read the same model.
>
> **Non-goal.** Observstory does not measure, rank or profile people, and it does not decide
> whose approach is right. It points to places that need a conversation.
>
> **Proof requirement.** We know it works when, on a repository with no configuration, two
> independently started pieces of work touching the same area show up as an overlap, with
> links to the PRs, branches and files, **before either is merged**, and a coding agent can
> retrieve the same fact with one query.

## Why GitHub doesn't already solve this

GitHub shows **objects** (a PR, a branch, a commit) and **feeds** (events in time order). It
doesn't compute **relations between different authors' unmerged work**: shared areas, waiting
chains, work nobody has touched in days. Those relations are the coordination state. Today
someone has to reconstruct them by reading every PR, and in practice nobody does until the merge
conflict arrives.

## What changes from the v0 claim

v0: "turns repository activity into a typed shared project-state model".
v1 keeps this and narrows it: **the project state that matters for coordination is in-flight
work**, and the typed model is organised around *work items* and *areas*, not contributors.
