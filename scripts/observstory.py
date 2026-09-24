#!/usr/bin/env python3
"""Observstory: turn GitHub repository activity into a typed project snapshot + dashboard."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict


TOKEN = os.environ.get("OBSERVSTORY_TOKEN", "")
REPOSITORY = os.environ.get("OBSERVSTORY_REPOSITORY", "")
OUTPUT = pathlib.Path(os.environ.get("OBSERVSTORY_OUTPUT", "observstory"))
CONFIG_PATH = pathlib.Path(os.environ.get("OBSERVSTORY_CONFIG", "observstory.config.json"))
SERVER_URL = os.environ.get("OBSERVSTORY_SERVER_URL", "https://github.com")
EVENT = os.environ.get("OBSERVSTORY_EVENT", "manual")
RUN_ID = os.environ.get("OBSERVSTORY_RUN_ID", "")
SHA = os.environ.get("OBSERVSTORY_SHA", "")

DEFAULT_CONFIG = {
    "title": "Project Observatory",
    "window_hours": 48,
    "max_commits": 60,
    "max_pull_requests": 40,
    "max_issues": 40,
    "lanes": [
        {"id": "intent", "label": "Intent", "description": "Framing, research and decisions",
         "paths": ["README.md", "docs/", "research/", "ARCHITECTURE.md", "DECISIONS.md"]},
        {"id": "build", "label": "Build", "description": "Product implementation",
         "paths": ["src/", "app/", "lib/", "packages/", "public/"]},
        {"id": "verify", "label": "Verify", "description": "Tests, evaluations and evidence",
         "paths": ["test/", "tests/", "evals/", "fixtures/"]},
        {"id": "ship", "label": "Ship", "description": "Automation and deployment",
         "paths": [".github/", "Dockerfile", "docker-compose", "deploy/", "infra/"]},
    ],
}


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(value: dt.datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            user = json.load(fh)
        cfg.update({k: v for k, v in user.items() if v is not None})
    return cfg


def api(path: str, params: dict | None = None):
    if not TOKEN:
        raise RuntimeError("OBSERVSTORY_TOKEN / github-token is required")
    url = f"https://api.github.com{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "observstory-action",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} for {path}: {body[:500]}") from exc


def classify(path: str, lanes: list[dict]) -> str:
    low = path.lower()
    for lane in lanes:
        for signal in lane.get("paths", []):
            s = signal.lower()
            if low == s or low.startswith(s) or s in low:
                return lane["id"]
    return "other"


def safe_user(item: dict | None) -> str:
    if not item:
        return "unknown"
    return item.get("login") or item.get("name") or "unknown"


def collect(config: dict) -> dict:
    owner, repo = REPOSITORY.split("/", 1)
    window_hours = int(config.get("window_hours", 48))
    since = now_utc() - dt.timedelta(hours=window_hours)
    since_iso = iso(since)

    repo_data = api(f"/repos/{owner}/{repo}")
    commits = api(
        f"/repos/{owner}/{repo}/commits",
        {"since": since_iso, "per_page": min(int(config.get("max_commits", 60)), 100)},
    )
    pulls = api(
        f"/repos/{owner}/{repo}/pulls",
        {"state": "all", "sort": "updated", "direction": "desc",
         "per_page": min(int(config.get("max_pull_requests", 40)), 100)},
    )
    issues_raw = api(
        f"/repos/{owner}/{repo}/issues",
        {"state": "all", "sort": "updated", "direction": "desc",
         "per_page": min(int(config.get("max_issues", 40)), 100)},
    )
    issues = [item for item in issues_raw if "pull_request" not in item]

    lane_activity = {lane["id"]: {"files": {}, "changes": 0, "contributors": set()} for lane in config["lanes"]}
    lane_activity["other"] = {"files": {}, "changes": 0, "contributors": set()}

    contributor_stats = defaultdict(lambda: {"commits": 0, "files": set(), "additions": 0, "deletions": 0})
    file_authors = defaultdict(set)
    file_changes = defaultdict(int)
    commit_rows = []

    # Commit detail supplies changed files and is the main evidence for lane activity.
    for commit in commits:
        detail = api(f"/repos/{owner}/{repo}/commits/{commit['sha']}")
        author = safe_user(commit.get("author")) if commit.get("author") else (
            commit.get("commit", {}).get("author", {}).get("name") or "unknown"
        )
        stats = detail.get("stats", {})
        contributor_stats[author]["commits"] += 1
        contributor_stats[author]["additions"] += int(stats.get("additions", 0))
        contributor_stats[author]["deletions"] += int(stats.get("deletions", 0))

        changed = []
        for file_item in detail.get("files", []):
            filename = file_item.get("filename", "unknown")
            changes = int(file_item.get("changes", 0))
            changed.append(filename)
            contributor_stats[author]["files"].add(filename)
            file_authors[filename].add(author)
            file_changes[filename] += changes

            lane_id = classify(filename, config["lanes"])
            lane = lane_activity[lane_id]
            lane["files"][filename] = lane["files"].get(filename, 0) + changes
            lane["changes"] += changes
            lane["contributors"].add(author)

        commit_rows.append({
            "sha": commit["sha"],
            "short_sha": commit["sha"][:7],
            "message": commit.get("commit", {}).get("message", "").splitlines()[0],
            "author": author,
            "date": commit.get("commit", {}).get("author", {}).get("date"),
            "url": commit.get("html_url"),
            "files": changed,
            "additions": int(stats.get("additions", 0)),
            "deletions": int(stats.get("deletions", 0)),
        })

    lanes = []
    lane_lookup = {lane["id"]: lane for lane in config["lanes"]}
    for lane_id, data in lane_activity.items():
        meta = lane_lookup.get(lane_id, {"id": "other", "label": "Other", "description": "Unclassified project activity"})
        top_files = sorted(data["files"].items(), key=lambda item: item[1], reverse=True)[:12]
        lanes.append({
            "id": lane_id,
            "label": meta.get("label", lane_id.title()),
            "description": meta.get("description", ""),
            "changes": data["changes"],
            "contributors": sorted(data["contributors"]),
            "files": [{"path": p, "changes": c} for p, c in top_files],
        })

    overlaps = []
    for filename, authors in file_authors.items():
        if len(authors) > 1:
            overlaps.append({
                "path": filename,
                "contributors": sorted(authors),
                "changes": file_changes[filename],
                "reason": "Multiple contributors touched this path in the observation window.",
            })
    overlaps.sort(key=lambda row: (len(row["contributors"]), row["changes"]), reverse=True)

    contributors = []
    for name, stats in contributor_stats.items():
        contributors.append({
            "login": name,
            "commits": stats["commits"],
            "files": len(stats["files"]),
            "additions": stats["additions"],
            "deletions": stats["deletions"],
        })
    contributors.sort(key=lambda row: (row["commits"], row["files"]), reverse=True)

    pr_rows = []
    for pr in pulls:
        updated = pr.get("updated_at", "")
        if updated and updated < since_iso:
            continue
        pr_rows.append({
            "number": pr["number"],
            "title": pr.get("title", ""),
            "state": pr.get("state", ""),
            "draft": bool(pr.get("draft")),
            "author": safe_user(pr.get("user")),
            "updated_at": updated,
            "url": pr.get("html_url"),
            "head": pr.get("head", {}).get("ref"),
            "base": pr.get("base", {}).get("ref"),
        })

    issue_rows = []
    for issue in issues:
        updated = issue.get("updated_at", "")
        if updated and updated < since_iso:
            continue
        issue_rows.append({
            "number": issue["number"],
            "title": issue.get("title", ""),
            "state": issue.get("state", ""),
            "author": safe_user(issue.get("user")),
            "updated_at": updated,
            "url": issue.get("html_url"),
            "labels": [label.get("name", "") for label in issue.get("labels", [])],
        })

    open_prs = sum(1 for pr in pr_rows if pr["state"] == "open")
    open_issues = sum(1 for issue in issue_rows if issue["state"] == "open")

    return {
        "schema": "observstory.snapshot/v0",
        "generated_at": iso(now_utc()),
        "window": {"hours": window_hours, "since": since_iso},
        "trigger": {"event": EVENT, "run_id": RUN_ID, "sha": SHA},
        "repository": {
            "full_name": REPOSITORY,
            "url": repo_data.get("html_url"),
            "description": repo_data.get("description"),
            "default_branch": repo_data.get("default_branch"),
            "visibility": repo_data.get("visibility"),
        },
        "summary": {
            "commits": len(commit_rows),
            "contributors": len(contributors),
            "open_pull_requests": open_prs,
            "open_issues": open_issues,
            "overlaps": len(overlaps),
        },
        "contributors": contributors,
        "lanes": lanes,
        "overlaps": overlaps[:20],
        "commits": commit_rows,
        "pull_requests": pr_rows,
        "issues": issue_rows,
        "provenance": {
            "source": "GitHub REST API",
            "repository": REPOSITORY,
            "collector": "blackmath88/observstory",
        },
    }


def esc(value) -> str:
    return html.escape(str(value or ""))


def render(snapshot: dict, config: dict) -> str:
    summary = snapshot["summary"]

    lane_cards = []
    for lane in snapshot["lanes"]:
        files = "".join(
            f'<li><code>{esc(item["path"])}</code><span>{item["changes"]} Δ</span></li>'
            for item in lane["files"][:7]
        ) or "<li class='muted'>No activity in this window.</li>"
        people = ", ".join(lane["contributors"]) or "—"
        lane_cards.append(f"""
        <article class="lane">
          <div class="lane-head">
            <div><span class="eyebrow">LANE</span><h3>{esc(lane["label"])}</h3></div>
            <strong>{lane["changes"]} Δ</strong>
          </div>
          <p>{esc(lane["description"])}</p>
          <div class="people">{esc(people)}</div>
          <ul>{files}</ul>
        </article>""")

    contributor_rows = "".join(
        f"<tr><td>{esc(c['login'])}</td><td>{c['commits']}</td><td>{c['files']}</td>"
        f"<td>+{c['additions']} / −{c['deletions']}</td></tr>"
        for c in snapshot["contributors"]
    ) or "<tr><td colspan='4' class='muted'>No contributor activity.</td></tr>"

    overlap_rows = "".join(
        f"<li><div><code>{esc(o['path'])}</code><small>{esc(', '.join(o['contributors']))}</small></div>"
        f"<strong>{o['changes']} Δ</strong></li>"
        for o in snapshot["overlaps"][:10]
    ) or "<li class='muted'>No multi-contributor path overlap detected.</li>"

    pr_rows = "".join(
        f"<li><a href='{esc(pr['url'])}'>#{pr['number']} {esc(pr['title'])}</a>"
        f"<span>{esc(pr['author'])} · {esc(pr['state'])}</span></li>"
        for pr in snapshot["pull_requests"][:12]
    ) or "<li class='muted'>No recent pull requests.</li>"

    commit_rows = "".join(
        f"<li><a href='{esc(c['url'])}'><code>{esc(c['short_sha'])}</code> {esc(c['message'])}</a>"
        f"<span>{esc(c['author'])} · {len(c['files'])} files</span></li>"
        for c in snapshot["commits"][:14]
    ) or "<li class='muted'>No commits in this window.</li>"

    title = esc(config.get("title", "Project Observatory"))
    repo = esc(snapshot["repository"]["full_name"])
    generated = esc(snapshot["generated_at"])
    hours = snapshot["window"]["hours"]
    raw = json.dumps(snapshot, ensure_ascii=False).replace("</", "<\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · {repo}</title>
<style>
:root{{--bg:#f4f3ef;--panel:#fff;--ink:#191919;--muted:#6f6f69;--line:#d9d7cf;--accent:#bd3768;--soft:#eceae3}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:1400px;margin:auto;padding:28px}}
header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;margin-bottom:26px}}
h1{{font-size:clamp(34px,6vw,72px);line-height:.92;letter-spacing:-.06em;margin:4px 0}}
h2{{font-size:21px;margin:0 0 14px}} h3{{margin:2px 0;font-size:18px}}
p{{color:var(--muted)}} a{{color:inherit;text-decoration:none}} a:hover{{text-decoration:underline}}
.eyebrow{{font-size:11px;font-weight:800;letter-spacing:.13em;color:var(--muted)}}
.meta{{text-align:right;color:var(--muted);font-size:12px}}
.grid{{display:grid;gap:12px}} .metrics{{grid-template-columns:repeat(5,1fr);margin-bottom:24px}}
.metric,.panel,.lane{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}}
.metric strong{{font-size:30px;display:block;letter-spacing:-.04em}}
.lanes{{grid-template-columns:repeat(auto-fit,minmax(220px,1fr));margin-bottom:24px}}
.lane{{min-height:280px}} .lane-head{{display:flex;justify-content:space-between;gap:16px;align-items:start}}
.lane-head>strong{{font-size:12px;background:var(--soft);padding:6px 8px;border-radius:999px}}
.people{{font-size:12px;margin:10px 0 14px;color:var(--accent)}}
.columns{{grid-template-columns:1.1fr .9fr;margin-bottom:12px}}
ul{{list-style:none;padding:0;margin:0}} li{{display:flex;justify-content:space-between;gap:18px;border-top:1px solid var(--line);padding:9px 0}}
li span,small{{color:var(--muted);font-size:12px}} small{{display:block;margin-top:3px}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}}
table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;border-top:1px solid var(--line);padding:9px 6px}} th{{font-size:11px;color:var(--muted);letter-spacing:.08em}}
.muted{{color:var(--muted)}} footer{{color:var(--muted);font-size:12px;padding:22px 2px}}
@media(max-width:800px){{main{{padding:16px}}header{{display:block}}.meta{{text-align:left;margin-top:12px}}.metrics{{grid-template-columns:repeat(2,1fr)}}.columns{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<main>
<header>
  <div><span class="eyebrow">OBSERVSTORY / LIVE PROJECT STATE</span><h1>{repo}</h1><p>{title} · last {hours} hours</p></div>
  <div class="meta">Generated {generated}<br>Trigger: {esc(snapshot["trigger"]["event"])}</div>
</header>

<section class="grid metrics">
  <div class="metric"><span class="eyebrow">COMMITS</span><strong>{summary["commits"]}</strong></div>
  <div class="metric"><span class="eyebrow">PEOPLE</span><strong>{summary["contributors"]}</strong></div>
  <div class="metric"><span class="eyebrow">OPEN PRS</span><strong>{summary["open_pull_requests"]}</strong></div>
  <div class="metric"><span class="eyebrow">OPEN ISSUES</span><strong>{summary["open_issues"]}</strong></div>
  <div class="metric"><span class="eyebrow">OVERLAPS</span><strong>{summary["overlaps"]}</strong></div>
</section>

<section>
  <div class="eyebrow">PROJECT TOPOLOGY</div>
  <h2>Typed lanes</h2>
  <div class="grid lanes">{''.join(lane_cards)}</div>
</section>

<section class="grid columns">
  <article class="panel"><div class="eyebrow">COLLABORATION SIGNAL</div><h2>Shared paths</h2><ul>{overlap_rows}</ul></article>
  <article class="panel"><div class="eyebrow">ACTIVE WORK</div><h2>Pull requests</h2><ul>{pr_rows}</ul></article>
</section>

<section class="grid columns">
  <article class="panel"><div class="eyebrow">RECENT FLOW</div><h2>Commits</h2><ul>{commit_rows}</ul></article>
  <article class="panel"><div class="eyebrow">CONTRIBUTORS</div><h2>Activity</h2>
    <table><thead><tr><th>Person</th><th>Commits</th><th>Files</th><th>Diff</th></tr></thead><tbody>{contributor_rows}</tbody></table>
  </article>
</section>

<footer>Observstory · state derived from GitHub metadata · <a href="data/snapshot.json">machine-readable snapshot</a></footer>
</main>
<script type="application/json" id="observstory-snapshot">{raw}</script>
</body>
</html>"""


def main():
    if not REPOSITORY or "/" not in REPOSITORY:
        raise RuntimeError("OBSERVSTORY_REPOSITORY must be owner/repo")
    config = load_config()
    snapshot = collect(config)
    data_dir = OUTPUT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    with (data_dir / "snapshot.json").open("w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, ensure_ascii=False, indent=2)

    with (OUTPUT / "index.html").open("w", encoding="utf-8") as fh:
        fh.write(render(snapshot, config))

    print(
        f"OBSERVSTORY_OK repo={REPOSITORY} "
        f"commits={snapshot['summary']['commits']} "
        f"contributors={snapshot['summary']['contributors']} "
        f"overlaps={snapshot['summary']['overlaps']}"
    )


if __name__ == "__main__":
    main()
