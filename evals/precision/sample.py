#!/usr/bin/env python3
"""Draw a fixed-seed stratified sample of overlap pairs for manual labelling -> data/sample.json.

Strata (bot pairs excluded; they are measured mechanically):
  A  unmerged × unmerged, same lines      B  unmerged × unmerged, same file, different lines
  C  unmerged × unmerged, area only       D  landed × unmerged (any patch class)
"""

import json
import pathlib
import random
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "src"))
sys.path.insert(0, str(HERE))
from analyze import DATA, load_items  # noqa: E402
from git_study import BOTS, CLONES, slug  # noqa: E402
from observstory import config  # noqa: E402

SIZES = {"A": 20, "B": 20, "C": 25, "D": 20}


def subjects(repo, item, obs):
    path = CLONES / slug(repo)
    if item["kind"] == "direct":
        return [c["message"] for c in obs["commits"] if c["author"]["name"] == item["id"][7:]][:5]
    ref = f"refs/pr/{item['number']}" if item["kind"] == "pull_request" else f"refs/remotes/origin/{item['head']}"
    base = next(p["merge_base"]["sha"] for p in obs["pull_requests"] + obs["branches"]
                if (p.get("number") == item.get("number") and item["kind"] == "pull_request") or p.get("name") == item["head"])
    out = subprocess.run(["git", "-C", str(path), "log", "--no-merges", "--format=%s", f"{base}..{ref}"],
                         capture_output=True, text=True).stdout.splitlines()
    return out[:5]


def main():
    cfg = config.normalise(None)
    strata = {k: [] for k in SIZES}
    for r in json.loads((DATA / "measurements.json").read_text()):
        items, _ = load_items(slug(r["repo"]), cfg)
        obs = json.loads((DATA / f"{slug(r['repo'])}.observations.json").read_text())
        for s in r["signals"]:
            for p in s["pairs"]:
                a, b = (items[i] for i in p["pair"])
                if any(BOTS.search(x) for w in (a, b) for x in w["actors"]) or p["stacked"]:
                    continue
                landed = "direct" in (a["kind"], b["kind"])
                k = "D" if landed else ("A" if p["hunk_overlap_files"] else "B" if p["shared_files_in_area"] else "C")
                strata[k].append((r["repo"], s["area"], p, a, b, obs))
    rng = random.Random(20260925)
    sample = []
    for k, pool in strata.items():
        for repo, area, p, a, b, obs in rng.sample(pool, min(SIZES[k], len(pool))):
            sample.append({
                "stratum": k, "pool_size": len(pool), "repo": repo, "area": area, "pair": p["pair"],
                "shared_files": p["shared_files_in_area"][:6], "same_line_files": p["hunk_overlap_files"][:6],
                "items": [{"id": w["id"], "url": w["url"], "authors": w["actors"], "n_files": len(w["paths"]),
                           "files_in_area": [f for f in w["paths"] if f.startswith(area)][:6],
                           "subjects": subjects(repo, w, obs)} for w in (a, b)],
            })
    (DATA / "sample.json").write_text(json.dumps(sample, indent=1, ensure_ascii=False))
    print({k: (min(SIZES[k], len(v)), len(v)) for k, v in strata.items()})


if __name__ == "__main__":
    main()
