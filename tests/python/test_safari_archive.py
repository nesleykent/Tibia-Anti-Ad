"""Validate the Safari temporary-extension download without requiring Xcode."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import package_safari_extension as packager
from safari_web_resources import content_manifest, resources


class SafariArchiveTests(unittest.TestCase):
    def test_source_zip_preserves_safari_manifest_and_original_resources(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "safari.zip"
            with patch.object(packager, "SOURCE_ZIP", output):
                packager.package_source()
                first = output.read_bytes()
                packager.package_source()
            self.assertEqual(output.read_bytes(), first)
            digest = hashlib.sha256(first).hexdigest()
            self.assertEqual(output.with_suffix(".zip.sha256").read_text(), f"{digest}  safari.zip\n")
            with ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                manifest = json.loads(archive.read("tibia-anti-ad-safari/manifest.json"))
                self.assertIn("safari", manifest["browser_specific_settings"])
                self.assertEqual(manifest, content_manifest(json.loads((ROOT / 'extension/src/manifest.json').read_text())))
                for source, relative in resources():
                    if relative.name != 'manifest.json':
                        self.assertEqual(archive.read('tibia-anti-ad-safari/' + relative.as_posix()), source.read_bytes())
                self.assertIn("tibia-anti-ad-safari/LICENSE", archive.namelist())
                self.assertIn("tibia-anti-ad-safari/THIRD_PARTY_NOTICES.md", archive.namelist())
