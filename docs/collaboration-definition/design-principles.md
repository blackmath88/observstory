# Design principles: collaboration state (checkable)

| Principle (from issue #7) | Check |
|---|---|
| 1. Declared intent isn't observed reality | Declared items are drawn in a different visual register from observed work: the rail above the map, in ink, never in lane cards. Every cue has a `declared` and an `observed` part. Test: `test_cue_has_both_sides` |
| 2. Transcript extraction is proposed state | The extractor only writes `proposed`. Reconciliation ignores proposed items. Test: `test_proposed_items_are_ignored` |
| 3. Observe work, don't score people | Cue subjects are gates and commitments; owners appear only as the declared name on the commitment. No per-person aggregates. The validator rejects numeric per-person fields |
| 4. Avoid PM duplication | No status field to maintain; commitment state comes from the repository |
| 5. Reconcile, don't replace | Links can be tracker URLs; Observstory never reads or writes trackers |
| 6. Evidence first | Cues link the declaration (session, confirmer, time) and the observed work items or commits |
| 7. Designed for intense projects | The rail is built for 24–72 h horizons, and "next gate" is the most prominent element |
