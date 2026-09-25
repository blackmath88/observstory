#!/usr/bin/env python3
"""Precision study for the overlap signal on real repositories.

  python3 evals/precision/run.py collect OWNER/REPO ...   # zero-config collect -> data/<owner>__<repo>.observations.json
  python3 evals/precision/run.py measure                  # derive + patch-level measurement -> data/measurements.json

This is evaluation tooling, not product code. It uses the product's own collect() and derive()
with default configuration, then fetches diff patches only for files named in overlap evidence,
to measure whether the parallel changes touch the same lines.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from observstory import config  # noqa: E402
from observstory.collect import collect  # noqa: E402
from observstory.derive import derive, parse_time  # noqa: E402
from observstory.github import Client  # noqa: E402

DATA = pathlib.Path(__file__).parent / "data"
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)
BOTS = re.compile(r"(\[bot\]$|^dependabot|^renovate|^github-actions|^pre-commit-ci|-bot$)", re.I)
GENERATED = re.compile(r"(^|/)(CHANGELOG[^/]*|.*\.lock|.*\.snap|.*\.generated\..*|package\.json|.*\.min\..*|"
                       r"pnpm-lock\.yaml|Cargo\.toml|go\.mod|pyproject\.toml|uv\.lock)$", re.I)
CONTEXT = 3  # lines of slack when comparing hunks


def slug(repo):
    return repo.replace("/", "__")


def cmd_collect(repos):
    client = Client(os.environ.get("GITHUB_TOKEN", ""), max_calls=900, reserve=200)
    cfg = config.normalise(None)
    for repo in repos:
        start = client.calls
        now = dt.datetime.now(dt.timezone.utc)
        obs = collect(client, repo, cfg, now, {"event": "precision-study"})
        (DATA / f"{slug(repo)}.observations.json").write_text(json.dumps(obs, indent=1))
        print(f"{repo}: {client.calls - start} calls, {len(obs['pull_requests'])} PRs, "
              f"{len(obs['branches'])} branches, {len(obs['commits'])} commits, degraded={len(obs['meta']['degraded'])}")


def ranges(patch):
    """Old-side line ranges touched by a unified diff (relative to the base the diff was taken against)."""
    out = []
    for m in HUNK.finditer(patch or ""):
        start, length = int(m.group(1)), int(m.group(2) or 1)
        out.append((start, start + max(length, 1) - 1))
    return out


def intersects(a, b):
    return any(x0 - CONTEXT <= y1 and y0 - CONTEXT <= x1 for x0, x1 in a for y0, y1 in b)


class Patches:
    def __init__(self, client, repo, obs):
        self.client, self.base, self.obs, self.cache = client, f"/repos/{repo}", obs, {}

    def for_item(self, item, later_shas=()):
        """{path: [old-side ranges]} for a work item. Direct items: only the given commits."""
        key = (item["id"], tuple(later_shas))
        if key in self.cache:
            return self.cache[key]
        files = []
        if item["kind"] == "pull_request":
            files = self.client.get(f"{self.base}/pulls/{item['number']}/files", {"per_page": 100})
        elif item["kind"] == "branch":
            dflt = self.obs["repository"]["default_branch"]
            files = self.client.get(f"{self.base}/compare/{dflt}...{item['head']}").get("files", [])
        else:
            for sha in later_shas:
                files += self.client.get(f"{self.base}/commits/{sha}").get("files", [])
        out = {}
        for f in files:
            out.setdefault(f["filename"], []).extend(ranges(f.get("patch")))
            out[f["filename"] + "#changes"] = [(f.get("changes", 0), 0)]
        self.cache[key] = out
        return out


def cmd_measure():
    client = Client(os.environ.get("GITHUB_TOKEN", ""), max_calls=1500, reserve=200)
    cfg = config.normalise(None)
    results = []
    for path in sorted(DATA.glob("*.observations.json")):
        obs = json.loads(path.read_text())
        repo = obs["repository"]["full_name"]
        snap = derive(obs, cfg, parse_time(obs["fetched_at"]))
        items = {w["id"]: w for w in snap["work_items"]}
        patches = Patches(client, repo, obs)
        sigs = [s for s in snap["signals"] if s["type"] == "overlap"]
        in_flight = [w for w in snap["work_items"] if w["in_flight"]]
        base_sources = {}
        for w in in_flight:
            src = (w.get("merge_base") or {}).get("source", "none")
            base_sources[src] = base_sources.get(src, 0) + 1
        repo_row = {"repo": repo, "fetched_at": obs["fetched_at"], "in_flight": len(in_flight),
                    "areas_active": snap["summary"]["areas_active"], "overlaps": len(sigs),
                    "degraded": obs["meta"]["degraded"], "commits_truncated": obs["meta"].get("commits_truncated"),
                    "merge_base_sources": base_sources, "signals": []}
        for s in sigs:
            members = [items[i] for i in s["work_items"]]
            later = {}  # direct item -> shas cited in base evidence
            for e in s["evidence"]:
                if e["kind"] == "base":
                    d = next((x for x in e["work_items"] if x.startswith("direct:")), None)
                    if d:
                        later[d] = re.findall(r"\b([0-9a-f]{7})\b", e["detail"].split(":")[-1])
            shared = [e["ref"] for e in s["evidence"] if e["kind"] == "file"]
            pairs = [p.split("|") for p in s["rule"]["params"]["parallel_pairs"]]
            pair_rows = []
            for a, b in pairs:
                pa, pb = items[a], items[b]
                if pa["kind"] == "direct" or pb["kind"] == "direct":
                    d = pa if pa["kind"] == "direct" else pb
                    full = [c["sha"] for c in obs["commits"] if c["sha"][:7] in later.get(d["id"], [])]
                else:
                    full = []
                ra = patches.for_item(pa, full if pa["kind"] == "direct" else ())
                rb = patches.for_item(pb, full if pb["kind"] == "direct" else ())
                files = sorted(set(k for k in ra if "#" not in k) & set(k for k in rb if "#" not in k)
                               & ({f for f in shared} or set(ra)))
                hunk_files = [f for f in files if intersects(ra[f], rb[f])]
                pair_rows.append({"pair": [a, b], "shared_files": files, "hunk_overlap_files": hunk_files})
            size = {w["id"]: len(w["paths"]) for w in members}
            results_sig = {
                "id": s["id"], "area": s["subject"]["id"], "confidence": s["confidence"], "basis": s["basis"],
                "work_items": [{"id": w["id"], "title": w["title"], "kind": w["kind"], "state": w["state"],
                                "actors": w["actors"], "files": size[w["id"]],
                                "merge_base_source": (w.get("merge_base") or {}).get("source")} for w in members],
                "shared_files": shared, "pairs": pair_rows,
                "flags": {
                    "bot_participant": any(BOTS.search(a) for w in members for a in w["actors"]),
                    "generated_only": bool(shared) and all(GENERATED.search(f) for f in shared),
                    "sweeping_participant": any(n >= 50 for n in size.values()),
                    "same_author": s["rule"]["params"]["same_author"],
                    "has_direct": any(w["kind"] == "direct" for w in members),
                    "hunk_overlap": any(p["hunk_overlap_files"] for p in pair_rows),
                },
            }
            repo_row["signals"].append(results_sig)
        results.append(repo_row)
        print(f"{repo}: {len(sigs)} overlaps, in_flight={len(in_flight)}")
    (DATA / "measurements.json").write_text(json.dumps(results, indent=1))
    print(f"api calls: {client.calls}")


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        cmd_collect(sys.argv[2:])
    else:
        cmd_measure()
