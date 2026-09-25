# UI integration

```text
┌ header: repo · status ─────────────────────────────────────────────────────────────┐
│ MISSION  Kickoff ○──── Skeleton │──── ○ Sat check-in ── Freeze core │ ─ NOW ─ Freeze web,src │ ── Submission │
│          ◆C1 ◆C2 ◇C4 …        next: Freeze web/, src/ in 7 h · 2 proposed items await confirmation │
├ lanes (Project Map, unchanged) ──────────────────────────┬ Needs attention ────────┤
│ …                                                        │ ● overlap …             │
│                                                          │ DECLARED VS OBSERVED    │
│                                                          │ ◇ Freeze src/core/: …   │
└──────────────────────────────────────────────────────────┴─────────────────────────┘
```

- **The rail only appears when `.observstory/coordination.json` exists.** Zero-config maps are unchanged.
- **Declared things are drawn in ink on the rail and never inside lane cards**, keeping declared and observed visually separate (principle 1).
- **Orange keeps its single meaning:** something needs a conversation, here a cue.
- **Clicking a gate, commitment or cue opens the inspector** with the declared side (text, session, confirmer, time) above the observed side (work items, commits).
- **Proposed items never appear on the rail.** Only a count is shown, with the command that confirms them.
