#!/usr/bin/env python3
"""Semantic UI Playground fixtures: observation bundles generated from a SEMANTIC spec.

A spec says what the project *means* (its shape, how much work is in flight, how that work relates,
what the team declared). It never says where anything goes. Each spec becomes a synthetic
observation bundle (plus, for declared states, a coordination file built by the real extractor and
a named confirmation) and then goes through the real derive -> compile_scene -> render_map.

Everything is SYNTHETIC: `northstar/*` repositories and their people are invented.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import collab_lab  # noqa: E402
import demo_lab  # noqa: E402
from demo_lab import AGENT, Repo, hours, iso  # noqa: E402
from observstory import coordination as co  # noqa: E402

NOW = dt.datetime(2026, 10, 7, 15, 0, tzinfo=dt.timezone.utc)   # a Wednesday afternoon
PEOPLE = ["Alice", "Ben", "Sofia", "Dana", "Emil", "Farah"]

SOFTWARE_CONFIG = {
    "title": "Northstar billing (synthetic playground)",
    "lanes": [
        {"id": "intent", "label": "Intent", "description": "Docs and decisions", "paths": ["README", "docs/"]},
        {"id": "build", "label": "Build", "description": "Application code", "paths": ["src/"]},
        {"id": "verify", "label": "Verify", "description": "Tests", "paths": ["tests/"]},
        {"id": "ship", "label": "Ship", "description": "Build and deploy", "paths": [".github/", "deploy/"]},
    ],
}

# Each shape: repository, lane config, and six work "slots" (title, files). Slot order is fixed, so the
# same work keeps the same number when only the relation or the volume changes.
SHAPES = {
    "software": {
        "label": "Software", "repo": "northstar/billing", "config": SOFTWARE_CONFIG,
        "slots": [("Session tokens", ["src/auth/session.py", "src/auth/tokens.py"]),
                  ("Invoice totals", ["src/billing/invoice.py"]),
                  ("Session test suite", ["tests/auth/test_session.py"]),
                  ("Helm chart values", ["deploy/helm/values.yaml"]),
                  ("API reference", ["docs/api.md"]),
                  ("Tax rules", ["src/billing/tax.py"])],
    },
    "ml": {
        "label": "ML", "repo": "northstar/recsys", "config": demo_lab.RECSYS_CONFIG,
        "slots": [("Tokenizer v2 features", ["pipeline/features/tokenize.py", "pipeline/features/vocab.py"]),
                  ("Embedding dim 1024", ["model/embed.py", "model/config.yaml"]),
                  ("Multilingual eval set", ["eval/multilingual/run.py"]),
                  ("Batch scoring endpoint", ["api/batch.py"]),
                  ("Click-log snapshot", ["data/sources.yaml"]),
                  ("Model card", ["docs/model-card.md"])],
    },
    "hackathon": {
        "label": "Hackathon", "repo": "northstar/voice-notes", "config": collab_lab.CONFIG,
        "slots": [("Audio capture pipeline", ["src/audio/capture.py", "src/audio/buffer.py"]),
                  ("Local transcription", ["src/transcribe/local.py"]),
                  ("Recorder UI", ["web/recorder/Recorder.tsx"]),
                  ("Transcription evals", ["evals/transcription/run.py"]),
                  ("Pitch deck notes", ["docs/pitch.md"]),
                  ("Waveform view", ["web/waveform/Waveform.tsx"])],
    },
}
RELATIONS = {
    "parallel": "Parallel work",
    "overlap": "Overlap",
    "waiting": "Waiting",
    "stale": "Stale",
    "burst": "Agent burst",
}
VOLUMES = {"low": 2, "high": 6}   # work items in flight
COLLAB = {
    "none": "Nothing declared",
    "commitment": "Commitments + deadline",
    "freeze": "Freeze ahead",
    "conflict": "Freeze crossed",
}


def matrix() -> list[dict]:
    """The prebuilt states. Not a full Cartesian product: declared collaboration is a hackathon
    concern, and each declared variant is shown with calm and with overlapping work only."""
    out = []
    for shape in SHAPES:
        for rel in RELATIONS:
            for vol in VOLUMES:
                out.append({"shape": shape, "relation": rel, "volume": vol, "collab": "none"})
    for collab in ("commitment", "freeze", "conflict"):
        for rel in ("parallel", "overlap"):
            for vol in VOLUMES:
                out.append({"shape": "hackathon", "relation": rel, "volume": vol, "collab": collab})
    return out


def state_id(spec: dict) -> str:
    return f'{spec["shape"]}.{spec["relation"]}.{spec["volume"]}.{spec["collab"]}'


def _clock(t: dt.datetime) -> str:
    return t.strftime("%a %H:%M")


def observations(spec: dict) -> dict:
    """Semantic spec -> the observation bundle the collector would have produced."""
    shape = SHAPES[spec["shape"]]
    r = Repo(shape["repo"])
    slots = shape["slots"][: VOLUMES[spec["volume"]]]

    for i, (title, files) in enumerate(slots):
        number, author = 10 + i, PEOPLE[i]
        start = NOW - dt.timedelta(hours=12 - 0.5 * i)
        times, body, trailer = hours(start, 0, 3, 6, 9.5), "", ""       # last activity 2.5 h ago or later
        if i == 1:  # the relation is always expressed by the second piece of work, relative to the first
            rel = spec["relation"]
            if rel == "overlap":
                files = files + [slots[0][1][0]]            # also changes the first item's file
            elif rel == "waiting":
                body = f"Depends on #{number - 1}."
            elif rel == "stale":
                times = hours(NOW - dt.timedelta(days=5), 0, 1)
            elif rel == "burst":
                times = [NOW - dt.timedelta(hours=2) + dt.timedelta(minutes=2 * k) for k in range(24)]
                trailer = AGENT
        r.open_pr(number, title, author, files, times, head=f"{author.lower()}/{files[0].split('/')[-1].split('.')[0]}",
                  body=body, trailer=trailer)
    obs = r.observe(NOW, f"Playground: {state_id(spec)}")
    obs["meta"]["source"] = "synthetic (Semantic UI Playground)"
    return obs


def declarations(spec: dict) -> dict | None:
    """What the team declared at the morning check-in, through the real extractor and a named confirmation."""
    if spec["collab"] == "none":
        return None
    frozen = SHAPES[spec["shape"]]["slots"][0][1][0].rsplit("/", 1)[0] + "/"     # the first item's directory
    session_at = NOW - dt.timedelta(hours=10)
    lines = [f"Morning check-in, {_clock(session_at)}.",
             f"- SUBMISSION at {_clock(NOW + dt.timedelta(hours=15))}",
             "- @Alice: first piece of work end to end (by {}) [#10]".format(_clock(NOW + dt.timedelta(hours=6)))]
    if spec["collab"] in ("freeze", "conflict"):
        at = NOW - dt.timedelta(hours=3) if spec["collab"] == "conflict" else NOW + dt.timedelta(hours=4)
        lines.insert(1, f"- FREEZE {frozen} at {_clock(at)}")
    if spec["collab"] == "commitment":
        lines.append("- @Ben: second piece of work reviewed (by {}) [#11]".format(_clock(NOW + dt.timedelta(hours=3))))
        lines.append("- @Dana: evaluation numbers for the pitch (by {}) [evals/]".format(_clock(NOW - dt.timedelta(hours=1))))
    data = co.empty()
    sid = co.propose(data, "\n".join(lines), "Morning check-in", iso(session_at))
    co.confirm(data, sid, by="Alice", at=iso(session_at + dt.timedelta(minutes=15)))
    return data


def config(spec: dict) -> dict:
    return SHAPES[spec["shape"]]["config"]
