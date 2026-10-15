import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("profile_renderer", ROOT / "scripts/render_profile.py")
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


class ProfileTests(unittest.TestCase):
    def test_calendar_uses_attribute_names_not_order(self):
        parser = renderer.Calendar()
        parser.feed('<td data-level="3" data-date="2026-10-15"></td><td data-date="2026-10-14" data-level="0"></td>')
        self.assertEqual(parser.days, {"2026-10-15":3,"2026-10-14":0})

    def test_invalid_levels_fail_closed(self):
        with self.assertRaises(ValueError):
            renderer.Calendar().feed('<td data-date="2026-10-15" data-level="8"></td>')

    def test_text_is_escaped(self):
        self.assertIn("&lt;script&gt;&amp;",renderer.text(0,0,"<script>&"))

    def test_assets_are_valid_self_contained_xml(self):
        for path in (ROOT / "assets").glob("*.svg"):
            source = path.read_text()
            element = ET.fromstring(source)
            self.assertEqual(element.tag,"{http://www.w3.org/2000/svg}svg")
            self.assertNotIn("<script",source)
            self.assertNotIn("http://",source.replace('xmlns="http://www.w3.org/2000/svg"',""))
            self.assertNotIn("https://",source)
            self.assertIn("prefers-reduced-motion",source)
            self.assertNotIn("transform:translate",source)

    def test_both_console_layouts_exist(self):
        for name in ["console.svg","console-mobile.svg"]:
            self.assertTrue((ROOT / "assets" / name).is_file())

    def test_renderer_only_produces_profile_assets(self):
        with patch("sys.argv", ["render_profile.py"]):
            renderer.main()
        self.assertEqual(
            {path.name for path in (ROOT / "assets").glob("*.svg")},
            {"console.svg", "console-mobile.svg", "activity.svg"},
        )


if __name__ == "__main__":
    unittest.main()
