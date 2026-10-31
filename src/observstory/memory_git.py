"""Git-side helpers for Project Memory: observe one commit, walk a first-parent lineage, and regenerate a
view without a durable store.

`regenerate_view` is the stateless host: it rebuilds history from Git alone, so every event's
`recorded_at` is the regeneration time (it never claims to have known anything earlier). The durable
NUC store keeps real ingestion times; use this for tests, offline review and public exports."""

from __future__ import annotations

import datetime as dt
import subprocess

from . import knowledge, memory


def _git(repo: str, *args: str) -> str:
    res = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if res.returncode:
        raise knowledge.KnowledgeError(f"git {' '.join(args[:2])}: {res.stderr.strip()}")
    return res.stdout


def first_parent_commits(repo: str, tip: str, since: str | None = None) -> list[str]:
    """Oldest-first first-parent commits reachable from tip (exclusive of `since` and its ancestors)."""
    rng = f"{since}..{tip}" if since else tip
    return _git(repo, "rev-list", "--first-parent", "--reverse", rng).split()


def position(repo: str, commit: str) -> int:
    return int(_git(repo, "rev-list", "--first-parent", "--count", commit).strip())


def commit_time(repo: str, commit: str) -> str:
    return _git(repo, "show", "-s", "--format=%cI", commit).strip()


def is_ancestor(repo: str, older: str, newer: str) -> bool | None:
    res = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", older, newer], capture_output=True)
    return {0: True, 1: False}.get(res.returncode)


def has_manifest(repo: str, commit: str, manifest_path: str = knowledge.DEFAULT_MANIFEST) -> bool:
    return bool(_git(repo, "ls-tree", "--full-tree", commit, "--", manifest_path).strip())


def observe_commit(repo: str, commit: str, repository: str, manifest_path: str = knowledge.DEFAULT_MANIFEST,
                   requested_ref: str | None = None, now: dt.datetime | None = None) -> dict:
    """Artifact + write-back + whole-file texts at one commit, all from Git objects of that commit.
    requested_ref: pass the ref name only when it resolved to `commit` during this read."""
    art = knowledge.build(repo, requested_ref or commit, manifest_path, repository, now=now)
    if art["resolved_commit"] != commit:
        raise knowledge.KnowledgeError(f"{requested_ref} moved: resolved {art['resolved_commit'][:12]}, "
                                       f"expected {commit[:12]}")
    texts = {}
    for s in art["sources"]:
        if s["status"] == "read" and s.get("blob"):
            try:
                texts[s["path"]] = subprocess.run(["git", "-C", repo, "cat-file", "blob", s["blob"]],
                                                  capture_output=True, check=True).stdout.decode("utf-8")
            except (subprocess.CalledProcessError, UnicodeDecodeError):
                pass
    return {"artifact": art, "writeback": memory.read_writeback(repo, commit), "texts": texts}


def regenerate_view(repo: str, ref: str, repository: str, *, manifest_path: str = knowledge.DEFAULT_MANIFEST,
                    now: dt.datetime | None = None, max_commits: int = 500) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    tip = knowledge.resolve(repo, ref)
    commits = first_parent_commits(repo, tip)[-max_commits:]
    snapshots, rvs, lvs, events = [], {}, {}, []
    prev = None
    boundary_done = False
    for c in commits:
        if not has_manifest(repo, c, manifest_path):
            continue
        o = observe_commit(repo, c, repository, manifest_path, requested_ref=ref if c == tip else None, now=now)
        obs = memory.observation(o["artifact"], o["writeback"], o["texts"])
        st = commit_time(repo, c)
        if not boundary_done:
            events.append(memory.coverage_boundary(repository, ref, c, "manifest first present at this commit; "
                                                   "earlier history is unavailable, not empty"))
            boundary_done = True
        for v in obs["records"].values():
            rvs.setdefault(v["version_id"], v)   # first observation keeps its pinned URL and location
        for v in obs["relations"].values():
            lvs.setdefault(v["relation_version_id"], v)
        evs = memory.derive_events(prev, obs, source_time=st)
        events.extend(evs)
        a = o["artifact"]
        snapshots.append({"snapshot_id": a["snapshot_id"], "repository": repository, "requested_ref": ref,
                          "commit": c, "position": position(repo, c), "lineage": 1, "recorded_seq": len(snapshots) + 1,
                          "base_snapshot_id": prev["artifact"]["snapshot_id"] if prev else None,
                          "source_time": st, "recorded_at": stamp, "complete": a["complete"],
                          "manifest_blob": a["source"]["manifest_blob"], "producer": a["producer"],
                          "audience": a["source"].get("audience"), "changed": bool(evs),
                          "diagnostics": a["diagnostics"] + o["writeback"]["diagnostics"]})
        prev = obs
    for i, ev in enumerate(events, 1):
        ev.update(seq=i, recorded_at=stamp, actor=ev.get("actor") or {"name": "observstory.memory_git", "kind": "producer"})
        ev.setdefault("source_time", None)
    return {"schema": memory.VIEW_SCHEMA, "generated_at": stamp,
            "host": {"kind": "git-regeneration", "note": "rebuilt from Git; recorded_at is the regeneration time"},
            "sources": [{"repository": repository, "requested_ref": ref, "cursor_commit": tip,
                         "head_snapshot_id": snapshots[-1]["snapshot_id"] if snapshots else None,
                         "last_sync": {"at": stamp, "outcome": "regenerated"}}],
            "snapshots": snapshots, "record_versions": list(rvs.values()), "relation_versions": list(lvs.values()),
            "events": events, "receipts": [], "indexing": {"state": "not_configured"}}
