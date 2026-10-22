"""Check browser-specific toolbar packaging and required raster sizes."""
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ToolbarIconTests(unittest.TestCase):
    def test_both_states_have_transparent_pngs_at_each_required_size(self):
        for browser, sizes in (("safari", (16, 19, 32, 38)), ("chrome", (16, 32, 48, 128))):
            base = ROOT / ("extension/src" if browser == "safari" else "extension/browsers/chrome")
            for size in sizes:
                images = []
                for state in ("active", "inactive"):
                    data = (base / f"icons/{browser}-toolbar/{state}-{size}.png").read_bytes()
                    self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                    self.assertEqual(struct.unpack(">II", data[16:24]), (size, size))
                    self.assertEqual(data[25], 6, "Expected an RGBA PNG with alpha")
                    images.append(data)
                self.assertNotEqual(*images)

    def test_default_action_uses_active_icons_without_changing_popup(self):
        for file, browser in (("extension/src/manifest.json", "safari"),
                              ("extension/browsers/chrome/manifest-overrides.json", "chrome")):
            action = json.loads((ROOT / file).read_text())["action"]
            self.assertEqual(action["default_popup"], "popup.html")
            self.assertTrue(all(f"icons/{browser}-toolbar/active-" in p
                                for p in action["default_icon"].values()))
