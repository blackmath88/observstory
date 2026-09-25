#!/usr/bin/env python3
"""Pair-level breakdown of overlap measurements.

  python3 evals/precision/analyze.py [measurements.json] [--config '{"signals": {...}}']

Every parallel pair behind an overlap signal gets exactly one noise category (first match wins),
or, if clean, a patch-level class. Categories are mechanical; human labels live in labels.json.
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from observstory import config  # noqa: E402
from observstory.derive import derive, parse_time  # noqa: E402

DATA = pathlib.Path(__file__).parent / "data"
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from git_study import BOTS, GENERATED  # noqa: E402

ORDER = ["closed_pr", "stale_participant", "bot_participant", "sweeping_participant", "stacked", "generated_only"]


def load_items(repo_slug, cfg):
    obs = json.loads((DATA / f"{repo_slug}.observations.json").read_text())
    now = parse_time(obs["fetched_at"])
    snap = derive(obs, cfg, now)
    return {w["id"]: w for w in snap["work_items"]}, now


def classify(pair, items, now, stale_hours, closed):
    a, b = (items[x] for x in pair["pair"])
    idle = [(now - parse_time(w["last_activity_at"])).total_seconds() / 3600 for w in (a, b) if w["last_activity_at"]]
    if any(w["id"] in closed for w in (a, b)):
        return "closed_pr"
    if any(h > stale_hours for h in idle):
        return "stale_participant"
    if any(BOTS.search(x) for w in (a, b) for x in w["actors"]):
        return "bot_participant"
    if any(len(w["paths"]) >= 50 for w in (a, b)):
        return "sweeping_participant"
    if pair["stacked"]:
        return "stacked"
    files = pair["shared_files_in_area"]
    if files and all(GENERATED.search(f) for f in files):
        return "generated_only"
    if pair["hunk_overlap_files"]:
        return "clean:same_lines"
    if files:
        return "clean:same_file"
    return "clean:area_only"


def main():
    args = sys.argv[1:]
    name = next((a for a in args if a.endswith(".json") and not a.startswith("{")), "measurements.json")
    cfg = config.normalise(json.loads(args[args.index("--config") + 1]) if "--config" in args else None)
    closed = set(json.loads((DATA / "pr_states.json").read_text()).get("closed", [])) \
        if (DATA / "pr_states.json").exists() else set()
    rows = json.loads((DATA / name).read_text())
    total, per_repo, examples = Counter(), {}, []
    for r in rows:
        slug = r["repo"].replace("/", "__")
        items, now = load_items(slug, cfg)
        c = Counter()
        for s in r["signals"]:
            for p in s["pairs"]:
                cat = classify(p, items, now, cfg["signals"]["stale_hours"],
                               {x.split("#")[1] for x in closed if x.startswith(r["repo"] + "#")})
                c[cat] += 1
                if cat.startswith("clean"):
                    examples.append({"repo": r["repo"], "area": s["area"], "pair": p["pair"], "class": cat,
                                     "files": p["shared_files_in_area"][:5], "hunk_files": p["hunk_overlap_files"][:5],
                                     "titles": [items[x]["title"] for x in p["pair"]],
                                     "urls": [items[x]["url"] for x in p["pair"]]})
        per_repo[r["repo"]] = {"signals": len(r["signals"]), "pairs": sum(c.values()), **c}
        total += c
    out = {"per_repo": per_repo, "total": dict(total), "clean_pairs": examples}
    (DATA / name.replace("measurements", "breakdown")).write_text(json.dumps(out, indent=1))
    cols = ["signals", "pairs"] + ORDER + ["clean:same_lines", "clean:same_file", "clean:area_only"]
    print("repo".ljust(20) + "".join(c.split(":")[-1][:10].rjust(11) for c in cols))
    for repo, row in per_repo.items():
        print(repo[:19].ljust(20) + "".join(str(row.get(c, 0)).rjust(11) for c in cols))
    print("TOTAL".ljust(20) + str(sum(v["signals"] for v in per_repo.values())).rjust(11)
          + str(sum(total.values())).rjust(11) + "".join(str(total.get(c, 0)).rjust(11) for c in cols[2:]))


if __name__ == "__main__":
    main()
