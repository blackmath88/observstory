"""Principles as tests (docs/definition/design-principles.md)."""

import glob
import pathlib
import unittest

from observstory.validate import validate
from tests.helpers import snapshot

NAMES = [pathlib.Path(p).stem for p in glob.glob(str(pathlib.Path(__file__).parents[1] / "fixtures/observations/*.json"))]


class Principles(unittest.TestCase):
    def test_every_fixture_snapshot_validates(self):
        for name in NAMES:
            with self.subTest(name=name):
                self.assertEqual(validate(snapshot(name)), [])

    def test_signals_are_about_areas_or_work_never_people(self):
        for name in NAMES:
            for s in snapshot(name)["signals"]:
                self.assertIn(s["subject"]["kind"], ("area", "work_item"))

    def test_every_signal_has_evidence_basis_confidence(self):
        for name in NAMES:
            for s in snapshot(name)["signals"]:
                self.assertTrue(s["evidence"])
                self.assertIn(s["basis"], ("derived", "heuristic", "declared"))
                self.assertIn(s["confidence"], ("high", "medium", "low"))

    def test_actors_carry_no_counts_and_are_alphabetical(self):
        for name in NAMES:
            actors = snapshot(name)["actors"]
            self.assertEqual([a["id"] for a in actors], sorted(a["id"] for a in actors))
            for a in actors:
                self.assertEqual(set(a), {"id", "kind", "linked", "work_items"})

    def test_validator_rejects_person_metrics(self):
        snap = snapshot("e1-same-subsystem")
        snap["actors"][0]["commits"] = 42
        self.assertTrue(validate(snap))


if __name__ == "__main__":
    unittest.main()
