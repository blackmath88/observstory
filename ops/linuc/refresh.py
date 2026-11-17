#!/usr/bin/env python3
"""Build allowlisted Observstory snapshots on an owned host, without Actions."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


class RefreshError(RuntimeError):
    pass


def command(args: list[str], *, cwd: Path | None = None, env: dict | None = None) -> str:
    child_env = (env or os.environ).copy()
    if Path(args[0]).name == "git":
        # Source repositories are data, not trusted runtime configuration.
        # Do not load operator-global Git filters or prompt for credentials.
        # The API token belongs to the deterministic collector, not Git.
        child_env.pop("OBSERVSTORY_TOKEN", None)
        child_env.update({"GIT_CONFIG_NOSYSTEM": "1",
                          "GIT_CONFIG_GLOBAL": os.devnull,
                          "GIT_TERMINAL_PROMPT": "0",
                          "GIT_LFS_SKIP_SMUDGE": "1"})
    try:
        result = subprocess.run(args, cwd=cwd, env=child_env, text=True, capture_output=True,
                                timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RefreshError(f"{args[0]} could not complete") from exc
    if result.returncode:
        # Git stderr can contain authenticated remote URLs. Never include it in
        # status files, shared logs, or exceptions.
        raise RefreshError(f"{Path(args[0]).name} exited with {result.returncode}")
    return result.stdout.strip()


def slug_for(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name):
        raise RefreshError("repository name must be an owner/repo pair")
    return name.replace("/", "--") + "-" + hashlib.sha256(name.encode()).hexdigest()[:8]


def validate_config(config: dict) -> None:
    if config.get("schema") != "observstory.owned-host/v1":
        raise RefreshError("unsupported host config schema")
    for key in ("state_root", "producer_root"):
        if not isinstance(config.get(key), str) or not Path(config[key]).is_absolute():
            raise RefreshError(f"{key} must be an absolute directory")
    sha = config.get("producer_sha", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RefreshError("producer_sha must pin a full commit")
    repos = config.get("repositories")
    if not isinstance(repos, list) or not repos:
        raise RefreshError("a nonempty repository allowlist is required")
    names = set()
    for repo in repos:
        name = repo.get("name", "")
        slug_for(name)
        if name in names:
            raise RefreshError("duplicate repository enrollment")
        names.add(name)
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", repo.get("branch", "main")):
            raise RefreshError("unsafe branch name")
        source = repo.get("source", "")
        approved = (source == f"git@github.com:{name}.git"
                    or source == f"https://github.com/{name}.git")
        if not approved and not (config.get("allow_local_test_sources") is True
                                 and source.startswith("file://")):
            raise RefreshError(f"unapproved source URL for {name}")
        if repo.get("frontend", "classic") not in ("classic", "observatory"):
            raise RefreshError("frontend must be classic or observatory")


def pinned_source(config: dict) -> Path:
    producer = Path(config["producer_root"]).resolve()
    if command(["git", "-C", str(producer), "rev-parse", "HEAD"]) != config["producer_sha"]:
        raise RefreshError("producer checkout differs from pinned commit")
    if command(["git", "-C", str(producer), "status", "--porcelain"]):
        raise RefreshError("producer checkout has uncommitted changes")
    return producer


def resolve_checkout(root: Path, repo: dict, checkout: Path) -> str:
    name, branch = repo["name"], repo.get("branch", "main")
    cache = root / "git" / (slug_for(name) + ".git")
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        command(["git", "init", "--bare", str(cache)])
        command(["git", "--git-dir", str(cache), "remote", "add", "origin", repo["source"]])
    else:
        actual = command(["git", "--git-dir", str(cache), "remote", "get-url", "origin"])
        if actual != repo["source"]:
            raise RefreshError("cached source URL differs from allowlist")
    ref = "refs/remotes/origin/" + branch
    command(["git", "--git-dir", str(cache), "fetch", "--no-tags", "origin",
             "+refs/heads/" + branch + ":" + ref])
    sha = command(["git", "--git-dir", str(cache), "rev-parse", ref])
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RefreshError("git did not resolve a commit")
    command(["git", "clone", "--shared", "--no-checkout", str(cache), str(checkout)])
    command(["git", "-C", str(checkout), "-c", "core.hooksPath=/dev/null",
             "-c", "filter.lfs.smudge=", "-c", "filter.lfs.required=false",
             "checkout", "--detach", sha])
    if command(["git", "-C", str(checkout), "rev-parse", "HEAD"]) != sha:
        raise RefreshError("checkout revision does not match fetched commit")
    return sha


def build(producer: Path, checkout: Path, target: Path, repo: dict, sha: str) -> dict:
    env = os.environ.copy()
    env.update({
        "OBSERVSTORY_REPOSITORY": repo["name"],
        "OBSERVSTORY_SHA": sha,
        "OBSERVSTORY_REF": "refs/heads/" + repo.get("branch", "main"),
        "OBSERVSTORY_EVENT": "owned-host",
        "OBSERVSTORY_RUN_ID": "",
        "OBSERVSTORY_OUTPUT": str(target),
    })
    if (checkout / "observstory.config.json").is_file():
        env["OBSERVSTORY_CONFIG"] = str(checkout / "observstory.config.json")
    if (checkout / ".observstory/coordination.json").is_file():
        env["OBSERVSTORY_COORDINATION"] = str(checkout / ".observstory/coordination.json")
    if repo.get("knowledge"):
        if not (checkout / ".observstory/knowledge.json").is_file():
            raise RefreshError("enrolled knowledge manifest is missing")
        env["OBSERVSTORY_KNOWLEDGE"] = ".observstory/knowledge.json"
        env["OBSERVSTORY_KNOWLEDGE_REPO"] = str(checkout)
    command([sys.executable, str(producer / "scripts/observstory.py"), "build"],
            cwd=checkout, env=env)
    command([sys.executable, str(producer / "scripts/publish_workspace.py")],
            cwd=checkout, env=env)
    snap_file = target / "data/snapshot.json"
    if not snap_file.is_file() or not (target / "index.html").is_file():
        raise RefreshError("Observstory output incomplete")
    try:
        snapshot = json.loads(snap_file.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise RefreshError("snapshot is not valid JSON") from exc
    if (snapshot.get("schema") != "observstory.snapshot/v1"
            or snapshot.get("repository", {}).get("full_name") != repo["name"]
            or snapshot.get("trigger", {}).get("sha") != sha
            or not isinstance(snapshot.get("provenance", {}).get("degraded"), list)):
        raise RefreshError("snapshot identity or provenance did not validate")
    if repo.get("knowledge"):
        try:
            knowledge = json.loads((target / "data/knowledge.json").read_text())
        except (OSError, ValueError) as exc:
            raise RefreshError("required knowledge output missing") from exc
        if knowledge.get("resolved_commit") != sha or not knowledge.get("complete"):
            raise RefreshError("required knowledge output is incomplete or at wrong commit")
    if repo.get("frontend", "classic") == "observatory":
        release = producer / "frontend/release"
        if not (release / "index.html").is_file() or not (release / "assets").is_dir():
            raise RefreshError("pinned producer has no built Observatory frontend")
        (target / "index.html").rename(target / "map.html")
        shutil.copy2(release / "index.html", target / "index.html")
        shutil.copytree(release / "assets", target / "assets")
    return {"sha": sha, "generated_at": snapshot.get("generated_at"),
            "degraded_coverage": snapshot["provenance"]["degraded"]}


def write_json(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def publish(root: Path, repo: dict, target: Path, info: dict) -> None:
    slug = slug_for(repo["name"])
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    release = root / "releases" / slug / (stamp + "-" + info["sha"][:12])
    release.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(target), str(release))
    write_json(release / "build.json", {"repository": repo["name"], **info})
    public = root / "public"
    public.mkdir(parents=True, exist_ok=True)
    link = public / slug
    tmp_link = public / ("." + slug + ".next")
    if tmp_link.exists() or tmp_link.is_symlink():
        tmp_link.unlink()
    tmp_link.symlink_to(release)
    os.replace(tmp_link, link)


def refresh(config: dict, selected: str | None = None) -> int:
    validate_config(config)
    root = Path(config["state_root"])
    root.mkdir(parents=True, exist_ok=True)
    with (root / "refresh.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RefreshError("another refresh is still running")
        producer = pinned_source(config)
        repos = [r for r in config["repositories"] if selected is None or r["name"] == selected]
        if not repos:
            raise RefreshError("repository is not on the allowlist")
        failures = 0
        for repo in repos:
            name, slug = repo["name"], slug_for(repo["name"])
            attempted = dt.datetime.now(dt.timezone.utc).isoformat()
            try:
                with tempfile.TemporaryDirectory(prefix="observstory-", dir=root) as tmp:
                    checkout, target = Path(tmp) / "checkout", Path(tmp) / "output"
                    sha = resolve_checkout(root, repo, checkout)
                    info = build(producer, checkout, target, repo, sha)
                    publish(root, repo, target, info)
                write_json(root / "status" / (slug + ".json"),
                           {"status": "ok", "repository": name, "last_attempt": attempted, **info})
                print(f"OK {name} {info['sha'][:12]} degraded={len(info['degraded_coverage'])}")
            except (RefreshError, OSError, ValueError) as exc:
                failures += 1
                write_json(root / "status" / (slug + ".json"),
                           {"status": "failed", "repository": name, "last_attempt": attempted,
                            "reason": str(exc)})
                print(f"FAILED {name}: {exc}", file=sys.stderr)
        return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repo", help="one allowlisted owner/repo")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        raise SystemExit(refresh(config, args.repo))
    except (OSError, ValueError, RefreshError) as exc:
        parser.exit(2, f"Observstory host refresh refused: {exc}\n")


if __name__ == "__main__":
    main()
