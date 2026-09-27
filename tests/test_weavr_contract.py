"""Known-consumer contract fitness tests for the Weavr integration."""

import json
import pathlib
import unittest

from tests.helpers import snapshot

ROOT = pathlib.Path(__file__).parents[1]
CONTRACT = json.loads((ROOT / "docs/integrations/weavr-consumer-contract-v1.json").read_text())


class WeavrConsumerContract(unittest.TestCase):
    def test_fixture_satisfies_weavr_required_shape(self):
        snap = snapshot("e1-same-subsystem")

        self.assertEqual(snap["schema"], CONTRACT["provider_contract"])

        for key in CONTRACT["required_top_level"]:
            self.assertIn(key, snap)

        for key in CONTRACT["required_repository_fields"]:
            self.assertIn(key, snap["repository"])

        for signal in snap["signals"]:
            for key in CONTRACT["required_signal_fields"]:
                self.assertIn(key, signal)

    def test_signal_semantics_used_by_weavr_remain_typed(self):
        snap = snapshot("e1-same-subsystem")
        for signal in snap["signals"]:
            self.assertIn(signal["basis"], ("derived", "heuristic", "declared"))
            self.assertIn(signal["confidence"], ("high", "medium", "low"))

    def test_contract_explicitly_allows_additive_fields(self):
        self.assertEqual(CONTRACT["compatibility"]["additive_fields"], "allowed")


if __name__ == "__main__":
    unittest.main()
