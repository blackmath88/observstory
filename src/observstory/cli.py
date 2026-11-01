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
  observstory checkin propose NOTES --label L --at ISO   notes -> PROPOSED items in .observstory/coordination.json
  observstory checkin confirm SESSION --by NAME          PROPOSED -> DECLARED (only a named person can)
  observstory checkin pending                            list items awaiting confirmation
  observstory knowledge build [--repo DIR] [--ref REF] [--out F] [--html F] [--base-ref REF | --base F]
                                          opt-in Project Knowledge artifact from a committed manifest
  observstory knowledge brief|record ID|changes|render [--artifact F]
                                          deterministic queries over that artifact (docs/project-knowledge/USAGE.md)
  observstory memory regenerate --repo DIR --ref REF [--out F]   history view rebuilt from Git (stateless host)
  observstory memory state|history ID|changes A B|context TASK|render|propose [--view F]
                                          Project Memory queries, context packets, UI (docs/project-knowledge/MEMORY.md)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

from . import config as config_mod
from . import coordination as coordination_mod
from . import knowledge as knowledge_mod
from . import query as query_mod
from .derive import derive, parse_time
from .map_compiler import compile_scene
from .map_render import render_map
from .render import render
from .validate import scene_errors, validate


def _write_outputs(out: pathlib.Path, observations: dict | None, snapshot: dict, knowledge_href: str | None = None) -> None:
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
    (out / "index.html").write_text(render_map(scene, knowledge_href=knowledge_href), encoding="utf-8")   # Project Map
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
    coord_path = os.environ.get("OBSERVSTORY_COORDINATION", coordination_mod.DEFAULT_PATH)
    try:
        declared = coordination_mod.load(coord_path)
    except ValueError as exc:
        raise SystemExit(f"::error::observstory coordination: {exc}")
    snap = derive(obs, cfg, now, coordination=declared, coordination_source=coord_path)
    _check(snap)
    out = pathlib.Path(os.environ.get("OBSERVSTORY_OUTPUT", "observstory"))
    knowledge_href = _build_knowledge(out, repository) if os.environ.get("OBSERVSTORY_KNOWLEDGE") else None
    _write_outputs(out, obs, snap, knowledge_href)
    for note in snap["provenance"]["degraded"]:
        print(f"::warning::observstory degraded: {note}")
    print(_summary_line(snap))
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as fh:
            fh.write(markdown_summary(snap))


def _build_knowledge(out: pathlib.Path, repository: str) -> str | None:
    """Opt-in (OBSERVSTORY_KNOWLEDGE=manifest path). Reads Git objects of the built commit in the checkout.
    Any failure is a warning: the Project Map is still written, just without the knowledge link."""
    from .knowledge_render import render_knowledge
    manifest = os.environ["OBSERVSTORY_KNOWLEDGE"]
    repo = os.environ.get("OBSERVSTORY_KNOWLEDGE_REPO", ".")
    ref = os.environ.get("OBSERVSTORY_SHA") or "HEAD"
    try:
        art = knowledge_mod.build(repo, ref, manifest, repository)
        # Read only the event's pinned SHA; retain its stable ref as the tracking
        # scope. Resolving the branch here could race a later push. This label
        # comes from the Action context and does not assert an upstream fetch.
        art["requested_ref"] = os.environ.get("OBSERVSTORY_REF") or ref
    except knowledge_mod.KnowledgeError as exc:
        print(f"::warning::observstory knowledge skipped: {exc}")
        return None
    errors = knowledge_mod.artifact_errors(art)
    if errors:
        print(f"::warning::observstory knowledge skipped, artifact invalid: {'; '.join(errors[:5])}")
        return None
    try:
        base = knowledge_mod.build(repo, f"{art['resolved_commit']}^1", manifest, repository)
        diff = knowledge_mod.changes(base, art)
    except knowledge_mod.KnowledgeError as exc:
        diff = knowledge_mod.changes(None, art, f"first parent of {art['resolved_commit'][:12]} has no usable manifest "
                                                f"or is not in the checkout: {exc}")
    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "knowledge.json").write_text(json.dumps(art, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (data / "knowledge.changes.json").write_text(json.dumps(diff, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "knowledge.html").write_text(render_knowledge(art, diff, map_href="index.html"), encoding="utf-8")
    for d in art["diagnostics"]:
        print(f"::{'error' if d['severity'] == 'error' else 'warning'}::knowledge {d['code']} {d['subject']}: {d['message']}")
    print(f"OBSERVSTORY_KNOWLEDGE_OK snapshot={art['snapshot_id']} commit={art['resolved_commit'][:12]} "
          f"complete={str(art['complete']).lower()} changes={diff['state']}")
    return "knowledge.html"


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
    declared = coordination_mod.load(args.coordination) if args.coordination else None
    if declared is not None:
        declared = coordination_mod.as_of(declared, now)
    snap = derive(obs, cfg, now, coordination=declared, coordination_source=args.coordination or "")
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


def cmd_checkin(args) -> None:
    path = pathlib.Path(args.file)
    data = coordination_mod.load(path) or coordination_mod.empty()
    if args.checkin_cmd == "propose":
        notes = sys.stdin.read() if args.notes == "-" else pathlib.Path(args.notes).read_text(encoding="utf-8")
        sid = coordination_mod.propose(data, notes, args.label, args.at, kind=args.kind)
        mine = [x for k in ("gates", "commitments", "decisions") for x in data[k] if x["source"]["session"] == sid]
        print(f"{sid}: {len(mine)} proposed item(s). Review them, then:  observstory checkin confirm {sid} --by NAME")
    elif args.checkin_cmd == "confirm":
        at = args.at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        split = lambda v: {x.strip() for x in v.split(",") if x.strip()} if v else None  # noqa: E731
        try:
            done = coordination_mod.confirm(data, args.session, args.by, at, only=split(args.only), drop=split(args.drop))
        except ValueError as e:
            raise SystemExit(str(e)) from None
        print(f"declared {len(done)} item(s) from {args.session}: {', '.join(done) or '-'}. Commit {path} to share them.")
    else:
        pending = [x for k in ("gates", "commitments", "decisions") for x in data[k] if x["status"] == "proposed"]
        for x in pending:
            print(f"{x['id']:>4}  {x['source']['session']}  {x.get('label') or x.get('text')}   (line {x['source']['line']})")
        print(f"{len(pending)} proposed item(s) awaiting confirmation")
        return
    errors = coordination_mod.validate(data)
    if errors:
        raise SystemExit("; ".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_json(path: str) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _knowledge_base(args, target: dict):
    """(base artifact or None, reason). A base is a retained artifact file or one regenerated from Git."""
    if args.base:
        if not pathlib.Path(args.base).exists():
            return None, f"base artifact {args.base} not found"
        return _load_json(args.base), ""
    if args.base_ref:
        try:
            return knowledge_mod.build(args.repo, args.base_ref, args.manifest, target["repository"]), ""
        except knowledge_mod.KnowledgeError as exc:
            return None, f"base {args.base_ref!r} could not be generated: {exc}"
    return None, "no base snapshot supplied"


def cmd_knowledge(args) -> None:
    from .knowledge_render import render_knowledge
    k = args.knowledge_cmd
    if k == "build":
        try:
            art = knowledge_mod.build(args.repo, args.ref, args.manifest, args.repository)
        except knowledge_mod.KnowledgeError as exc:
            raise SystemExit(f"::error::observstory knowledge: {exc}") from None
        errors = knowledge_mod.artifact_errors(art)
        if errors:
            raise SystemExit("::error::knowledge artifact validation: " + "; ".join(errors[:10]))
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(art, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        diff = None
        if args.base or args.base_ref:
            base, reason = _knowledge_base(args, art)
            diff = knowledge_mod.changes(base, art, reason)
            out.with_name(out.stem + ".changes.json").write_text(json.dumps(diff, indent=2, ensure_ascii=False) + "\n",
                                                                 encoding="utf-8")
        if args.html:
            pathlib.Path(args.html).write_text(render_knowledge(art, diff, map_href=args.map_href), encoding="utf-8")
        sel = art["selection"]["current_direction"]
        print(f"OBSERVSTORY_KNOWLEDGE_OK snapshot={art['snapshot_id']} commit={art['resolved_commit'][:12]} "
              f"complete={str(art['complete']).lower()} records={len(art['records'])} "
              f"current={sel['record'] or 'unresolved:' + sel['reason']} "
              f"errors={sum(d['severity'] == 'error' for d in art['diagnostics'])}"
              + (f" changes={diff['state']}" if diff else ""))
        return
    if k == "changes":
        if args.target:
            target = _load_json(args.target)
        else:
            try:
                target = knowledge_mod.build(args.repo, args.ref, args.manifest, args.repository)
            except knowledge_mod.KnowledgeError as exc:
                raise SystemExit(f"observstory knowledge: {exc}") from None
        base, reason = _knowledge_base(args, target)
        print(json.dumps(knowledge_mod.changes(base, target, reason), indent=2, ensure_ascii=False))
        return
    art = _load_json(args.artifact)
    if k == "brief":
        print(knowledge_mod.brief_text(art) if args.format == "text"
              else json.dumps(knowledge_mod.brief(art), indent=2, ensure_ascii=False))
    elif k == "record":
        result = knowledge_mod.record(art, args.id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        raise SystemExit(0 if result["answer"]["found"] else 1)
    elif k == "render":
        diff = _load_json(args.changes) if args.changes else None
        pathlib.Path(args.out).write_text(render_knowledge(art, diff, map_href=args.map_href), encoding="utf-8")


def cmd_memory(args) -> None:
    from . import memory as mem
    from . import memory_git
    from .memory_render import render_memory
    m = args.memory_cmd
    out = lambda obj: print(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True))  # noqa: E731
    if m == "regenerate":
        try:
            view = memory_git.regenerate_view(args.repo, args.ref, args.repository or knowledge_mod._repository_from_remote(args.repo) or "local/unknown")
        except knowledge_mod.KnowledgeError as exc:
            raise SystemExit(f"observstory memory: {exc}") from None
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.out).write_text(json.dumps(view, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {args.out}: {len(view['snapshots'])} snapshots, {len(view['events'])} events")
        return
    if m == "propose":
        doc = mem.new_proposal(args.id, args.kind, args.title, args.statement, author=args.author, author_kind=args.author_kind,
                               via=args.via, repository=args.repository_name, base_commit=args.base_commit,
                               packet_id=args.packet_id, evidence=args.evidence, conditions=args.condition,
                               change=args.change)
        errors = mem.proposal_errors(doc)
        if errors:
            raise SystemExit("proposal invalid: " + "; ".join(errors))
        text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(args.out).write_text(text, encoding="utf-8")
            print(f"wrote {args.out}; commit it on a branch and open a pull request for review")
        else:
            sys.stdout.write(text)
        return
    view = _load_json(args.view)
    errors = mem.view_errors(view)
    if errors:
        raise SystemExit("memory view invalid: " + "; ".join(errors[:5]))
    repo = args.repository or (view["sources"][0]["repository"] if view["sources"] else "")
    if m == "state":
        out(mem.state_at(view, repo, snapshot_id=args.snapshot, commit=args.commit, known_at=args.known_at))
    elif m == "history":
        out(mem.record_history(view, repo, args.id))
    elif m == "changes":
        out(mem.changes_between(view, repo, args.base, args.target))
    elif m == "context":
        p = mem.context_packet(view, repo, args.task, snapshot_id=args.snapshot, known_at=args.known_at,
                               include_historical=args.include_historical, limit=args.limit)
        if args.format == "markdown":
            sys.stdout.write(mem.packet_markdown(p))
        else:
            out(p)
    elif m == "render":
        b = mem.ui_bundle(mem.public_view(view) if args.public else view, repo)
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.out).write_text(render_memory(b), encoding="utf-8")
        print(f"wrote {args.out}")


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
    d.add_argument("--coordination", help="declared collaboration state (.observstory/coordination.json)")
    d.add_argument("--out", default="observstory")
    r = sub.add_parser("render")
    r.add_argument("snapshot")
    r.add_argument("--out", default="index.html")
    r.add_argument("--view", choices=["map", "radar"], default="map")
    c = sub.add_parser("checkin", help="check-in notes -> proposed items -> confirmed declarations")
    csub = c.add_subparsers(dest="checkin_cmd", required=True)
    cp = csub.add_parser("propose", help="extract PROPOSED items from notes (a file, or - for stdin)")
    cp.add_argument("notes")
    cp.add_argument("--label", required=True)
    cp.add_argument("--at", required=True, help="when the check-in happened, ISO 8601 with offset")
    cp.add_argument("--kind", default="check-in", choices=["check-in", "kickoff", "review", "other"])
    cc = csub.add_parser("confirm", help="promote a session's PROPOSED items to DECLARED, by a named person")
    cc.add_argument("session")
    cc.add_argument("--by", required=True)
    cc.add_argument("--at", help="confirmation time (default: now)")
    cc.add_argument("--only", help="comma-separated ids to confirm (others stay proposed)")
    cc.add_argument("--drop", help="comma-separated ids to discard")
    csub.add_parser("pending", help="list PROPOSED items awaiting confirmation")
    for x in (cp, cc, csub.choices["pending"]):
        x.add_argument("--file", default=coordination_mod.DEFAULT_PATH)
    q = sub.add_parser("query")
    q.add_argument("name", choices=sorted(query_mod.QUERIES))
    q.add_argument("args", nargs="*")
    q.add_argument("--snapshot", default="observstory/data/snapshot.json")
    k = sub.add_parser("knowledge", help="opt-in Project Knowledge artifact and queries")
    ksub = k.add_subparsers(dest="knowledge_cmd", required=True)
    kb = ksub.add_parser("build", help="resolve one commit, read the manifest and its sources there, write the artifact")
    kc = ksub.add_parser("changes", help="compare two artifacts (or two refs regenerated from Git)")
    for x in (kb, kc):
        x.add_argument("--repo", default=".", help="local Git repository (default: .)")
        x.add_argument("--ref", default="HEAD")
        x.add_argument("--manifest", default=knowledge_mod.DEFAULT_MANIFEST)
        x.add_argument("--repository", help="owner/name for source links (default: from origin)")
        x.add_argument("--base", help="retained base artifact JSON")
        x.add_argument("--base-ref", help="regenerate the base artifact from this ref")
    kb.add_argument("--out", default="observstory/data/knowledge.json")
    kb.add_argument("--html", help="also write the human view here")
    kb.add_argument("--map-href", default=None, help="link from the view back to the Project Map")
    kc.add_argument("--target", help="target artifact JSON (default: build --ref)")
    kbr = ksub.add_parser("brief", help="current direction, decisions, research, open questions, retired material")
    kbr.add_argument("--format", choices=["json", "text"], default="json")
    kr = ksub.add_parser("record", help="one record with its sources and relationships")
    kr.add_argument("id")
    kre = ksub.add_parser("render", help="render the human view from an artifact")
    kre.add_argument("--changes", help="changes JSON to include")
    kre.add_argument("--out", default="observstory/knowledge.html")
    kre.add_argument("--map-href", default=None)
    for x in (kbr, kr, kre):
        x.add_argument("--artifact", default="observstory/data/knowledge.json")
    mm = sub.add_parser("memory", help="Project Memory: history, temporal queries, context packets, UI")
    msub = mm.add_subparsers(dest="memory_cmd", required=True)
    mg = msub.add_parser("regenerate", help="rebuild a memory view from first-parent Git history (recorded_at = now)")
    mg.add_argument("--repo", default=".")
    mg.add_argument("--ref", default="HEAD")
    mg.add_argument("--repository")
    mg.add_argument("--out", default="observstory/data/memory.json")
    ms = msub.add_parser("state", help="state at a revision and/or as known at a time")
    ms.add_argument("--snapshot")
    ms.add_argument("--commit")
    ms.add_argument("--known-at")
    mh = msub.add_parser("history", help="versions and events of one record")
    mh.add_argument("id")
    mc = msub.add_parser("changes", help="recorded changes between two snapshots of one lineage")
    mc.add_argument("base")
    mc.add_argument("target")
    mx = msub.add_parser("context", help="task context packet (JSON or Markdown)")
    mx.add_argument("task")
    mx.add_argument("--snapshot")
    mx.add_argument("--known-at")
    mx.add_argument("--include-historical", action="store_true")
    mx.add_argument("--limit", type=int, default=12)
    mx.add_argument("--format", choices=["json", "markdown"], default="json")
    mr = msub.add_parser("render", help="static Observatory page (Now / History / Graph / Context)")
    mr.add_argument("--out", default="observstory/memory.html")
    mr.add_argument("--public", action="store_true", help="keep only audience=public material")
    for x in (ms, mh, mc, mx, mr):
        x.add_argument("--view", default="observstory/data/memory.json")
        x.add_argument("--repository")
    mp = msub.add_parser("propose", help="write an observstory.proposal/v1 record for review through a pull request")
    mp.add_argument("--id", required=True)
    mp.add_argument("--kind", choices=sorted({"finding", "proposal"}), default="finding")
    mp.add_argument("--title", required=True)
    mp.add_argument("--statement", required=True)
    mp.add_argument("--author", required=True)
    mp.add_argument("--author-kind", choices=["human", "assistant"], required=True)
    mp.add_argument("--via", help="e.g. 'Claude Code on the NUC'")
    mp.add_argument("--repository-name", required=True, help="owner/name")
    mp.add_argument("--base-commit", required=True)
    mp.add_argument("--packet-id", help="context packet the finding was based on")
    mp.add_argument("--evidence", action="append", required=True, help="RECORD[@VERSION] or PATH, repeatable")
    mp.add_argument("--condition", action="append", default=[])
    mp.add_argument("--change", default="none", help="none | set_status:RECORD:STATUS | add_link:FROM:REL:TO")
    mp.add_argument("--out")
    v = sub.add_parser("validate")
    v.add_argument("snapshot")
    args = parser.parse_args(argv)
    handlers = {"build": cmd_build, "derive": cmd_derive, "render": cmd_render, "query": cmd_query, "checkin": cmd_checkin,
                "validate": cmd_validate, "knowledge": cmd_knowledge, "memory": cmd_memory, None: cmd_build}
    handlers[args.cmd](args)

