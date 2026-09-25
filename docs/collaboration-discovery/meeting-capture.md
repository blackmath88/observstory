# Meeting capture: record → transcript → proposals → confirmation → state

## The pipeline, and what each stage produces

| Stage | Output | Status | Can it become state automatically? |
|---|---|---|---|
| 1. Recording | audio | **observed** (raw) | No: it's a capture artefact, not project state. It needs consent |
| 2. Transcript | text with timestamps and (weak) speakers | **observed**, with error | No: speech-to-text errors of 3–35% and speaker errors of 11–13% ([Circleback](https://circleback.ai/blog/how-ai-meeting-notes-work)) |
| 3. Extraction | candidate decisions, commitments, questions, gates | **proposed** (derived) | **Never.** Hallucinated action items are common (D2) |
| 4. Review | edited items | still **proposed** | No |
| 5. Confirmation | a named person confirms each item | **declared** | Yes. Only this becomes project state |

The rule the rest of the design follows:

> **Only human confirmation promotes anything to declared state.** Transcript text is kept as the
> item's *provenance*, not as its truth.

## Consent and recording UX

- Recording is **opt-in per session**. The session record states that it was recorded and who confirmed consent. There is no background capture.
- **The transcript is not stored in the repository by default.** Only confirmed items are, plus an optional short excerpt as provenance. Raw audio never goes in the repo.
- **Local transcription is preferred** (on-device). A cloud adapter must be an explicit choice.
- **Speakers aren't attributed automatically to people.** A commitment's owner is whoever the confirmer names.

## v1 decision (carried into Define)

Live audio and transcription are **out of v1**. v1 accepts **transcript text or notes typed after
the meeting**, turns them into *proposed* items with a pluggable extractor, and requires
confirmation. The default extractor is deterministic (line markers such as `DECISION:`,
`@name will …`, `FREEZE … at 20:00`). An LLM extractor (e.g. a locally run open model) can be
added behind the same interface, and it may only ever produce `proposed` items.

Why: an audio pipeline would dominate the work, carry consent and retention risk, and add no
evidence about the central question, which is whether *reconciling* declared and observed state
is useful.
