#!/usr/bin/env python3
"""Collaboration-state fixtures (issue #7): a SYNTHETIC 36-hour hackathon.

`northstar/voice-notes` and its team (Alice, Ben, Sofia, Dana) are invented. Check-in notes go
through the real extractor (propose) and a named confirmation (confirm); the repository timeline
is observation bundles, as in the Demo Lab. Declarations and observations are then reconciled by
the real derive().

  python3 fixtures/collab_lab.py   -> fixtures/collab-lab/{coordination,<moment>}.json
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

from demo_lab import AGENT, Repo, hours, iso  # noqa: E402
from observstory import coordination as co  # noqa: E402

OUT = HERE / "collab-lab"
START = dt.datetime(2026, 10, 2, 18, 0, tzinfo=dt.timezone.utc)   # Friday 18:00, hackathon kickoff
CONFIG = {
    "title": "Voice notes hackathon (synthetic demo)",
    "lanes": [
        {"id": "intent", "label": "Intent", "description": "Pitch and decisions", "paths": ["README", "docs/"]},
        {"id": "core", "label": "Core", "description": "Audio, transcription, core API", "paths": ["src/"]},
        {"id": "interface", "label": "Interface", "description": "Recorder UI", "paths": ["web/"]},
        {"id": "verify", "label": "Verify", "description": "Evaluation", "paths": ["evals/", "tests/"]},
    ],
}

KICKOFF_NOTES = """Kickoff, Friday 18:30. Everyone present; not recorded.
- CHECKPOINT Skeleton demo at 00:00
- FREEZE src/core/ at Sat 12:00
- FREEZE web/, src/ at Sat 22:00
- SUBMISSION at Sun 06:00
- @Alice: audio capture pipeline (by Sat 10:00) [src/audio/]
- @Ben: transcription adapter (by Sat 12:00) [src/transcribe/]
- @Sofia: recorder UI (by Sat 14:00) [web/recorder/]
- @Dana: evaluation set for transcription accuracy (by Sat 16:00) [evals/]
- DECISION: everything runs locally, no cloud speech-to-text [src/transcribe/]
- ? do we need speaker labels for the demo
Pizza at 20:00."""

MORNING_NOTES = """Saturday 09:00 check-in.
- @Ben: route transcription through the core API (by 11:30) [#12]
- DECISION: core API is frozen at 12:00; only fixes after [src/core/]
- ? is the demo laptop's microphone good enough"""

EVENING_NOTES = """Saturday 19:00 check-in (draft, not yet confirmed).
- @Sofia: record the demo video (by Sun 04:00) [docs/demo/]
- DECISION: drop speaker labels for the demo"""


def at(hours_after_start: float) -> dt.datetime:
    return START + dt.timedelta(hours=hours_after_start)


def declarations() -> dict:
    """The coordination file as it would be after the team's check-ins, built with the real extractor."""
    data = co.empty()
    s1 = co.propose(data, KICKOFF_NOTES, "Kickoff", iso(at(0.5)), kind="kickoff")
    co.confirm(data, s1, by="Alice", at=iso(at(0.8)))
    s2 = co.propose(data, MORNING_NOTES, "Saturday morning check-in", iso(at(15)))
    co.confirm(data, s2, by="Ben", at=iso(at(15.2)))
    co.propose(data, EVENING_NOTES, "Saturday evening check-in", iso(at(25)))  # proposed, never confirmed
    return data


def moments() -> dict[str, dict]:
    r, out = Repo("northstar/voice-notes"), {}
    r.push(at(-20), "Alice", ["README.md"], "Pitch and plan")
    r.push(at(-2), "Ben", ["src/core/api.py"], "Core API skeleton")
    out["kickoff"] = r.observe(at(1), "The kickoff check-in has just been confirmed; no work yet.")

    r.open_pr(10, "Audio capture pipeline", "Alice", ["src/audio/capture.py", "src/audio/buffer.py", "src/core/api.py"],
              hours(at(2), 0, 3, 6, 9), head="alice/audio")
    r.open_pr(11, "Recorder UI", "Sofia", ["web/recorder/Recorder.tsx", "web/recorder/Waveform.tsx"],
              hours(at(7), 0, 4, 8, 13), head="sofia/recorder")
    r.open_pr(12, "Transcription via the core API", "Ben", ["src/transcribe/local.py", "src/core/api.py"],
              hours(at(14), 0, 1), head="ben/transcribe")
    r.close_pr(10, at(15.5), merged=True)
    out["saturday-morning"] = r.observe(at(15.5), "Alice's pipeline landed; Ben and Sofia are in flight; Dana hasn't started.")

    r.push(at(18.7), "Alice", ["src/core/api.py"], "Fix buffer types in core API")      # after the 12:00 core freeze
    r.prs[12]["commits"] += r.commits("Ben", hours(at(19), 0, 0.5), "Transcription: move model loading into core")
    r.prs[12]["updated_at"] = iso(at(19.5))
    out["after-core-freeze"] = r.observe(at(21), "The core API freeze has passed; the core API is still changing.")

    r.open_pr(13, "Transcription accuracy evals", "Dana", ["evals/transcription/run.py", "evals/transcription/clips.json"],
              hours(at(23), 0, 2), head="dana/evals")
    r.close_pr(12, at(24), merged=True)
    r.prs[11]["commits"] += r.commits("Sofia", hours(at(26), 0, 0.2, 0.4, 0.6, 1.5), "Recorder: polish", AGENT)
    r.prs[11]["updated_at"] = iso(at(27.5))
    out["feature-freeze"] = r.observe(at(29), "The feature freeze has passed; the recorder PR is still open and changing.")
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    data = declarations()
    assert co.validate(data) == [], co.validate(data)
    (OUT / "coordination.json").write_text(json.dumps(data, indent=1) + "\n")
    for name, obs in moments().items():
        (OUT / f"{name}.json").write_text(json.dumps(obs, indent=1) + "\n")
        print("wrote", name)
    (OUT / "voice-notes.config.json").write_text(json.dumps(CONFIG, indent=2) + "\n")
