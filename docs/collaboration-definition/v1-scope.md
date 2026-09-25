# v1 scope: collaboration state

**v1 in one line:** check-in notes → proposed items (deterministic extractor) → confirmed by a
named person → `.observstory/coordination.json` → reconciled against the repository → a mission
rail, commitment states and "declared vs observed" cues on the Project Map.

## MUST
- `schema/coordination-v1.json` with Session, Gate, Commitment and Decision; `status` and `source` on every declaration
- `observstory checkin propose NOTES --session … --at …` (deterministic extractor; writes proposed items)
- `observstory checkin confirm SESSION --by NAME [--only IDs | --drop IDs]` (promotes proposed → declared)
- The Action reads the coordination file if it exists (zero-config: none means no rail)
- Reconciliation rules C-linked, C-unlinked, G-freeze and G-open in `snapshot.coordination`
- A mission rail on the Project Map: NOW, gates, check-ins, commitment due times; the next gate emphasised
- Cues in the attention column; inspector views for gates and commitments
- A synthetic hackathon demo state in the Demo Lab; tests; ADRs; docs

## SHOULD
- An extractor adapter interface, so an LLM extractor (e.g. a locally run open model) can plug in and produce only `proposed` items
- Agents: `observstory query coordination` (gates, commitments, cues)

## NOT YET
- Audio recording and transcription (consent UX, local speech-to-text)
- A browser-based check-in review UI that writes to the repository (it needs auth, or a GitHub App)
- Tracker sync (Linear or GitHub issue links are allowed as `url` links but not read)

## NEVER
- Per-person commitment rates or scorecards; inferred owners; inferred links
- Task boards, statuses to maintain, priorities, estimates, sprints
- Extracted items shown as decisions without confirmation
- Storing audio or full transcripts in the repository
