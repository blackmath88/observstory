import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from observstory import config, derive  # noqa: E402

FIXTURES = ROOT / "fixtures" / "observations"


def observations(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def snapshot(name, user_config=None):
    obs = observations(name)
    return derive.derive(obs, config.normalise(user_config), derive.parse_time(obs["fetched_at"]))


def of_type(snap, kind):
    return [s for s in snap["signals"] if s["type"] == kind]
