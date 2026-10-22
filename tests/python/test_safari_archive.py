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
                for source in (ROOT / "extension/src").rglob("*"):
                    if source.is_file():
                        self.assertEqual(archive.read("tibia-anti-ad-safari/" + source.relative_to(ROOT / "extension/src").as_posix()), source.read_bytes())
                self.assertIn("tibia-anti-ad-safari/LICENSE", archive.namelist())
                self.assertIn("tibia-anti-ad-safari/THIRD_PARTY_NOTICES.md", archive.namelist())
