"""Check the downloadable package users extract before choosing Load unpacked."""
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
import build_chrome_extension as builder
import package_chrome_extension as packager


class ChromeArchiveTests(unittest.TestCase):
    def test_zip_can_be_extracted_and_loaded_from_the_documented_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archive_path = directory / "tibia-anti-ad-chrome.zip"
            with patch.object(builder, "OUTPUT", directory / "build"), patch.object(packager, "ARCHIVE", archive_path):
                packager.package()
                first_digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
                packager.package()
            self.assertEqual(hashlib.sha256(archive_path.read_bytes()).hexdigest(), first_digest)
            self.assertEqual(archive_path.with_suffix(".zip.sha256").read_text(), f"{first_digest}  {archive_path.name}\n")
            with ZipFile(archive_path) as archive:
                self.assertIsNone(archive.testzip())
                self.assertTrue(all(name.startswith("tibia-anti-ad-chrome/") for name in archive.namelist()))
                archive.extractall(directory / "extracted")
            folder = directory / "extracted/tibia-anti-ad-chrome"
            manifest = json.loads((folder / "manifest.json").read_text())
            self.assertNotIn("browser_specific_settings", manifest)
            self.assertEqual(manifest["background"], {"service_worker": "background.js"})
            self.assertTrue((folder / "background.js").is_file())
            self.assertTrue((folder / "LICENSE").is_file())
            self.assertTrue((folder / "THIRD_PARTY_NOTICES.md").is_file())
