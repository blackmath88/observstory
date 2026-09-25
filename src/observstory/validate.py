"""Minimal JSON Schema validator (stdlib only, ADR-008).

Supports the subset used by schema/snapshot-v1.json: type, const, enum, required,
properties, additionalProperties(false), items, minItems, $ref to #/$defs.
Plus semantic checks the schema can't express (principles 1 and 2).
"""

from __future__ import annotations

import json
import pathlib

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[2] / "schema" / "snapshot-v1.json"
SCENE_SCHEMA_PATH = SCHEMA_PATH.with_name("scene-v1.json")
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _is_type(value, name):
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


def _check(value, schema, root, path, errors):
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        schema = root["$defs"][name]
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(value, t) for t in types):
            errors.append(f"{path}: expected {'/'.join(types)}, got {type(value).__name__}")
            return
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing '{key}'")
        props = schema.get("properties", {})
        for key, sub in props.items():
            if key in value:
                _check(value[key], sub, root, f"{path}.{key}", errors)
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: unexpected property '{key}'")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: needs at least {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                _check(item, schema["items"], root, f"{path}[{i}]", errors)


def semantic_errors(snapshot: dict) -> list[str]:
    errors = []
    ids = {w["id"] for w in snapshot.get("work_items", [])}
    for s in snapshot.get("signals", []):
        if s["subject"]["kind"] not in ("area", "work_item"):
            errors.append(f"signal {s['id']}: subject must be an area or work item")
        for w in s["work_items"]:
            if w not in ids:
                errors.append(f"signal {s['id']}: unknown work item {w}")
    for a in snapshot.get("actors", []):
        numeric = [k for k, v in a.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric:
            errors.append(f"actor {a['id']}: per-person numeric fields are not allowed ({numeric})")
    return errors


def validate(snapshot: dict, schema: dict | None = None) -> list[str]:
    schema = schema or json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    _check(snapshot, schema, schema, "$", errors)
    if not errors:
        errors += semantic_errors(snapshot)
    return errors


def scene_errors(scene: dict) -> list[str]:
    """Scene contract plus referential integrity: every reference resolves, every node is drawn once."""
    schema = json.loads(SCENE_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    _check(scene, schema, schema, "$", errors)
    if errors:
        return errors
    zones = {z["id"] for z in scene["zones"]}
    groups = {g["id"]: g for g in scene["groups"]}
    nodes = {n["id"]: n for n in scene["nodes"]}
    edges = {e["id"] for e in scene["edges"]}
    for g in scene["groups"]:
        if g["zone"] not in zones:
            errors.append(f"group {g['id']}: unknown zone {g['zone']}")
        for n in g["nodes"] + g["also_active"]:
            if n not in nodes:
                errors.append(f"group {g['id']}: unknown node {n}")
    for n in scene["nodes"]:
        if n["group"] not in groups or n["id"] not in groups[n["group"]]["nodes"]:
            errors.append(f"node {n['id']}: not drawn in its group {n['group']}")
    placed = [n for g in scene["groups"] for n in g["nodes"]]
    if len(placed) != len(set(placed)):
        errors.append("a node is drawn in more than one group")
    for e in scene["edges"]:
        for end in (e["from"], e["to"]):
            if end not in nodes:
                errors.append(f"edge {e['id']}: unknown node {end}")
    for a in scene["attention"]:
        if a["target"] not in edges and a["target"] not in nodes:
            errors.append(f"attention {a['label']!r}: unknown target {a['target']}")
    return errors
