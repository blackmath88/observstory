#!/usr/bin/env python3
"""Precision study, git-only mode.

This session can read public repositories over git but not through the GitHub REST API, so this
script builds observation bundles (observstory.observations/v1) from a local blobless clone and
runs them through the *unmodified* product derive(). run.py is the API-mode equivalent.

How git stands in for the API:
  open PRs          refs/pull/N/merge exists (GitHub keeps merge refs for open PRs); validated on a
                    sample against the PR web pages (see precision-report.md)
  "recently updated" the 30 open PRs with the newest head-commit date (collector: 30 most recently updated)
  merge base        git merge-base <default> <head>  (identical to compare's merge_base_commit)
  PR files/commits  git diff --name-only / git log  <merge-base>..<head>
  PR base branch    unknown in git; assumed to be the default branch (stacked PRs are flagged in measure)
  titles, authors   head-commit subject and git author names (not GitHub logins)

  python3 evals/precision/git_study.py collect OWNER/REPO ...
  python3 evals/precision/git_study.py measure
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from observstory import OBSERVATIONS_SCHEMA, config  # noqa: E402
from observstory.derive import derive, iso, parse_time  # noqa: E402

DATA = pathlib.Path(__file__).parent / "data"
CLONES = pathlib.Path.home() / "precision-clones"
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", re.MULTILINE)
BOTS = re.compile(r"(\[bot\]|^dependabot|^renovate|^github-actions|^pre-commit-ci|-bot$)", re.I)
GENERATED = re.compile(r"(^|/)(CHANGELOG[^/]*|[^/]*\.lock|[^/]*\.snap|pnpm-lock\.yaml|package\.json|Cargo\.toml|"
                       r"pyproject\.toml|go\.mod|go\.sum)$", re.I)
CONTEXT = 3
SEP = "\x1f"


def git(repo: pathlib.Path, *args: str, check=True) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=900)
    if check and out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {out.stderr.strip()[:300]}")
    return out.stdout


def slug(repo: str) -> str:
    return repo.replace("/", "__")


def ensure_clone(repo: str) -> tuple[pathlib.Path, str]:
    path = CLONES / slug(repo)
    url = f"https://github.com/{repo}"
    if not (path / ".git").exists():
        path.mkdir(parents=True, exist_ok=True)
        git(path, "init", "-q")
        git(path, "remote", "add", "origin", url)
        git(path, "config", "remote.origin.promisor", "true")
        git(path, "config", "remote.origin.partialclonefilter", "blob:none")
    head = git(path, "ls-remote", "--symref", "origin", "HEAD")
    default = re.search(r"ref: refs/heads/(\S+)\s+HEAD", head).group(1)
    return path, default


def commit_rows(repo: pathlib.Path, rev_range: list[str], with_paths: bool) -> list[dict]:
    fmt = "\x1e" + SEP.join(["%H", "%P", "%an", "%cI", "%s"])  # separator first: --name-only prints files after the record
    args = ["log", f"--format={fmt}", *rev_range]
    if with_paths:
        args.insert(1, "--name-only")
    rows = []
    for chunk in git(repo, *args).split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        head, *files = chunk.strip("\n").split("\n")
        sha, parents, author, date, subject = head.split(SEP)
        rows.append({"sha": sha, "parents": parents.split(), "date": date.replace("+00:00", "Z"),
                     "author": {"login": None, "name": author, "type": "Bot" if BOTS.search(author) else "User"},
                     "message": subject, "paths": [f for f in files if f]})
    return rows


def cmd_collect(repos: list[str], max_prs=30, max_branches=20, window_hours=48):
    for repo in repos:
        path, default = ensure_clone(repo)
        now = dt.datetime.now(dt.timezone.utc)
        refs = git(path, "ls-remote", "origin", "refs/pull/*/merge", "refs/pull/*/head", "refs/heads/*")
        heads, merges, branches = {}, set(), {}
        for line in refs.splitlines():
            sha, ref = line.split("\t")
            if m := re.match(r"refs/pull/(\d+)/(head|merge)$", ref):
                (merges.add(int(m.group(1))) if m.group(2) == "merge" else heads.__setitem__(int(m.group(1)), sha))
            elif ref.startswith("refs/heads/"):
                branches[ref[len("refs/heads/"):]] = sha
        open_prs = sorted(n for n in merges if n in heads)
        specs = [f"+refs/heads/{default}:refs/remotes/origin/{default}"]
        specs += [f"+refs/pull/{n}/head:refs/pr/{n}" for n in open_prs]
        git(path, "fetch", "-q", "--filter=blob:none", "origin", *specs)
        dates = {}
        for line in git(path, "for-each-ref", "--format=%(refname:short) %(committerdate:iso-strict)", "refs/pr").splitlines():
            ref, date = line.split(" ")
            dates[int(ref.split("/")[-1])] = date
        chosen = sorted(open_prs, key=lambda n: dates.get(n, ""), reverse=True)[:max_prs]
        base_ref = f"refs/remotes/origin/{default}"
        prs = []
        for n in chosen:
            head = f"refs/pr/{n}"
            mb = git(path, "merge-base", base_ref, head, check=False).strip()
            if not mb:
                continue
            cs = commit_rows(path, [f"{mb}..{head}"], with_paths=False)
            files = [f for f in git(path, "diff", "--name-only", mb, head).splitlines() if f]
            author = cs[-1]["author"] if cs else {"login": None, "name": "unknown", "type": "User"}
            prs.append({
                "number": n, "title": cs[0]["message"] if cs else f"PR {n}", "body": "", "state": "open",
                "draft": False, "merged": False, "head": f"pull/{n}", "base": default, "author": author,
                "created_at": cs[-1]["date"] if cs else None, "updated_at": dates.get(n, "").replace("+00:00", "Z"),
                "url": f"https://github.com/{repo}/pull/{n}", "requested_reviewers": [], "paths": files,
                "commits": [{k: c[k] for k in ("sha", "date", "author", "message", "parents")} for c in cs],
                "merge_base": {"sha": mb, "source": "compare"}, "_head_sha": heads[n],
            })
        pr_shas = {heads[n] for n in heads}
        candidates = sorted(b for b, sha in branches.items() if b != default and sha not in pr_shas)
        branch_rows = []
        if candidates[:max_branches]:
            git(path, "fetch", "-q", "--filter=blob:none", "origin",
                *[f"+refs/heads/{b}:refs/remotes/origin/{b}" for b in candidates[:max_branches]])
        for b in candidates[:max_branches]:
            ref = f"refs/remotes/origin/{b}"
            mb = git(path, "merge-base", base_ref, ref, check=False).strip()
            if not mb:
                continue
            cs = commit_rows(path, [f"{mb}..{ref}"], with_paths=False)
            branch_rows.append({"name": b, "url": f"https://github.com/{repo}/tree/{b}", "ahead_by": len(cs),
                                "paths": [f for f in git(path, "diff", "--name-only", mb, ref).splitlines() if f] if cs else [],
                                "commits": cs[:250], "merge_base": {"sha": mb, "source": "compare"}})
        since = now - dt.timedelta(hours=window_hours)
        commits = commit_rows(path, ["--since", iso(since), base_ref], with_paths=True)[:60]
        for c in commits:
            c["url"] = f"https://github.com/{repo}/commit/{c['sha']}"
        obs = {
            "schema": OBSERVATIONS_SCHEMA, "fetched_at": iso(now),
            "repository": {"full_name": repo, "url": f"https://github.com/{repo}", "default_branch": default,
                           "visibility": "public", "description": None},
            "window": {"hours": float(window_hours), "since": iso(since)},
            "trigger": {"event": "precision-study-git"},
            "commits": commits, "pull_requests": prs, "branches": branch_rows, "issues": [],
            "meta": {"source": "git (precision study adapter)", "api_calls": 0, "rate_limit_remaining": None,
                     "degraded": [], "commits_truncated": len(commits) >= 60, "open_prs_total": len(open_prs)},
        }
        (DATA / f"{slug(repo)}.observations.json").write_text(json.dumps(obs, indent=1))
        print(f"{repo}: {len(open_prs)} open PRs (merge refs), inspected {len(prs)}, "
              f"{len(branch_rows)} unproposed branches, {len(commits)} default-branch commits in {window_hours}h")


# ------------------------------------------------------------------ measure

def old_ranges(diff: str) -> dict[str, list[tuple[int, int]]]:
    out, current = {}, None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current = line.split(" b/", 1)[-1]
            out.setdefault(current, [])
        elif current and (m := HUNK.match(line)):
            start, length = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
            out[current].append((start, start + max(length, 1) - 1))
    return out


def intersects(a, b):
    return any(x0 - CONTEXT <= y1 and y0 - CONTEXT <= x1 for x0, x1 in a for y0, y1 in b)


def cmd_measure(cfg_override: dict | None = None, out_name="measurements.json"):
    cfg = config.normalise(cfg_override)
    results = []
    for obs_path in sorted(DATA.glob("*.observations.json")):
        obs = json.loads(obs_path.read_text())
        repo = obs["repository"]["full_name"]
        path, _ = ensure_clone(repo)
        snap = derive(obs, cfg, parse_time(obs["fetched_at"]))
        items = {w["id"]: w for w in snap["work_items"]}
        pr_obs = {f"pr:{p['number']}": p for p in obs["pull_requests"]}
        br_obs = {f"branch:{b['name']}": b for b in obs["branches"]}

        def rev_of(item_id):
            if item_id in pr_obs:
                return pr_obs[item_id]["merge_base"]["sha"], f"refs/pr/{pr_obs[item_id]['number']}"
            b = br_obs[item_id]
            return b["merge_base"]["sha"], f"refs/remotes/origin/{b['name']}"

        def ranges_for(item_id, files, later_shas=()):
            if item_id.startswith("direct:"):
                out = {}
                for sha in later_shas:
                    for f, r in old_ranges(git(path, "show", "-U0", "--format=", sha, "--", *files)).items():
                        out.setdefault(f, []).extend(r)
                return out
            mb, head = rev_of(item_id)
            return old_ranges(git(path, "diff", "-U0", mb, head, "--", *files))

        sigs = [s for s in snap["signals"] if s["type"] == "overlap"]
        row = {"repo": repo, "fetched_at": obs["fetched_at"], "open_prs_total": obs["meta"].get("open_prs_total"),
               "in_flight": snap["summary"]["in_flight"], "areas_active": snap["summary"]["areas_active"],
               "overlaps": len(sigs), "signals": []}
        for s in sigs:
            members = [items[i] for i in s["work_items"]]
            later = {}
            for e in s["evidence"]:
                if e["kind"] == "base":
                    d = next((x for x in e["work_items"] if x.startswith("direct:")), None)
                    if d:
                        short = re.findall(r"\b([0-9a-f]{7})\b", e["detail"].split(":")[-1])
                        later[d] = [c["sha"] for c in obs["commits"] if c["sha"][:7] in short]
            pair_rows = []
            for pair in s["rule"]["params"]["parallel_pairs"]:
                a, b = pair.split("|")
                files = sorted(set(items[a]["paths"]) & set(items[b]["paths"]))
                if a.startswith("direct:") or b.startswith("direct:"):
                    d = a if a.startswith("direct:") else b
                    later_paths = {p for c in obs["commits"] if c["sha"] in later.get(d, []) for p in c["paths"]}
                    files = [f for f in files if f in later_paths]
                area_files = [f for f in files if any(e["kind"] == "file" and e["ref"] == f for e in s["evidence"])]
                stacked = False
                if not a.startswith("direct:") and not b.startswith("direct:"):
                    (_, ha), (_, hb) = rev_of(a), rev_of(b)
                    stacked = any(subprocess.run(["git", "-C", str(path), "merge-base", "--is-ancestor", x, y]).returncode == 0
                                  for x, y in ((ha, hb), (hb, ha)))
                hunk = []
                if area_files:
                    ra = ranges_for(a, area_files, later.get(a, ()))
                    rb = ranges_for(b, area_files, later.get(b, ()))
                    hunk = [f for f in area_files if intersects(ra.get(f, []), rb.get(f, []))]
                pair_rows.append({"pair": [a, b], "shared_files_in_area": area_files, "hunk_overlap_files": hunk,
                                  "stacked": stacked})
            shared = [e["ref"] for e in s["evidence"] if e["kind"] == "file"]
            row["signals"].append({
                "id": s["id"], "area": s["subject"]["id"], "confidence": s["confidence"], "basis": s["basis"],
                "work_items": [{"id": w["id"], "title": w["title"], "actors": w["actors"], "files": len(w["paths"]),
                                "url": w["url"]} for w in members],
                "shared_files": shared, "pairs": pair_rows,
                "flags": {
                    "bot_participant": any(BOTS.search(a) for w in members for a in w["actors"]),
                    "generated_only": bool(shared) and all(GENERATED.search(f) for f in shared),
                    "sweeping_participant": any(len(w["paths"]) >= 50 for w in members),
                    "same_author": s["rule"]["params"]["same_author"],
                    "has_direct": any(w["kind"] == "direct" for w in members),
                    "stacked_pair": any(p["stacked"] for p in pair_rows),
                    "hunk_overlap": any(p["hunk_overlap_files"] for p in pair_rows),
                },
            })
        results.append(row)
        print(f"{repo}: {len(sigs)} overlaps / {snap['summary']['in_flight']} in flight")
    (DATA / out_name).write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        cmd_collect(sys.argv[2:])
    else:
        cmd_measure()
