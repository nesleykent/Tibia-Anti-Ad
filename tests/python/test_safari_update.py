"""Personal updates must retain the installed app when verification fails."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import update_safari_extension as updater


class SafariUpdateTests(unittest.TestCase):
    def test_invalid_candidate_does_not_touch_installed_app_or_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed, built, backup = root / "Installed.app", root / "Built.app", root / "backup.app"
            for path, version in ((installed, "installed"), (built, "invalid"), (backup, "backup")):
                path.mkdir()
                (path / "version").write_text(version)
            with patch.object(updater, "BACKUP", backup), patch.object(updater, "verify_app", side_effect=RuntimeError("wrong team")):
                with self.assertRaisesRegex(RuntimeError, "wrong team"):
                    updater.install(built, installed, "TEAM")
            self.assertEqual((installed / "version").read_text(), "installed")
            self.assertEqual((backup / "version").read_text(), "backup")

    def test_failed_installed_verification_restores_previous_app(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed, built = root / "Installed.app", root / "Built.app"
            installed.mkdir()
            built.mkdir()
            (installed / "version").write_text("old")
            (built / "version").write_text("new")
            with patch.object(updater, "BACKUP", root / "backup.app"), patch.object(updater, "verify_app", side_effect=["TEAM", RuntimeError("invalid copy")]):
                with self.assertRaisesRegex(RuntimeError, "invalid copy"):
                    updater.install(built, installed, "TEAM")
            self.assertEqual((installed / "version").read_text(), "old")

    def test_successful_update_replaces_app_and_retains_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed, built = root / "Installed.app", root / "Built.app"
            installed.mkdir()
            built.mkdir()
            (installed / "version").write_text("old")
            (built / "version").write_text("new")
            with patch.object(updater, "BACKUP", root / "backup.app"), patch.object(updater, "verify_app", return_value="TEAM"):
                backup = updater.install(built, installed, "TEAM")
            self.assertEqual((installed / "version").read_text(), "new")
            self.assertEqual((backup / "version").read_text(), "old")

    def test_stale_copies_are_every_other_app_safari_sees(self):
        listing = """
     com.nesleykent.tibiaantiad.Extension(1.3.0)
            Path = /Applications/Tibia Anti-Ad.app/Contents/PlugIns/Tibia Anti-Ad Extension.appex
     com.nesleykent.tibiaantiad.Extension(1.2.3)
            Path = /Users/me/Downloads/Tibia Anti-Ad.app/Contents/PlugIns/Tibia Anti-Ad Extension.appex
     com.nesleykent.tibiaantiad.Toolbar(1.3.0)
            Path = /Users/me/Code/Adblock/local/safari/previous.noindex/Tibia Anti-Ad.app/Contents/PlugIns/Tibia Anti-Ad Toolbar.appex
"""
        self.assertEqual(updater.stale_copies(listing, Path("/Applications/Tibia Anti-Ad.app")), [
            Path("/Users/me/Code/Adblock/local/safari/previous.noindex/Tibia Anti-Ad.app"),
            Path("/Users/me/Downloads/Tibia Anti-Ad.app"),
        ])

    def test_registration_removes_duplicate_uuids_at_the_same_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            app = Path(temporary) / "Installed.app"
            appex = app / "Contents/PlugIns/Filter.appex"
            appex.mkdir(parents=True)
            listing = f"            Path = {appex}\n"
            with patch.object(updater, "bundle_identifier", return_value="test.Filter"), patch.object(
                    updater, "output", side_effect=[listing * 2, "", "", listing]) as command:
                updater.reconcile_registration(app)
            self.assertEqual(command.call_args_list, [
                (("pluginkit", "-mADvvv", "-i", "test.Filter"),),
                (("pluginkit", "-r", appex),),
                (("pluginkit", "-a", appex),),
                (("pluginkit", "-mADvvv", "-i", "test.Filter"),),
            ])

    def test_registration_preserves_an_already_unique_instance(self):
        with tempfile.TemporaryDirectory() as temporary:
            app = Path(temporary) / "Installed.app"
            appex = app / "Contents/PlugIns/Filter.appex"
            appex.mkdir(parents=True)
            with patch.object(updater, "bundle_identifier", return_value="test.Filter"), patch.object(
                    updater, "output", return_value=f"Path = {appex}\n") as command:
                updater.reconcile_registration(app)
            command.assert_called_once_with("pluginkit", "-mADvvv", "-i", "test.Filter")

    def test_registration_rejects_a_failed_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            app = Path(temporary) / "Installed.app"
            appex = app / "Contents/PlugIns/Filter.appex"
            appex.mkdir(parents=True)
            listing = f"Path = {appex}\n" * 2
            with patch.object(updater, "bundle_identifier", return_value="test.Filter"), patch.object(
                    updater, "output", side_effect=[listing, "", "", listing]):
                with self.assertRaisesRegex(RuntimeError, "still duplicated"):
                    updater.reconcile_registration(app)
