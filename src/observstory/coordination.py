"""Declared collaboration state (issue #7, ADR-027..030).

Three steps, kept apart on purpose:
  extract    notes -> PROPOSED items (deterministic markers; an LLM adapter could plug in, still proposing)
  confirm    PROPOSED -> DECLARED, recording who confirmed and when (only a named person can do this)
  reconcile  DECLARED items x observed repository state -> commitment states and cues (pure, deterministic)

Declared state lives in the observed repository at .observstory/coordination.json.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re

SCHEMA = "observstory.coordination/v1"
DEFAULT_PATH = ".observstory/coordination.json"
SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[2] / "schema" / "coordination-v1.json"


def empty() -> dict:
    return {"schema": SCHEMA, "sessions": [], "gates": [], "commitments": [], "decisions": []}


def _t(value: str | None) -> dt.datetime | None:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _iso(value: dt.datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: str | pathlib.Path | None) -> dict | None:
    """The declared state, or None when the repository has none (zero-config: no rail)."""
    if not path:
        return None
    p = pathlib.Path(path)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        raise ValueError(f"{p}: " + "; ".join(errors[:5]))
    return data


def validate(data: dict) -> list[str]:
    from .validate import _check  # the same stdlib validator as the snapshot (ADR-008)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    _check(data, schema, schema, "$", errors)
    ids = [x["id"] for k in ("sessions", "gates", "commitments", "decisions") for x in data.get(k, [])]
    if len(ids) != len(set(ids)):
        errors.append("ids must be unique across sessions, gates, commitments and decisions")
    for k in ("gates", "commitments", "decisions"):
        for x in data.get(k, []):
            if x.get("status") == "declared" and not x.get("confirmed_by"):
                errors.append(f"{x['id']}: declared without confirmed_by")
    return errors


# ---------------------------------------------------------------- extraction (proposes only)

TIME = r"(?:(mon|tue|wed|thu|fri|sat|sun)\w*\s+)?(\d{1,2}):(\d{2})"   # "14:00" or "Sat 14:00"
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MARKERS = [
    # FREEZE web/, src/ at 23:00   |   GATE submission at 12:00   |   DEMO at 14:00
    ("gate", re.compile(rf"^(?P<kind>FREEZE|GATE|SUBMISSION|DEMO|CHECKPOINT)\b(?P<rest>.*?)\bat\s+{TIME}\s*$", re.I)),
    # DECISION: keep SQLite until the demo [src/store/]
    ("decision", re.compile(r"^DECISION:\s*(?P<text>.+?)\s*(\[(?P<areas>[^\]]+)\])?\s*$", re.I)),
    # @Sofia: eval harness for memory (by 14:00) [evals/, #44]
    ("commitment", re.compile(rf"^@(?P<owner>[\w.-]+):?\s*(?P<text>.+?)\s*(\(by\s+{TIME}\))?\s*(\[(?P<links>[^\]]+)\])?\s*$", re.I)),
    # ? is the search API stable
    ("question", re.compile(r"^(\?|QUESTION:)\s*(?P<text>.+)$", re.I)),
]


def _clock(session_at: dt.datetime, day: str | None, hh: str, mm: str) -> str:
    """A clock time after the session: on the named weekday if given, else the next occurrence of that time."""
    t = session_at.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if day:
        t += dt.timedelta(days=(DAYS.index(day.lower()[:3]) - t.weekday()) % 7)
        return _iso(t if t >= session_at else t + dt.timedelta(days=7))
    return _iso(t if t >= session_at else t + dt.timedelta(days=1))


def _link(token: str) -> dict:
    token = token.strip()
    if re.fullmatch(r"#?\d+", token):
        return {"kind": "pr", "ref": token.lstrip("#")}
    if token.startswith(("http://", "https://")):
        return {"kind": "url", "ref": token}
    if token.startswith("branch:"):
        return {"kind": "branch", "ref": token[7:]}
    return {"kind": "path", "ref": token}


def extract(notes: str, session_id: str, session_at: str) -> dict:
    """Deterministic extractor: explicit markers only, one item per line. Everything is PROPOSED."""
    at = _t(session_at)
    out = {"gates": [], "commitments": [], "decisions": [], "open_questions": []}
    for n, raw in enumerate(notes.splitlines(), 1):
        line = raw.strip().lstrip("-*• ").strip()
        if not line:
            continue
        for kind, rx in MARKERS:
            m = rx.match(line)
            if not m:
                continue
            source = {"session": session_id, "extractor": "markers/v1", "line": n, "excerpt": raw.strip()[:200]}
            if kind == "gate":
                word = m.group("kind").lower()
                gkind = {"gate": "checkpoint", "submission": "submission", "demo": "demo",
                         "freeze": "freeze", "checkpoint": "checkpoint"}[word]
                rest = m.group("rest").strip()
                # freeze scope: the path-like tokens (web/, src/core, schema.json); none means the whole repository
                areas = [a for a in re.split(r"[,\s]+", rest) if a and ("/" in a or "." in a)] if gkind == "freeze" else []
                label = {"freeze": "Freeze" + (" " + ", ".join(areas) if areas else ""),
                         "submission": "Submission", "demo": "Demo"}.get(gkind, rest or "Checkpoint")
                if gkind == "checkpoint" and rest:
                    label = rest
                out["gates"].append({"kind": gkind, "label": label, "at": _clock(at, m.group(3), m.group(4), m.group(5)),
                                     "areas": areas, "source": source})
            elif kind == "decision":
                areas = [a.strip() for a in (m.group("areas") or "").split(",") if a.strip()]
                out["decisions"].append({"text": m.group("text"), "areas": areas, "source": source})
            elif kind == "commitment":
                g = m.groups()
                due = _clock(at, g[3], g[4], g[5]) if g[4] else None
                links = [_link(x) for x in (m.group("links") or "").split(",") if x.strip()]
                out["commitments"].append({"text": m.group("text"), "owner": m.group("owner"), "due": due,
                                           "links": links, "source": source})
            else:
                out["open_questions"].append(m.group("text"))
            break
    return out


def _next_id(data: dict, prefix: str, key: str) -> str:
    used = {x["id"] for x in data[key]}
    n = 1
    while f"{prefix}{n}" in used:
        n += 1
    return f"{prefix}{n}"


def propose(data: dict, notes: str, label: str, at: str, kind: str = "check-in") -> str:
    """Add a session and its PROPOSED items. Returns the session id."""
    sid = _next_id(data, "S", "sessions")
    items = extract(notes, sid, at)
    data["sessions"].append({"id": sid, "kind": kind, "label": label, "at": at, "recorded": False,
                             "open_questions": items["open_questions"]})
    for key, prefix in (("gates", "G"), ("commitments", "C"), ("decisions", "D")):
        for item in items[key]:
            data[key].append({"id": _next_id(data, prefix, key), "status": "proposed",
                              "confirmed_by": None, "confirmed_at": None, **item})
    return sid


def confirm(data: dict, session_id: str, by: str, at: str, only: set | None = None, drop: set | None = None) -> list[str]:
    """PROPOSED -> DECLARED for one session, by a named person. Dropped items are removed. Returns confirmed ids."""
    if not by or not by.strip():
        raise ValueError("confirmation needs a person's name (--by)")
    confirmed = []
    for key in ("gates", "commitments", "decisions"):
        kept = []
        for x in data[key]:
            mine = x.get("source", {}).get("session") == session_id and x["status"] == "proposed"
            if mine and drop and x["id"] in drop:
                continue
            if mine and (only is None or x["id"] in only):
                x.update(status="declared", confirmed_by=by.strip(), confirmed_at=at)
                confirmed.append(x["id"])
            kept.append(x)
        data[key] = kept
    return confirmed


# ---------------------------------------------------------------- reconciliation (declared x observed)

def _under(path: str, prefix: str) -> bool:
    p = prefix.rstrip("/")
    return path == p or path.startswith(p + "/")


def _matches(link: dict, w: dict) -> bool:
    if link["kind"] == "pr":
        return w["kind"] == "pull_request" and str(w.get("number")) == link["ref"]
    if link["kind"] == "branch":
        return w.get("head") == link["ref"] and w["kind"] in ("branch", "pull_request")
    if link["kind"] == "path":
        return any(_under(p, link["ref"]) for p in w["paths"])
    return False


def _name(w: dict) -> str:
    """How a cue names observed work: by the work, not by the person (Develop finding F2)."""
    if w["kind"] == "pull_request":
        return f"#{w['number']}"
    if w["kind"] == "branch":
        return f"branch {w['head']}"
    return "a direct push"


def as_of(data: dict, now: dt.datetime) -> dict:
    """The declarations as they existed at `now`: sessions after `now` (and their items) didn't exist yet."""
    keep = {s["id"] for s in data["sessions"] if _t(s["at"]) <= now}
    out = {"schema": data["schema"], "sessions": [s for s in data["sessions"] if s["id"] in keep]}
    for k in ("gates", "commitments", "decisions"):
        out[k] = [x for x in data[k] if x.get("source", {}).get("session") in keep
                  and (x["status"] == "proposed" or not x.get("confirmed_at") or _t(x["confirmed_at"]) <= now)]
    return out


def reconcile(data: dict, work_items: list[dict], commit_rows: list[dict], now: dt.datetime, source: str) -> dict:
    """Pure. work_items still carry `_commits` (derive calls this before stripping them)."""
    sessions = {s["id"]: s for s in data["sessions"]}
    declared = {k: [x for x in data[k] if x["status"] == "declared"] for k in ("gates", "commitments", "decisions")}
    pending = sum(1 for k in ("gates", "commitments", "decisions") for x in data[k] if x["status"] == "proposed")
    items = {w["id"]: w for w in work_items}
    cues = []

    def since(x):
        s = sessions.get(x.get("source", {}).get("session"))
        return _t(s["at"]) if s else _t(x.get("confirmed_at"))

    # gates: passed / next
    gates = sorted(declared["gates"], key=lambda g: g["at"])
    upcoming = [g for g in gates if _t(g["at"]) > now]
    gate_rows = [dict(g, passed=_t(g["at"]) <= now, next=bool(upcoming) and g["id"] == upcoming[0]["id"]) for g in gates]

    # commitments: observed state from linked work (C-linked / C-unlinked)
    commitment_rows = []
    for c in declared["commitments"]:
        start = since(c) or now
        observable = [l for l in c["links"] if l["kind"] != "url"]
        matched = []
        for w in work_items:
            by_ref = any(_matches(l, w) for l in observable if l["kind"] in ("pr", "branch"))
            by_path = any(_matches(l, w) for l in observable if l["kind"] == "path")
            last = _t(w["last_activity_at"])
            # a PR or branch link is explicit; a path link only counts work since the commitment was made
            if by_ref or (by_path and last is not None and last >= start):
                matched.append(w["id"])
        if not c["links"]:
            state = "unlinked"
        elif not observable:
            state = "tracked_elsewhere"
        elif any(items[m]["in_flight"] for m in matched):
            state = "in_progress"
        elif any(items[m]["state"] in ("merged", "pushed") for m in matched):
            state = "landed"
        elif matched:
            state = "closed"
        else:
            state = "not_started"
        row = dict(c, state=state, matched=sorted(matched), cue=None)
        due = _t(c.get("due"))
        if state == "not_started" and due:
            half = start + (due - start) / 2
            if now >= due or now >= half:
                overdue = now >= due
                cue = {"id": f"commitment:{c['id']}", "rule": "commitment.unstarted",
                       "subject": {"kind": "commitment", "id": c["id"]}, "confidence": "high",
                       "summary": f"\"{c['text']}\" " + ("was due " if overdue else "is due ") + c["due"][11:16]
                                  + ": no linked work yet",
                       "declared": {"text": c["text"], "owner": c.get("owner"), "due": c["due"],
                                    "links": c["links"], "session": c.get("source", {}).get("session"),
                                    "confirmed_by": c["confirmed_by"]},
                       "observed": {"work_items": [], "detail": "no open, landed or recent work matches "
                                    + ", ".join(f"{l['kind']} {l['ref']}" for l in observable)}}
                cues.append(cue)
                row["cue"] = cue["id"]
        commitment_rows.append(row)

    # G-freeze: frozen areas that changed after the freeze
    commit_by_item: dict[str, list] = {}
    for c in commit_rows:
        commit_by_item.setdefault(c["work_item"], []).append(c)
    for g in gate_rows:
        if g["kind"] != "freeze" or not g["passed"]:
            continue
        at = _t(g["at"])
        areas = g.get("areas") or [""]

        def frozen(path):
            return any(a == "" or _under(path, a) for a in areas)

        hits = []
        for w in work_items:
            exact = [c for c in commit_by_item.get(w["id"], []) if _t(c["date"]) and _t(c["date"]) > at
                     and any(frozen(p) for p in c["paths"])]
            if exact:
                hits.append((w, "exact", [c["sha"][:7] for c in exact], sorted({p for c in exact for p in c["paths"] if frozen(p)})))
                continue
            later = [c for c in w.get("_commits", []) if _t(c.get("date")) and _t(c["date"]) > at]
            touched = sorted(p for p in w["paths"] if frozen(p))
            if later and touched and w["kind"] != "direct":
                hits.append((w, "work-item", [c["sha"][:7] for c in later], touched))
        if hits:
            exact_only = all(h[1] == "exact" for h in hits)
            where = ", ".join(g.get("areas") or ["the repository"])
            cues.append({
                "id": f"gate:{g['id']}", "rule": "freeze.changed_after", "subject": {"kind": "gate", "id": g["id"]},
                "confidence": "high" if exact_only else "medium",
                "summary": f"{g['label']} at {g['at'][11:16]}: {where} changed afterwards in "
                           + ", ".join(_name(h[0]) for h in hits),
                "declared": {"text": g["label"], "at": g["at"], "areas": g.get("areas", []),
                             "session": g.get("source", {}).get("session"), "confirmed_by": g["confirmed_by"]},
                "observed": {"work_items": [h[0]["id"] for h in hits],
                             "detail": "; ".join(f"{h[0]['id']}: {len(h[2])} commit(s) after the freeze "
                                                 + ("touching " if h[1] == "exact" else "on work that touches ")
                                                 + ", ".join(h[3][:3]) for h in hits)},
            })

    # G-open: a gate passed while committed work due before it is still open.
    # A freeze only speaks for commitments linked inside its scope (Develop finding F1).
    def in_scope(row, g):
        if g["kind"] != "freeze" or not g.get("areas"):
            return True
        refs = [l["ref"] for l in row["links"] if l["kind"] == "path"]
        refs += [p for m in row["matched"] for p in items[m]["paths"]]
        return any(_under(r, a) or _under(a, r) for r in refs for a in g["areas"])

    for g in gate_rows:
        if not g["passed"] or g["kind"] == "checkpoint":
            continue
        for row in commitment_rows:
            due = _t(row.get("due"))
            if due and due <= _t(g["at"]) and row["state"] == "in_progress" and in_scope(row, g):
                cues.append({
                    "id": f"gate:{g['id']}:{row['id']}", "rule": "gate.passed_with_open_work",
                    "subject": {"kind": "commitment", "id": row["id"]}, "confidence": "high",
                    "summary": f"{g['label']} passed at {g['at'][11:16]}; \"{row['text']}\" still has open work",
                    "declared": {"text": row["text"], "due": row["due"], "gate": g["id"], "confirmed_by": row["confirmed_by"]},
                    "observed": {"work_items": [m for m in row["matched"] if items[m]["in_flight"]],
                                 "detail": "linked work is still in flight"},
                })

    # decisions: areas that changed after the decision (context only, never a cue)
    decision_rows = []
    for d in declared["decisions"]:
        start = since(d) or now
        later = sorted(w["id"] for w in work_items if d.get("areas")
                       and any(_under(p, a) for p in w["paths"] for a in d["areas"])
                       and _t(w["last_activity_at"]) and _t(w["last_activity_at"]) > start)
        decision_rows.append(dict(d, changed_after=later))

    used_sessions = {x.get("source", {}).get("session") for k in declared for x in declared[k]}
    return {
        "source": source, "now": _iso(now), "proposed_pending": pending,
        "sessions": [s for s in data["sessions"] if s["id"] in used_sessions],
        "gates": gate_rows, "commitments": commitment_rows, "decisions": decision_rows, "cues": cues,
    }
