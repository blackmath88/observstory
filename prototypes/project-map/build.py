#!/usr/bin/env python3
"""Project Map demos (issue #3): one page per scenario, all compiled from fixtures.

  python3 prototypes/project-map/build.py            # pages -> prototypes/project-map/*.html
  python3 prototypes/project-map/build.py --shots    # also screenshots -> docs/demo/img/map-*.png (needs Playwright)
"""

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from observstory import config  # noqa: E402
from observstory.derive import derive, parse_time  # noqa: E402
from observstory.map_compiler import compile_scene  # noqa: E402
from observstory.map_render import render_map  # noqa: E402

HERE = pathlib.Path(__file__).parent
ML = json.loads((ROOT / "fixtures/configs/ml-project.json").read_text())
SCENARIOS = {  # page name: (fixture, config, what it shows)
    "demo-t0": ("demo-t0", None, "Two contributors working normally"),
    "demo-t1": ("demo-t1", None, "A second branch starts changing src/conversation"),
    "demo-t2": ("demo-t2", None, "The overlap is visible before either change merges"),
    "demo-t3": ("demo-t3", None, "Resolution: evaluation work that waits on #41"),
    "crowded-area": ("m2-crowded-area", None, "Three overlaps in one area"),
    "ml-project": ("m3-ml-project", ML, "Six custom lanes, a cross-lane overlap and a waiting edge"),
    "long-labels": ("m4-long-labels", None, "Long titles, paths and branch names"),
    "stale": ("e3-stale", None, "Stale work and a branch without a pull request"),
    "quiet": ("m1-empty", None, "Nothing in flight"),
}
SHOTS = [  # (page, png, width, height, click)
    ("demo-t2", "map-demo-t2", 1440, 520, None),
    ("demo-t2", "map-demo-t2-inspector", 1440, 620, ".att-item"),
    ("demo-t3", "map-demo-t3", 1440, 480, None),
    ("ml-project", "map-ml-project", 1440, 560, None),
    ("crowded-area", "map-crowded-area", 1440, 460, '[data-id="pr:70"]'),
    ("demo-t2", "map-narrow", 390, 844, None),
    ("self", "map-self", 1440, 760, None),
]


def page(fixture, cfg):
    obs = json.loads((ROOT / "fixtures/observations" / f"{fixture}.json").read_text())
    snap = derive(obs, config.normalise(cfg), parse_time(obs["fetched_at"]))
    return render_map(compile_scene(snap), radar_href=None)


def main():
    for name, (fixture, cfg, note) in SCENARIOS.items():
        (HERE / f"{name}.html").write_text(page(fixture, cfg))
        print(f"{name}.html  {note}")
    self_snap = HERE / "self-snapshot.json"
    if self_snap.exists():
        (HERE / "self.html").write_text(render_map(compile_scene(json.loads(self_snap.read_text())), radar_href=None))
        print("self.html  Observstory's own repository")
    if "--shots" in sys.argv:
        for name, png, w, h, click in SHOTS:
            if not (HERE / f"{name}.html").exists():
                continue
            subprocess.run(["node", str(HERE / "shot.js"), str(HERE / f"{name}.html"), str(ROOT / "docs/demo/img" / f"{png}.png"),
                            str(w), str(h)] + ([click] if click else []), check=True)


if __name__ == "__main__":
    main()
