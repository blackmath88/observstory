"""Project Knowledge: an opt-in, source-owned orientation artifact (observstory.knowledge/v1).

Separate from the metadata-only snapshot (snapshot/v1 is untouched). A repository opts in by committing
a manifest (default .observstory/knowledge.json) that selects existing documents. The producer resolves
one Git commit and reads the manifest and every selected file as Git objects of that commit: no working
tree, no remote, no model. Status is what the manifest/source declares; nothing here approves anything.

Identity is kept apart on purpose:
  logical identity  record id (repository-qualified)       survives edits and renames
  content identity  blob sha + sha256 of the selected text  same bytes -> same hash, on any branch
  membership        snapshot_id = repository + commit + manifest + producer version

Queries (brief, record, changes) all read an artifact, so the HTML view and agents see the same thing.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess

SCHEMA = "observstory.knowledge/v1"
MANIFEST_SCHEMA = "observstory.knowledge-manifest/v1"
PRODUCER = {"name": "observstory.knowledge", "version": "0.1.0"}
DEFAULT_MANIFEST = ".observstory/knowledge.json"
MAX_BYTES = 512 * 1024
EXCERPT_CHARS = 1500

STATUSES = {
    "concept": {"current", "candidate", "superseded", "historical"},
    "decision": {"stated", "proposed", "declared", "superseded"},
    "research": {"reference", "input", "historical"},
    "plan": {"current", "historical"},
    "question": {"open", "resolved"},
    "module": {"optional", "current", "historical"},
}
RELATIONS = {"supersedes", "informs", "qualifies", "applies_to", "plans", "answers"}
NOTE = ("Statuses are declarations by the source repository or its manifest, not verified approval. "
        "Follow each source link (pinned to resolved_commit) before acting. "
        "The producer reads local Git objects; it does not prove the ref matches any remote.")


class KnowledgeError(Exception):
    """The artifact cannot be produced at all (unresolvable ref, missing or unreadable manifest)."""


# ---------------------------------------------------------------- git objects of one commit

def _git(repo: str, *args: str) -> bytes:
    res = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    if res.returncode:
        raise KnowledgeError(f"git {' '.join(args[:2])}: {res.stderr.decode(errors='replace').strip()}")
    return res.stdout


def resolve(repo: str, ref: str) -> str:
    try:
        return _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").decode().strip()
    except KnowledgeError:
        raise KnowledgeError(f"ref_unresolved: {ref!r} does not resolve to a commit in {repo}") from None


def _tree_entries(repo: str, commit: str, paths: list[str]) -> dict[str, tuple[str, str]]:
    """path -> (object type, sha) for paths that exist at commit."""
    if not paths:
        return {}
    out = _git(repo, "ls-tree", "-z", "--full-tree", commit, "--", *paths)
    entries = {}
    for row in out.split(b"\0"):
        if row:
            meta, path = row.split(b"\t", 1)
            _mode, kind, sha = meta.decode().split()
            entries[path.decode()] = (kind, sha)
    return entries


def _repository_from_remote(repo: str) -> str:
    try:
        url = _git(repo, "remote", "get-url", "origin").decode().strip()
    except KnowledgeError:
        return ""
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    return m.group(1) if m else ""


# ---------------------------------------------------------------- text helpers

def _norm(s: str) -> str:
    return " ".join(s.split())


def _headings(lines: list[str]):
    fenced = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        m = None if fenced else re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            yield i, len(m.group(1)), m.group(2)


def _title(lines: list[str], fallback: str) -> str:
    return next((text for _i, level, text in _headings(lines) if level == 1), fallback)


def _section(lines: list[str], name: str):
    """(start, end) 1-based inclusive line range of the heading named `name`, or None."""
    hs = list(_headings(lines))
    for n, (i, level, text) in enumerate(hs):
        if text == name:
            end = next((j for j, lv, _t in hs[n + 1:] if lv <= level), len(lines))
            while end > i + 1 and not lines[end - 1].strip():
                end -= 1
            return i + 1, end
    return None


def _safe_path(p) -> bool:
    return isinstance(p, str) and p and not p.startswith("/") and "\\" not in p and ".." not in p.split("/")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- producer

def build(repo: str, ref: str = "HEAD", manifest_path: str = DEFAULT_MANIFEST, repository: str | None = None,
          now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    commit = resolve(repo, ref)
    repository = repository or _repository_from_remote(repo) or "local/unknown"
    diags: list[dict] = []

    def diag(severity, code, subject, message):
        diags.append({"severity": severity, "code": code, "subject": subject, "message": message})

    def url(path, start=None, end=None):
        if repository == "local/unknown":
            return None
        frag = f"#L{start}-L{end}" if start and end and end != start else (f"#L{start}" if start else "")
        return f"https://github.com/{repository}/blob/{commit}/{path}{frag}"

    if not _safe_path(manifest_path):
        raise KnowledgeError(f"invalid manifest path {manifest_path!r}")
    entry = _tree_entries(repo, commit, [manifest_path]).get(manifest_path)
    if not entry or entry[0] != "blob":
        raise KnowledgeError(f"manifest_missing: {manifest_path} is not present at {commit[:12]} ({ref})")
    manifest_bytes = _git(repo, "cat-file", "blob", entry[1])
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeError(f"manifest_invalid: {manifest_path}: {exc}") from None
    if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA:
        raise KnowledgeError(f"manifest_invalid: schema must be {MANIFEST_SCHEMA!r}")

    raw_records = manifest.get("records") if isinstance(manifest.get("records"), list) else []
    raw_links = manifest.get("links") if isinstance(manifest.get("links"), list) else []
    imports = manifest.get("imports") if isinstance(manifest.get("imports"), list) else []

    # Every path the manifest names, read once from the same commit.
    wanted = []
    for r in raw_records:
        if isinstance(r, dict):
            wanted.append(r.get("path"))
            wanted += [d.get("path") for d in r.get("declared_in") or [] if isinstance(d, dict)]
    for link in raw_links:
        if isinstance(link, dict):
            wanted += [d.get("path") for d in link.get("declared_in") or [] if isinstance(d, dict)]
    wanted += [i.get("path") for i in imports if isinstance(i, dict)]
    paths, seen = [], set()
    for p in wanted:
        if p in seen:
            continue
        seen.add(p)
        if _safe_path(p):
            paths.append(p)
        else:
            diag("error", "invalid_path", str(p), "paths must be repository-relative without '..'")
    entries = _tree_entries(repo, commit, paths)
    texts: dict[str, str] = {}
    sources = []
    for p in paths:
        kind, sha = entries.get(p, (None, None))
        status, size = "read", None
        if kind != "blob":
            status = "missing"
            diag("error", "source_missing_at_commit", p,
                 f"not present at {commit[:12]}; this is not evidence of deletion, only that it could not be read")
        else:
            data = _git(repo, "cat-file", "blob", sha)
            size = len(data)
            if size > MAX_BYTES:
                status = "too_large"
                diag("error", "source_too_large", p, f"{size} bytes exceeds {MAX_BYTES}")
            else:
                try:
                    texts[p] = data.decode("utf-8")
                except UnicodeDecodeError:
                    status = "not_utf8"
                    diag("error", "source_not_utf8", p, "selected sources must be UTF-8 text")
        sources.append({"path": p, "blob": sha, "size": size, "status": status})
    blobs = {s["path"]: s["blob"] for s in sources}

    def declarations(items, subject):
        out = []
        for d in items or []:
            if not isinstance(d, dict) or not isinstance(d.get("quote"), str) or not d.get("path"):
                diag("error", "invalid_declaration", subject, "declared_in entries need path and quote")
                continue
            text = texts.get(d["path"])
            found, line = None, None
            if text is not None:
                q = _norm(d["quote"])
                found = q in _norm(text)
                line = next((i + 1 for i, ln in enumerate(text.splitlines()) if q in _norm(ln)), None) if found else None
                if not found:
                    diag("warning", "declaration_not_found", subject,
                         f"quoted declaration not found in {d['path']} at this commit")
            out.append({"path": d["path"], "quote": d["quote"], "found": found, "line": line,
                        "url": url(d["path"], line) if found else url(d["path"])})
        return out

    def basis(decls, fallback):
        if any(d["found"] for d in decls):
            return {"kind": "source_declared", "declarations": decls}
        return {"kind": fallback, "declarations": decls}

    records: list[dict] = []
    ids: set[str] = set()

    def add(rec):
        if rec["id"] in ids:
            diag("error", "duplicate_id", rec["id"], "record id appears more than once; later occurrence ignored")
            return
        ids.add(rec["id"])
        records.append(rec)

    for n, r in enumerate(raw_records):
        if not isinstance(r, dict) or not isinstance(r.get("id"), str) or not r["id"]:
            diag("error", "invalid_record", f"records[{n}]", "a record needs a string id")
            continue
        rid, rtype, status = r["id"], r.get("type"), r.get("status")
        if rtype not in STATUSES:
            diag("error", "invalid_type", rid, f"type {rtype!r} not in {sorted(STATUSES)}")
        elif status not in STATUSES[rtype]:
            diag("error", "invalid_status", rid, f"status {status!r} not allowed for {rtype}: {sorted(STATUSES[rtype])}")
        if rtype == "decision" and status == "declared":
            diag("error", "confirmation_required", rid,
                 "'declared' decisions come from a confirmed coordination record; the manifest cannot approve")
        path = r.get("path")
        text = texts.get(path) if _safe_path(path) else None
        rec = {"id": rid, "logical_id": f"{repository}#{rid}", "type": rtype, "status": status,
               "origin": "manifest", "title": None, "path": path, "section": r.get("section"),
               "location": None, "blob": blobs.get(path), "content_sha256": None, "excerpt": None,
               "excerpt_truncated": False, "url": None, "readable": text is not None,
               "basis": basis(declarations(r.get("declared_in"), rid), "manifest_classification"),
               "note": r.get("note")}
        if text is not None:
            lines = text.splitlines()
            rec["title"] = _title(lines, path)
            selected = text
            if rec["section"]:
                span = _section(lines, rec["section"])
                if span is None:
                    diag("error", "section_not_found", rid, f"heading {rec['section']!r} not found in {path}")
                    rec["readable"] = False
                    selected = None
                else:
                    rec["location"] = {"start_line": span[0], "end_line": span[1]}
                    selected = "\n".join(lines[span[0] - 1:span[1]])
                    rec["excerpt"] = selected[:EXCERPT_CHARS]
                    rec["excerpt_truncated"] = len(selected) > EXCERPT_CHARS
                    rec["title"] = f"{rec['title']} › {rec['section']}"
            if selected is not None:
                rec["content_sha256"] = _sha256(selected)
                loc = rec["location"] or {}
                rec["url"] = url(path, loc.get("start_line"), loc.get("end_line"))
        add(rec)

    for imp in imports:
        if not isinstance(imp, dict) or imp.get("adapter") != "observstory.coordination/v1":
            diag("error", "unknown_adapter", str(imp.get("adapter") if isinstance(imp, dict) else imp),
                 "only observstory.coordination/v1 is supported")
            continue
        for rec in _import_coordination(imp, texts, blobs, repository, url, diag):
            add(rec)

    by_id = {r["id"]: r for r in records}
    relationships = []
    for n, link in enumerate(raw_links):
        if not isinstance(link, dict):
            diag("error", "invalid_link", f"links[{n}]", "a link must be an object")
            continue
        subject = f"{link.get('from')} {link.get('rel')} {link.get('to')}"
        if link.get("rel") not in RELATIONS:
            diag("error", "invalid_relation", subject, f"rel must be one of {sorted(RELATIONS)}")
        dangling = [x for x in (link.get("from"), link.get("to")) if x not in by_id]
        for x in dangling:
            diag("error", "dangling_link", subject, f"unknown record {x!r}")
        relationships.append({"from": link.get("from"), "rel": link.get("rel"), "to": link.get("to"),
                              "resolved": not dangling,
                              "basis": basis(declarations(link.get("declared_in"), subject), "manifest_declared")})

    supersedes = [(x["from"], x["to"]) for x in relationships if x["rel"] == "supersedes" and x["resolved"]]
    for cycle in _cycles(supersedes):
        diag("error", "supersession_cycle", " -> ".join(cycle), "records supersede each other; none can be current")
    for older in {to for _f, to in supersedes}:
        if by_id[older]["status"] == "current":
            diag("error", "superseded_but_current", older, "declared current but superseded by another record")

    selection = _select(records, diags)
    read_failed = [s["path"] for s in sources if s["status"] != "read"]
    complete = not read_failed and not any(d["code"] in ("invalid_record", "unknown_adapter") for d in diags)
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    snapshot_id = "ks_" + hashlib.sha256(json.dumps(
        [SCHEMA, PRODUCER["version"], repository, commit, manifest_path, manifest_sha]).encode()).hexdigest()[:20]
    stamp = now.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA, "producer": dict(PRODUCER), "snapshot_id": snapshot_id,
        "repository": repository, "requested_ref": ref, "resolved_commit": commit,
        "title": manifest.get("title") or repository,
        "source": {"method": "git-objects-at-resolved-commit", "manifest_path": manifest_path,
                   "manifest_blob": entry[1], "manifest_sha256": manifest_sha,
                   "selection_policy": manifest.get("selection_policy"), "audience": manifest.get("audience"),
                   "note": manifest.get("note"),
                   "upstream_check": "not_performed: the ref was resolved in the local repository only"},
        "generated_at": stamp, "complete": complete,
        "completeness": {"selected_sources": len(paths), "read": len(paths) - len(read_failed), "failed": read_failed},
        "records": records, "relationships": relationships, "selection": selection,
        "sources": sources, "diagnostics": diags,
    }


def _import_coordination(imp, texts, blobs, repository, url, diag):
    path, include = imp.get("path"), set(imp.get("include") or ["decisions", "open_questions"])
    text = texts.get(path)
    if text is None:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        diag("error", "import_invalid", path, f"not JSON: {exc}")
        return []
    if data.get("schema") != "observstory.coordination/v1":
        diag("error", "import_invalid", path, "expected schema observstory.coordination/v1")
        return []
    lines = text.splitlines()

    def line_of(needle):
        return next((i + 1 for i, ln in enumerate(lines) if needle in ln), None)

    def rec(rid, rtype, status, title, line, basis_kind, extra):
        r = {"id": f"coordination:{rid}", "logical_id": f"{repository}#coordination:{rid}", "type": rtype,
             "status": status, "origin": "import:observstory.coordination/v1", "title": title, "path": path,
             "section": None, "location": {"start_line": line, "end_line": line} if line else None,
             "blob": blobs.get(path), "content_sha256": _sha256(json.dumps(extra["item"], sort_keys=True)),
             "excerpt": None, "excerpt_truncated": False, "url": url(path, line), "readable": True,
             "basis": {"kind": basis_kind, "declarations": []}, "note": extra.get("note")}
        r.update({k: v for k, v in extra.items() if k not in ("item", "note")})
        return r

    out = []
    if "decisions" in include:
        for d in data.get("decisions", []):
            status = d.get("status") if d.get("status") in STATUSES["decision"] else None
            if status is None:
                diag("error", "invalid_status", f"coordination:{d.get('id')}", f"unknown status {d.get('status')!r}")
            confirmed = status == "declared" and d.get("confirmed_by")
            out.append(rec(d.get("id"), "decision", status, d.get("text"),
                           line_of(f'"id": "{d.get("id")}"'), "coordination_confirmed" if confirmed else "coordination_recorded",
                           {"item": d, "confirmed_by": d.get("confirmed_by"), "confirmed_at": d.get("confirmed_at"),
                            "note": "confirmed_by is the recorded claim in coordination.json; no review event was verified."
                            if confirmed else None}))
    if "open_questions" in include:
        for s in data.get("sessions", []):
            for n, q in enumerate(s.get("open_questions") or [], 1):
                out.append(rec(f"{s.get('id')}.Q{n}", "question", "open", q, line_of(json.dumps(q, ensure_ascii=False)[1:-1]),
                               "coordination_recorded", {"item": {"session": s.get("id"), "question": q},
                                                         "session": s.get("id")}))
    return out


def _cycles(edges):
    graph: dict[str, list[str]] = {}
    for a, b in edges:
        graph.setdefault(a, []).append(b)
    found, seen = [], set()

    def visit(node, stack):
        if node in stack:
            cyc = stack[stack.index(node):] + [node]
            key = frozenset(cyc)
            if key not in seen:
                seen.add(key)
                found.append(cyc)
            return
        for nxt in graph.get(node, []):
            visit(nxt, stack + [node])

    for start in sorted(graph):
        visit(start, [])
    return found


def _select(records, diags):
    """Current direction = the one concept declared current, with a verified source declaration.
    Anything else is unresolved. Timestamps and file order never break a tie."""
    candidates = [r for r in records if r["type"] == "concept" and r["status"] == "current"]
    blocked = {d["subject"] for d in diags if d["code"] in ("superseded_but_current",)}
    cyclic = any(d["code"] == "supersession_cycle" for d in diags)
    ids = [r["id"] for r in candidates]
    if not candidates:
        return {"current_direction": {"state": "unresolved", "reason": "no_current_declaration", "record": None, "candidates": []}}
    if len(candidates) > 1:
        return {"current_direction": {"state": "unresolved", "reason": "conflicting_declarations", "record": None, "candidates": ids}}
    only = candidates[0]
    reason = ("supersession_cycle" if cyclic else "superseded_but_current" if only["id"] in blocked
              else "source_unreadable" if not only["readable"]
              else "declaration_unverified" if only["basis"]["kind"] != "source_declared" else None)
    if reason:
        return {"current_direction": {"state": "unresolved", "reason": reason, "record": None, "candidates": ids}}
    return {"current_direction": {"state": "selected", "reason": "single_verified_declaration", "record": only["id"], "candidates": ids}}


def artifact_errors(a: dict) -> list[str]:
    from .validate import SCHEMA_PATH, _check
    schema = json.loads(SCHEMA_PATH.with_name("knowledge-v1.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    _check(a, schema, schema, "$", errors)
    return errors


# ---------------------------------------------------------------- queries

def receipt(a: dict) -> dict:
    return {"repository": a["repository"], "requested_ref": a["requested_ref"], "resolved_commit": a["resolved_commit"],
            "snapshot_id": a["snapshot_id"], "complete": a["complete"], "generated_at": a["generated_at"],
            "producer_version": a["producer"]["version"], "selection_policy": a["source"]["selection_policy"],
            "upstream_check": a["source"]["upstream_check"]}


def _brief_record(r: dict) -> dict:
    return {k: r.get(k) for k in ("id", "type", "status", "title", "path", "location", "url", "blob", "basis", "note",
                                   "confirmed_by", "excerpt") if r.get(k) is not None or k in ("id", "status")}


def _envelope(a, name, args, answer):
    return {"query": name, "args": args, "snapshot": receipt(a), "answer": answer,
            "diagnostics": a["diagnostics"], "evidence_note": NOTE}


def brief(a: dict) -> dict:
    """What is the current direction, what applies, what is open, what is retired?"""
    recs = a["records"]
    by_id = {r["id"]: r for r in recs}
    sel = a["selection"]["current_direction"]
    pick = lambda pred: [_brief_record(r) for r in recs if pred(r)]  # noqa: E731
    return _envelope(a, "knowledge-brief", {}, {
        "title": a["title"],
        "current_direction": {**sel, "record": _brief_record(by_id[sel["record"]]) if sel["record"] else None},
        "decisions": pick(lambda r: r["type"] == "decision" and r["status"] != "superseded"),
        "plans": pick(lambda r: r["type"] == "plan" and r["status"] == "current"),
        "research": pick(lambda r: r["type"] in ("research", "module") and r["status"] != "historical"),
        "open_questions": pick(lambda r: r["type"] == "question" and r["status"] == "open"),
        "retired": pick(lambda r: r["status"] in ("superseded", "historical")),
        "relationships": a["relationships"],
    })


def record(a: dict, rid: str) -> dict:
    by_id = {r["id"]: r for r in a["records"]}
    r = by_id.get(rid)
    if r is None:
        return _envelope(a, "knowledge-record", {"id": rid}, {"found": False, "known_ids": sorted(by_id)})
    return _envelope(a, "knowledge-record", {"id": rid}, {
        "found": True, "record": r,
        "outgoing": [x for x in a["relationships"] if x["from"] == rid],
        "incoming": [x for x in a["relationships"] if x["to"] == rid],
        "source": next((s for s in a["sources"] if s["path"] == r["path"]), None),
    })


def history_unavailable(target: dict | None, reason: str) -> dict:
    return {"query": "knowledge-changes", "state": "history_unavailable", "reason": reason,
            "base": None, "target": receipt(target) if target else None,
            "evidence_note": "No base snapshot: this says nothing about whether anything changed."}


def changes(base: dict | None, target: dict, base_reason: str = "no base snapshot supplied") -> dict:
    """Differences between two artifacts, by logical record id. Never infers ancestry from SHAs or times."""
    if base is None:
        return history_unavailable(target, base_reason)
    if base["repository"] != target["repository"]:
        return {"query": "knowledge-changes", "state": "incomparable", "reason": "different repositories",
                "base": receipt(base), "target": receipt(target)}
    b = {r["id"]: r for r in base["records"]}
    t = {r["id"]: r for r in target["records"]}
    out = {"added": [], "removed": [], "removal_unconfirmed": [], "content_changed": [], "status_changed": [],
           "unreadable_in_target": [], "unchanged": 0}
    for rid, r in t.items():
        if rid not in b:
            out["added"].append({"id": rid, "type": r["type"], "status": r["status"], "url": r["url"]})
            continue
        old = b[rid]
        if not r["readable"] and old["readable"]:
            out["unreadable_in_target"].append({"id": rid, "path": r["path"]})
            continue
        changed = False
        if old["status"] != r["status"]:
            out["status_changed"].append({"id": rid, "from": old["status"], "to": r["status"]})
            changed = True
        if old["content_sha256"] != r["content_sha256"] or old["path"] != r["path"]:
            out["content_changed"].append({"id": rid, "from_sha256": old["content_sha256"], "to_sha256": r["content_sha256"],
                                           "from_path": old["path"], "to_path": r["path"],
                                           "from_url": old["url"], "to_url": r["url"]})
            changed = True
        out["unchanged"] += not changed
    for rid, old in b.items():
        if rid not in t:
            # Only a complete target snapshot can establish that a record is gone.
            key = "removed" if target["complete"] else "removal_unconfirmed"
            out[key].append({"id": rid, "type": old["type"], "status": old["status"], "last_url": old["url"]})
    edge = lambda x: (x["from"], x["rel"], x["to"])  # noqa: E731
    be, te = {edge(x) for x in base["relationships"]}, {edge(x) for x in target["relationships"]}
    bs, ts = base["selection"]["current_direction"], target["selection"]["current_direction"]
    return {"query": "knowledge-changes", "state": "compared", "base": receipt(base), "target": receipt(target),
            "same_requested_ref": base["requested_ref"] == target["requested_ref"],
            "ancestry": "not_inferred",
            "selection": {"from": bs, "to": ts, "changed": (bs["state"], bs["record"]) != (ts["state"], ts["record"])},
            "records": out,
            "relationships": {"added": [list(e) for e in sorted(te - be)], "removed": [list(e) for e in sorted(be - te)]},
            "evidence_note": "Compared by logical record id and content hash. Removals require a complete target snapshot."}


def brief_text(a: dict) -> str:
    """Concise readable form of brief(), for terminals and agent prompts."""
    ans, s = brief(a)["answer"], receipt(a)
    lines = [f"{ans['title']}", f"{s['repository']} @ {s['requested_ref']} = {s['resolved_commit'][:12]} · "
             f"snapshot {s['snapshot_id']} · {'complete' if s['complete'] else 'INCOMPLETE'}", ""]
    cd = ans["current_direction"]
    if cd["state"] == "selected":
        r = cd["record"]
        decl = next((d for d in r["basis"]["declarations"] if d["found"]), None)
        lines.append(f"CURRENT DIRECTION: {r['title']} ({r['path']})")
        if decl:
            lines.append(f"  basis: {decl['path']}:{decl['line']} “{decl['quote']}”")
    else:
        lines.append(f"CURRENT DIRECTION: unresolved ({cd['reason']}) candidates={cd['candidates']}")
    for label, key in (("DECISIONS", "decisions"), ("PLANS", "plans"), ("RESEARCH", "research"),
                       ("OPEN QUESTIONS", "open_questions"), ("RETIRED", "retired")):
        lines += ["", f"{label}:"]
        for r in ans[key] or []:
            where = f"{r.get('path')}" + (f":{r['location']['start_line']}" if r.get("location") else "")
            lines.append(f"  [{r['status']}] {r['id']}: {r.get('title') or ''} ({where})")
        if not ans[key]:
            lines.append("  (none declared)")
    errs = [d for d in a["diagnostics"] if d["severity"] == "error"]
    warns = [d for d in a["diagnostics"] if d["severity"] != "error"]
    lines += ["", f"DIAGNOSTICS: {len(errs)} error(s), {len(warns)} warning(s)"]
    lines += [f"  {d['severity']}: {d['code']} {d['subject']}: {d['message']}" for d in a["diagnostics"]]
    return "\n".join(lines)
