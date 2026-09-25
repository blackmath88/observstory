"""observstory CLI.

  observstory build                       collect from GitHub (env-driven, used by the Action)
  observstory derive OBS [--config C] [--now ISO] [--out DIR]
                                          offline: observations -> snapshot + dashboard
  observstory render SNAPSHOT [--out F] [--view map|radar]
                                          re-render a view from a snapshot (default: Project Map)
  observstory query NAME [ARGS] [--snapshot F]
                                          agent surface: changes-since ISO | work-near PATH.. |
                                          overlaps [PATH] | open-loops | handoff
  observstory validate SNAPSHOT
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

from . import config as config_mod
from . import query as query_mod
from .derive import derive, parse_time
from .map_compiler import compile_scene
from .map_render import render_map
from .render import render
from .validate import scene_errors, validate


def _write_outputs(out: pathlib.Path, observations: dict | None, snapshot: dict) -> None:
    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    if observations is not None:
        (data / "observations.json").write_text(json.dumps(observations, indent=2, ensure_ascii=False), encoding="utf-8")
    (data / "snapshot.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    scene = compile_scene(snapshot)
    errors = scene_errors(scene)
    if errors:
        for e in errors[:20]:
            print(f"::error::scene validation: {e}", file=sys.stderr)
        raise SystemExit(2)
    (data / "scene.json").write_text(json.dumps(scene, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "index.html").write_text(render_map(scene), encoding="utf-8")   # Project Map (default view)
    (out / "radar.html").write_text(render(snapshot), encoding="utf-8")    # radar (alternative projection)


def _check(snapshot: dict) -> None:
    errors = validate(snapshot)
    if errors:
        for e in errors[:20]:
            print(f"::error::snapshot validation: {e}", file=sys.stderr)
        raise SystemExit(2)


def _summary_line(snap: dict) -> str:
    s = snap["summary"]
    sig = s["signals"]
    return (f"OBSERVSTORY_OK repo={snap['repository']['full_name']} in_flight={s['in_flight']} "
            f"areas_active={s['areas_active']} overlap={sig['overlap']} stale={sig['stale']} "
            f"waiting={sig['waiting']} burst={sig['burst']} degraded={len(snap['provenance']['degraded'])}")


def cmd_build(_args) -> None:
    from .collect import collect
    from .github import Client, GitHubError

    repository = os.environ.get("OBSERVSTORY_REPOSITORY", "")
    if "/" not in repository:
        raise SystemExit("OBSERVSTORY_REPOSITORY must be owner/repo")
    try:
        cfg = config_mod.load(os.environ.get("OBSERVSTORY_CONFIG", "observstory.config.json"))
    except config_mod.ConfigError as exc:
        raise SystemExit(f"::error::observstory config: {exc}")
    now = dt.datetime.now(dt.timezone.utc)
    trigger = {"event": os.environ.get("OBSERVSTORY_EVENT", "manual"), "run_id": os.environ.get("OBSERVSTORY_RUN_ID", ""),
               "sha": os.environ.get("OBSERVSTORY_SHA", "")}
    try:
        client = Client(os.environ.get("OBSERVSTORY_TOKEN", ""),
                        os.environ.get("OBSERVSTORY_API_URL", "https://api.github.com"))
        obs = collect(client, repository, cfg, now, trigger)
    except GitHubError as exc:
        raise SystemExit(f"::error::observstory: {exc}")
    snap = derive(obs, cfg, now)
    _check(snap)
    out = pathlib.Path(os.environ.get("OBSERVSTORY_OUTPUT", "observstory"))
    _write_outputs(out, obs, snap)
    for note in snap["provenance"]["degraded"]:
        print(f"::warning::observstory degraded: {note}")
    print(_summary_line(snap))
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as fh:
            fh.write(markdown_summary(snap))


def markdown_summary(snap: dict) -> str:
    s = snap["summary"]
    lines = [f"### Observstory · {snap['repository']['full_name']}", "",
             f"**{s['in_flight']}** work items in flight across **{s['areas_active']}** areas.", ""]
    if snap["signals"]:
        lines += ["| signal | confidence | basis | summary |", "|---|---|---|---|"]
        lines += [f"| {x['type']} | {x['confidence']} | {x['basis']} | {x['summary']} |" for x in snap["signals"][:15]]
    else:
        lines.append("No coordination signals.")
    return "\n".join(lines) + "\n"


def cmd_derive(args) -> None:
    obs = json.loads(pathlib.Path(args.observations).read_text(encoding="utf-8"))
    cfg = config_mod.load(args.config) if args.config else config_mod.normalise(None)
    now = parse_time(args.now) if args.now else parse_time(obs["fetched_at"])
    snap = derive(obs, cfg, now)
    _check(snap)
    _write_outputs(pathlib.Path(args.out), obs, snap)
    print(_summary_line(snap))


def cmd_render(args) -> None:
    snap = json.loads(pathlib.Path(args.snapshot).read_text(encoding="utf-8"))
    _check(snap)
    page = render(snap) if args.view == "radar" else render_map(compile_scene(snap))
    pathlib.Path(args.out).write_text(page, encoding="utf-8")


def cmd_query(args) -> None:
    snap = json.loads(pathlib.Path(args.snapshot).read_text(encoding="utf-8"))
    fn = query_mod.QUERIES[args.name]
    if args.name == "changes-since":
        if not args.args:
            raise SystemExit("changes-since needs an ISO timestamp")
        result = fn(snap, args.args[0])
    elif args.name == "work-near":
        if not args.args:
            raise SystemExit("work-near needs one or more paths")
        result = fn(snap, args.args)
    elif args.name == "overlaps":
        result = fn(snap, args.args[0] if args.args else None)
    else:
        result = fn(snap)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_validate(args) -> None:
    errors = validate(json.loads(pathlib.Path(args.snapshot).read_text(encoding="utf-8")))
    print("\n".join(errors) if errors else "valid")
    raise SystemExit(1 if errors else 0)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="observstory", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("build")
    d = sub.add_parser("derive")
    d.add_argument("observations")
    d.add_argument("--config")
    d.add_argument("--now")
    d.add_argument("--out", default="observstory")
    r = sub.add_parser("render")
    r.add_argument("snapshot")
    r.add_argument("--out", default="index.html")
    r.add_argument("--view", choices=["map", "radar"], default="map")
    q = sub.add_parser("query")
    q.add_argument("name", choices=sorted(query_mod.QUERIES))
    q.add_argument("args", nargs="*")
    q.add_argument("--snapshot", default="observstory/data/snapshot.json")
    v = sub.add_parser("validate")
    v.add_argument("snapshot")
    args = parser.parse_args(argv)
    handlers = {"build": cmd_build, "derive": cmd_derive, "render": cmd_render, "query": cmd_query,
                "validate": cmd_validate, None: cmd_build}
    handlers[args.cmd](args)
