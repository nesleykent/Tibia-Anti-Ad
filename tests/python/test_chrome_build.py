"""Validate the actual Chrome output, including browser-specific conversion."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("chrome_builder", ROOT / "tools/build_chrome_extension.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ChromeBuildTests(unittest.TestCase):
    def test_package_resources_and_chrome_conversion(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "extension"
            with patch.object(builder, "OUTPUT", output):
                builder.build()
                # A rebuild must discard obsolete files from earlier packages.
                (output / "obsolete.js").write_text("obsolete")
                builder.build()
            self.assertFalse((output / "obsolete.js").exists())
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertNotIn("browser_specific_settings", manifest)
            self.assertIn("service_worker", manifest["background"])
            self.assertNotIn("scripts", manifest["background"])
            self.assertFalse((output / "icons/safari-toolbar").exists())
            resources = [manifest["background"]["service_worker"], manifest["action"]["default_popup"],
                         *manifest["icons"].values(), *manifest["action"]["default_icon"].values(),
                         "LICENSE", "THIRD_PARTY_NOTICES.md"]
            for script in manifest["content_scripts"]:
                self.assertNotIn("css_origin", script)
                resources.extend(script.get("js", []) + script.get("css", []))
            resources.extend(r["path"] for r in manifest["declarative_net_request"]["rule_resources"])
            for resource in resources:
                with self.subTest(resource=resource):
                    self.assertTrue((output / resource).is_file())
            worker = (output / manifest["background"]["service_worker"]).read_text()
            self.assertEqual(manifest["background"]["service_worker"], "background.js")
            self.assertIn("importScripts", worker)
            for name in ("sites.js", "settings.js"):
                self.assertIn(name, worker)
                self.assertTrue((output / name).is_file())
            self.assertIn("MIT License", (output / "LICENSE").read_text())
