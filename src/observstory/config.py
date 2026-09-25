"""Configuration: every field is optional. Zero-config must be useful (principle 4)."""

from __future__ import annotations

import json
import pathlib

DEFAULT_LANES = [
    {"id": "intent", "label": "Intent", "description": "Framing, research and decisions",
     "paths": ["README", "docs/", "research/", "ARCHITECTURE", "DECISIONS", "ROADMAP", "adr/"]},
    {"id": "build", "label": "Build", "description": "Product implementation",
     "paths": ["src/", "app/", "apps/", "lib/", "libs/", "packages/", "public/", "services/", "cmd/", "internal/", "scripts/"]},
    {"id": "verify", "label": "Verify", "description": "Tests, evaluations and evidence",
     "paths": ["test/", "tests/", "__tests__/", "spec/", "evals/", "fixtures/", "e2e/"]},
    {"id": "ship", "label": "Ship", "description": "Automation, deployment and runtime",
     "paths": [".github/", "Dockerfile", "docker-compose", "deploy/", "infra/", "action.yml", "Makefile"]},
]

DEFAULT_IGNORE = [
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock", "go.sum",
    "uv.lock", "Gemfile.lock", "composer.lock",
    "dist/", "build/", "node_modules/", "vendor/", "*.min.js", "*.min.css", "*.map",
    "/observstory/",  # the generated output; leading "/" anchors to the repo root (gitignore style)
]

DEFAULT_CONTAINERS = ["src", "packages", "apps", "services", "lib", "libs", "app", "modules", "crates", "internal", "cmd"]

DEFAULT_SIGNALS = {
    "overlap_min_work_items": 2,
    "stale_hours": 72,
    "burst_min_commits": 8,
    "burst_window_minutes": 30,
}

DEFAULTS = {
    "title": "Project Observatory",
    "window_hours": 48,
    "max_commits": 60,
    "max_pull_requests": 40,
    "max_open_pull_requests": 30,
    "max_branches": 20,
    "max_issues": 40,
    "area_depth": 1,
}


class ConfigError(ValueError):
    pass


def normalise(user: dict | None) -> dict:
    """Merge a user config over the defaults and validate the shape."""
    user = user or {}
    if not isinstance(user, dict):
        raise ConfigError("config must be a JSON object")
    cfg = dict(DEFAULTS)
    for key in DEFAULTS:
        if user.get(key) is not None:
            cfg[key] = user[key]
    cfg["source"] = "file" if user else "default"
    lanes = user.get("lanes")
    if lanes:
        seen = set()
        for lane in lanes:
            if not isinstance(lane, dict) or not lane.get("id"):
                raise ConfigError("each lane needs an 'id'")
            if lane["id"] in seen:
                raise ConfigError(f"duplicate lane id {lane['id']!r}")
            seen.add(lane["id"])
            if not isinstance(lane.get("paths", []), list):
                raise ConfigError(f"lane {lane['id']!r}: 'paths' must be a list")
        cfg["lanes"] = [dict(lane, source="config") for lane in lanes]
        cfg["lanes_source"] = "config"
    else:
        cfg["lanes"] = [dict(lane, source="default") for lane in DEFAULT_LANES]
        cfg["lanes_source"] = "default"
    cfg["ignore"] = list(DEFAULT_IGNORE) + list(user.get("ignore", []))
    cfg["containers"] = list(user.get("containers", DEFAULT_CONTAINERS))
    signals = dict(DEFAULT_SIGNALS)
    for key, value in (user.get("signals") or {}).items():
        if key not in DEFAULT_SIGNALS:
            raise ConfigError(f"unknown signal setting {key!r}")
        if not isinstance(value, (int, float)) or value <= 0:
            raise ConfigError(f"signal setting {key!r} must be a positive number")
        signals[key] = value
    cfg["signals"] = signals
    return cfg


def load(path: str | pathlib.Path | None) -> dict:
    if path:
        p = pathlib.Path(path)
        if p.exists():
            try:
                return normalise(json.loads(p.read_text(encoding="utf-8")))
            except json.JSONDecodeError as exc:
                raise ConfigError(f"{p}: invalid JSON ({exc})") from exc
    return normalise(None)
