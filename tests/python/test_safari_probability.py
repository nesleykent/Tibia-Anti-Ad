"""Safari adds the probability presentation; Chrome keeps the shared filter."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import build_safari_extension as safari
import build_chrome_extension as chrome


class SafariProbabilityTests(unittest.TestCase):
    def test_safari_loads_probability_view_before_the_shared_filter(self):
        manifest = safari.safari_manifest(json.loads((safari.SOURCE / 'manifest.json').read_text()))
        entry = next(item for item in manifest['content_scripts'] if 'tibia-filter.js' in item.get('js', []))
        self.assertLess(entry['js'].index('tibia-probability.js'), entry['js'].index('tibia-filter.js'))
        self.assertIn('tibia-probability.css', entry['css'])
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'safari'
            safari.stage_web_extension(output)
            for name in ('tibia-probability.js', 'tibia-probability.css'):
                self.assertTrue((output / name).is_file())
            self.assertEqual((output / 'tibia-filter.js').read_bytes(), (safari.SOURCE / 'tibia-filter.js').read_bytes())

    def test_chrome_does_not_load_or_ship_the_safari_probability_view(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'chrome'
            with patch.object(chrome, 'OUTPUT', output):
                chrome.build()
            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertNotIn('tibia-probability', json.dumps(manifest))
            self.assertFalse((output / 'tibia-probability.js').exists())
            self.assertFalse((output / 'tibia-probability.css').exists())
