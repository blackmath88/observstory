# Roadmap

## V0 — repo-native proof

- [x] reusable composite GitHub Action
- [x] event-triggered builds
- [x] ten-minute reconciliation workflow pattern
- [x] typed lane configuration
- [x] normalized JSON snapshot
- [x] generated static dashboard
- [x] basic overlap signals from changed paths
- [ ] dogfood Observstory on this repository
- [ ] publish a tagged `v0` action release

## V1 — useful in a live team

- [ ] richer PR/check status
- [ ] branch/worktree view
- [ ] contributor focus view
- [ ] open-loop detection
- [ ] better path ownership and overlap heuristics
- [ ] configurable modules
- [ ] timeline playback
- [ ] snapshot schema tests

## V2 — installable service

Build a GitHub App so setup becomes:

> Install Observstory → select repositories → open control center.

Components:

- webhook receiver
- event queue
- normalized event log
- materialized project state
- scheduled reconciliation
- hosted dashboard
- auth and repository permissions

## V3 — agent interface

Expose the typed project state through MCP.

Candidate resources/tools:

- `project://snapshot`
- `project://lanes`
- `project://contributors`
- `project://open-loops`
- `project.changes_since`
- `project.overlaps`
- `project.handoff`

The MCP layer should not independently crawl GitHub. It should read Observstory state so agents and humans share one source of coordination truth.
