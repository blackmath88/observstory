# Declared collaboration state: how to use it (issue #7)

Optional. Without `.observstory/coordination.json` the Project Map is unchanged.
`observstory …` below means `python3 scripts/observstory.py …` from a checkout (stdlib only).

## The flow

```text
check-in notes (text you already write)
   │  observstory checkin propose notes.md --label "Sat check-in" --at 2026-10-03T09:00:00+02:00
   ▼
PROPOSED items in .observstory/coordination.json   ← never shown on the rail, never reconciled
   │  observstory checkin pending                  (review; edit the notes or the JSON if something is wrong)
   │  observstory checkin confirm S2 --by Ben [--only C5,G4 | --drop D2]
   ▼
DECLARED items (confirmed_by, confirmed_at, source line)
   │  git commit .observstory/coordination.json && git push
   ▼
the Action reconciles them with repository evidence on its next run
   ▼
Project Map: mission rail · commitment states · "Declared vs observed" cues · `observstory query coordination`
```

Nothing is recorded or transcribed. Paste notes from any tool, including an AI note-taker's
summary: the extractor only reads marked lines, and everything it finds stays *proposed* until
a named person confirms it (ADR-029).

## Marker grammar (`markers/v1`)

One item per line; a leading `-`, `*` or `•` is ignored, and so is every line without a marker.

| Line | Becomes | Example |
|---|---|---|
| `FREEZE <paths> at [Day] HH:MM` | gate, kind freeze, scoped to the paths | `- FREEZE src/core/ at Sat 12:00` |
| `GATE`, `SUBMISSION`, `DEMO`, `CHECKPOINT <label> at [Day] HH:MM` | gate | `- SUBMISSION at Sun 06:00` |
| `@Owner: text (by [Day] HH:MM) [links]` | commitment | `- @Dana: evaluation set (by Sat 16:00) [evals/]` |
| `DECISION: text [areas]` | decision | `- DECISION: no cloud speech-to-text [src/transcribe/]` |
| `? text` or `QUESTION: text` | open question (kept on the session, never reconciled) | `- ? do we need speaker labels` |

- **Times** resolve against the session time `--at`: `HH:MM` is the next occurrence, `Sat HH:MM` the
  next Saturday; the session's UTC offset is used.
- **Links** in `[...]`: `#12` → pull request, `branch:name` → branch, `https://…` → URL (kept, never
  fetched), anything else → path. Links are the only way work is attached to a
  commitment; Observstory never guesses one.
- **Owner** is copied as written. It is shown as "(as declared)" and never used to attribute work.

## What reconciliation says

| State / cue | Meaning | Evidence |
|---|---|---|
| `in_progress` / `landed` / `closed` | linked work exists and is open / merged / closed unmerged | the linked PR or branch; for a path, work touching it that was active after the commitment was made |
| `not_started` | a linked path, but no work touches it yet | none, and that is the point |
| `unlinked` / `tracked_elsewhere` | no links / only URLs (e.g. a tracker ticket) | nothing is inferred |
| cue `commitment.unstarted` | not started, and half the time to the due time has passed (or it is due) | the declaration and its links |
| cue `freeze.changed_after` | a freeze time passed and files in its scope changed afterwards | exact commits when known, else work item activity (medium confidence) |
| cue `gate.passed_with_open_work` | a gate passed while declared, in-scope commitments are still open | the commitment and its open work |

Cues are listed separately from repository signals ("Declared vs observed") and describe work
and declarations, never people (ADR-030).

## For agents

```bash
observstory query coordination --snapshot observstory/data/snapshot.json
```

Returns the next gate, gates, commitments with states, decisions and cues. Proposed items are
counted (`proposed_pending`) but not returned.

## Demo

`demo/index.html#after-core-freeze`: the "Declared vs observed" act of the Demo Lab, a synthetic
36-hour hackathon at four moments (`fixtures/collab_lab.py`). Each moment only sees check-ins that
had happened by then.

![Declared vs observed in the Demo Lab](../demo/img/demo-lab-declared.png)
