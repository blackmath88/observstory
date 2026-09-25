#!/usr/bin/env python3
"""Direction 1 prototype: Project Radar, rendered for each demo moment.

  python3 prototypes/radar/build.py   ->  prototypes/radar/demo-t{0..3}.html
The production dashboard (src/observstory/render.py) grew out of this direction.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from observstory import config  # noqa: E402
from observstory.derive import derive, parse_time  # noqa: E402
from observstory.render import render  # noqa: E402

for i in range(4):
    obs = json.loads((ROOT / f"fixtures/observations/demo-t{i}.json").read_text())
    snap = derive(obs, config.normalise(None), parse_time(obs["fetched_at"]))
    (pathlib.Path(__file__).parent / f"demo-t{i}.html").write_text(render(snap))
    print(f"demo-t{i}: {obs['note']}")
