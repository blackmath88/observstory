"""Fitness checks for the prebuilt frontend the Action ships (ADR-038).

The Action copies frontend/release/ into a consumer's output when `frontend: observatory`
is set. Consumers never build it, so the committed bundle itself must be shippable."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RELEASE = ROOT / "frontend" / "release"


class FrontendRelease(unittest.TestCase):
    def test_bundle_is_present(self):
        self.assertTrue((RELEASE / "index.html").is_file(), "run `npm run release` in frontend/")
        self.assertTrue(any((RELEASE / "assets").glob("*.js")))

    def test_asset_urls_are_relative(self):
        html = (RELEASE / "index.html").read_text(encoding="utf-8")
        urls = re.findall(r'(?:src|href)\s*[=:]\s*"([^"]+\.(?:js|css))"', html)
        self.assertTrue(urls, "expected script and stylesheet references")
        for url in urls:
            self.assertTrue(url.startswith("./assets/"), f"asset URL must be relative: {url}")

    def test_every_referenced_asset_exists(self):
        html = (RELEASE / "index.html").read_text(encoding="utf-8")
        for name in set(re.findall(r"\./assets/([A-Za-z0-9._-]+)", html)):
            self.assertTrue((RELEASE / "assets" / name).is_file(), name)

    def test_bundle_carries_no_data(self):
        self.assertFalse((RELEASE / "data").exists(), "data/ is written per Action run, never shipped")

    def test_action_keeps_classic_as_default(self):
        action = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertRegex(action, r"frontend:\n(?:.*\n)*?\s+default: classic")
        self.assertIn('mv "$OBSERVSTORY_OUTPUT/index.html" "$OBSERVSTORY_OUTPUT/map.html"', action)


if __name__ == "__main__":
    unittest.main()
