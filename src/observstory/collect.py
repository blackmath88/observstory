"""Ingestion: GitHub -> observations bundle (observstory.observations/v1).

The only module that talks to GitHub. It normalises facts and never derives relations (ADR-006).
When the budget runs low it degrades in a fixed order and records what it skipped:
  1. commit file lists  2. branch comparisons  3. PR commit lists  4. PR file lists
"""

from __future__ import annotations

import datetime as dt
import urllib.parse

from . import OBSERVATIONS_SCHEMA
from .derive import iso
from .github import BudgetExhausted, Client


def _author(user: dict | None, fallback: dict | None = None) -> dict:
    if user and user.get("login"):
        return {"login": user["login"], "name": None, "type": user.get("type", "User")}
    return {"login": None, "name": (fallback or {}).get("name") or "unknown", "type": "User"}


def _commit_row(c: dict) -> dict:
    return {"sha": c["sha"], "url": c.get("html_url"),
            "date": c.get("commit", {}).get("author", {}).get("date"),
            "author": _author(c.get("author"), c.get("commit", {}).get("author")),
            "message": c.get("commit", {}).get("message", ""),
            "parents": [x.get("sha") for x in c.get("parents", []) if x.get("sha")]}


def _q(ref: str) -> str:
    return urllib.parse.quote(ref, safe="/")


def collect(client: Client, repository: str, cfg: dict, now: dt.datetime, trigger: dict | None = None) -> dict:
    owner, repo = repository.split("/", 1)
    base = f"/repos/{owner}/{repo}"
    since = iso(now - dt.timedelta(hours=float(cfg["window_hours"])))
    degraded: list[str] = []

    repo_data = client.get(base, essential=True)
    default_branch = repo_data.get("default_branch") or "main"

    # Default-branch commits in the window, each with its file list
    raw_commits = client.get(f"{base}/commits", {"since": since, "per_page": min(int(cfg["max_commits"]), 100)},
                             essential=True)
    commits, skipped = [], 0
    for c in raw_commits:
        row = _commit_row(c)
        try:
            detail = client.get(f"{base}/commits/{c['sha']}")
            row["paths"] = [f["filename"] for f in detail.get("files", [])]
        except BudgetExhausted:
            row["paths"], skipped = [], skipped + 1
        commits.append(row)
    if skipped:
        degraded.append(f"file lists skipped for {skipped} default-branch commits (API budget)")

    # Pull requests (recently updated), with files and commits for open ones
    raw_prs = client.get(f"{base}/pulls", {"state": "all", "sort": "updated", "direction": "desc",
                                           "per_page": min(int(cfg["max_pull_requests"]), 100)}, essential=True)
    open_budget = int(cfg["max_open_pull_requests"])
    prs, pr_heads = [], set()
    for pr in raw_prs:
        head_repo = ((pr.get("head") or {}).get("repo") or {}).get("full_name")
        if head_repo == repository:
            pr_heads.add(pr["head"]["ref"])
        row = {
            "number": pr["number"], "title": pr.get("title", ""), "body": (pr.get("body") or "")[:4000],
            "state": pr.get("state"), "draft": bool(pr.get("draft")), "merged": bool(pr.get("merged_at")),
            "head": (pr.get("head") or {}).get("ref"), "base": (pr.get("base") or {}).get("ref"),
            "author": _author(pr.get("user")), "created_at": pr.get("created_at"), "updated_at": pr.get("updated_at"),
            "url": pr.get("html_url"),
            "requested_reviewers": [u.get("login") for u in pr.get("requested_reviewers", [])]
                                   + [t.get("slug") for t in pr.get("requested_teams", [])],
            "paths": [], "commits": [], "merge_base": None,
        }
        if pr.get("state") == "open" and open_budget > 0:
            open_budget -= 1
            try:
                files = client.get(f"{base}/pulls/{pr['number']}/files", {"per_page": 100})
                row["paths"] = [f["filename"] for f in files]
                if len(files) == 100:
                    degraded.append(f"pr:{pr['number']} has 100+ files; only the first 100 are used")
            except BudgetExhausted:
                degraded.append(f"pr:{pr['number']} file list skipped (API budget)")
            try:
                row["commits"] = [_commit_row(c) for c in client.get(f"{base}/pulls/{pr['number']}/commits",
                                                                     {"per_page": 100})]
            except BudgetExhausted:
                degraded.append(f"pr:{pr['number']} commit list skipped (API budget)")
            # Where did this PR diverge from its base? Prefer compare (merge-base SHA); fall back to the
            # first commit's parent, which is wrong only if the branch merged its base back in (issue #2).
            head_sha = (pr.get("head") or {}).get("sha")
            try:
                cmp = client.get(f"{base}/compare/{_q(row['base'])}...{head_sha or _q(row['head'])}")
                sha = (cmp.get("merge_base_commit") or {}).get("sha")
                row["merge_base"] = {"sha": sha, "source": "compare"} if sha else None
            except BudgetExhausted:
                first = row["commits"][0]["parents"][0] if row["commits"] and row["commits"][0]["parents"] else None
                row["merge_base"] = {"sha": first, "source": "first_parent"} if first else None
                degraded.append(f"pr:{pr['number']} merge base from first-commit parent (API budget)")
        elif pr.get("state") == "open":
            degraded.append(f"pr:{pr['number']} not inspected (max_open_pull_requests reached)")
        prs.append(row)

    # Unmerged branches with no PR (squash-merged PR branches are excluded via pr_heads)
    branches = []
    try:
        raw_branches = client.get(f"{base}/branches", {"per_page": 100})
    except BudgetExhausted:
        raw_branches = []
        degraded.append("branch list skipped (API budget)")
    candidates = [b["name"] for b in raw_branches if b["name"] != default_branch and b["name"] not in pr_heads]
    if len(candidates) > int(cfg["max_branches"]):
        degraded.append(f"{len(candidates) - int(cfg['max_branches'])} branches without PRs not inspected (max_branches)")
    for name in candidates[: int(cfg["max_branches"])]:
        try:
            cmp = client.get(f"{base}/compare/{_q(default_branch)}...{_q(name)}")
        except BudgetExhausted:
            degraded.append(f"branch {name} not compared (API budget)")
            continue
        branches.append({
            "name": name, "url": f"{repo_data.get('html_url')}/tree/{name}", "ahead_by": cmp.get("ahead_by", 0),
            "paths": [f["filename"] for f in cmp.get("files", [])],
            "commits": [_commit_row(c) for c in cmp.get("commits", [])],
            "merge_base": ({"sha": cmp["merge_base_commit"]["sha"], "source": "compare"}
                           if (cmp.get("merge_base_commit") or {}).get("sha") else None),
        })

    # Issues: open, or updated in the window
    issues = []
    try:
        for it in client.get(f"{base}/issues", {"state": "all", "sort": "updated", "direction": "desc",
                                                "per_page": min(int(cfg["max_issues"]), 100)}):
            if "pull_request" in it:
                continue
            if it.get("state") != "open" and (it.get("updated_at") or "") < since:
                continue
            issues.append({"number": it["number"], "title": it.get("title", ""), "state": it.get("state"),
                           "url": it.get("html_url"), "updated_at": it.get("updated_at"),
                           "labels": [lab.get("name", "") for lab in it.get("labels", [])]})
    except BudgetExhausted:
        degraded.append("issues skipped (API budget)")

    return {
        "schema": OBSERVATIONS_SCHEMA,
        "fetched_at": iso(now),
        "repository": {"full_name": repository, "url": repo_data.get("html_url"), "default_branch": default_branch,
                       "visibility": repo_data.get("visibility"), "description": repo_data.get("description")},
        "window": {"hours": float(cfg["window_hours"]), "since": since},
        "trigger": trigger or {},
        "commits": commits, "pull_requests": prs, "branches": branches, "issues": issues,
        "meta": {"source": "GitHub REST API", "api_calls": client.calls,
                 "rate_limit_remaining": client.remaining, "degraded": degraded,
                 "commits_truncated": len(raw_commits) >= min(int(cfg["max_commits"]), 100)},
    }
