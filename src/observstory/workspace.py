"""Optional public workspace declaration; read Git objects, never the working tree."""
import json
import pathlib
import re
import subprocess
from .validate import _check, SCHEMA_PATH


def errors(data):
    schema = json.loads(SCHEMA_PATH.with_name("workspace-v1.json").read_text())
    result = []
    _check(data, schema, schema, "$", result)
    if result:
        return result
    ids = [r["id"] for r in data["records"]]
    if len(ids) != len(set(ids)):
        result.append("duplicate record id")
    for r in data["records"]:
        for url in r.get("sources", []):
            if not url.startswith("https://"):
                result.append("sources must be public HTTPS URLs")
        p = r.get("planned")
        if p:
            pattern = {"year": r"\d{4}", "month": r"\d{4}-(0[1-9]|1[0-2])", "day": r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"}[p["precision"]]
            if any(not re.fullmatch(pattern, p[k]) for k in ("start", "end") if k in p):
                result.append("planned dates must preserve their declared precision")
            if p.get("end", p["start"]) < p["start"]:
                result.append("planned end precedes start")
    by_id = {r["id"]: r for r in data["records"]}
    visited, stack = set(), set()
    def visit(key):
        if key in stack:
            return False
        if key in visited:
            return True
        stack.add(key)
        for child in by_id[key].get("members", []):
            if child in by_id and not visit(child):
                return False
        stack.remove(key)
        visited.add(key)
        return True
    if any(not visit(key) for key in by_id):
        result.append("cyclic workspace membership")
    for edge in data["relations"]:
        if edge["from"] not in ids or edge["to"] not in ids or edge["from"] == edge["to"]:
            result.append("relationship endpoints must be distinct workspace records")
    return result


def publish(repo, ref, output):
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", ref], text=True).strip()
    path = ".observstory/workspace.json"
    source = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], capture_output=True, text=True)
    target = pathlib.Path(output) / "data" / "workspace.json"
    if source.returncode:
        target.unlink(missing_ok=True)
        return
    data = json.loads(source.stdout)
    issues = errors(data)
    if issues:
        raise ValueError("Invalid workspace: " + "; ".join(issues))
    data["source_commit"] = commit
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
