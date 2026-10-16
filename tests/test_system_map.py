import json
import tempfile
import unittest
from pathlib import Path

from src.observstory.system_map import build, render_html, render_mermaid, validate_system_map


MODEL = {
    "schema": "observstory.system-map/v0",
    "title": "Example",
    "purpose": "Prove semantic architecture rendering.",
    "groups": [
        {"id": "input", "label": "Input", "order": 1},
        {"id": "core", "label": "Core", "order": 2},
    ],
    "nodes": [
        {
            "id": "specimen",
            "kind": "domain",
            "label": "Specimen",
            "group": "input",
            "status": "established",
            "basis": "human-declared",
        },
        {
            "id": "observation",
            "kind": "domain",
            "label": "Observation",
            "group": "core",
            "status": "candidate",
            "basis": "research",
            "evidence": [{"ref": "docs/research.md", "kind": "research"}],
        },
    ],
    "edges": [
        {
            "from": "specimen",
            "to": "observation",
            "kind": "produces",
            "status": "candidate",
            "basis": "research",
        }
    ],
    "views": [{"id": "flow", "label": "Flow", "include": ["specimen", "observation"]}],
}


class SystemMapValidation(unittest.TestCase):
    def test_valid_model(self):
        self.assertEqual(validate_system_map(MODEL), [])

    def test_missing_edge_target_fails(self):
        broken = json.loads(json.dumps(MODEL))
        broken["edges"][0]["to"] = "missing"
        self.assertTrue(any("missing node" in e for e in validate_system_map(broken)))

    def test_duplicate_node_id_fails(self):
        broken = json.loads(json.dumps(MODEL))
        broken["nodes"].append(dict(broken["nodes"][0]))
        self.assertTrue(any("duplicate node id" in e for e in validate_system_map(broken)))


class SystemMapRendering(unittest.TestCase):
    def test_mermaid_is_deterministic_and_has_no_coordinates(self):
        first = render_mermaid(MODEL)
        second = render_mermaid(MODEL)
        self.assertEqual(first, second)
        self.assertIn("flowchart LR", first)
        self.assertIn("Specimen", first)
        self.assertNotIn("position", first.lower())

    def test_view_filters_nodes(self):
        narrowed = json.loads(json.dumps(MODEL))
        narrowed["views"].append({"id": "one", "label": "One", "include": ["specimen"]})
        page = render_mermaid(narrowed, "one")
        self.assertIn("Specimen", page)
        self.assertNotIn("Observation", page)

    def test_html_has_semantic_editor_and_export(self):
        page = render_html(MODEL)
        self.assertIn("Edit semantics", page)
        self.assertIn("Export JSON", page)
        self.assertIn("application/json", page)
        self.assertIn("candidate", page)
        self.assertNotIn("<canvas", page.lower())

    def test_build_writes_durable_and_interactive_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "system.json"
            source.write_text(json.dumps(MODEL))
            out = root / "out"
            build(source, out)
            self.assertTrue((out / "system.mmd").exists())
            self.assertTrue((out / "system.html").exists())


if __name__ == "__main__":
    unittest.main()
