"""Release checks reject damaged or stale extension packages."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import release_extension as release


class ReleaseTests(unittest.TestCase):
    def packages(self, folder, version):
        for name, prefix in zip(release.PACKAGES,
                                ['tibia-anti-ad-chrome', 'tibia-anti-ad-safari', 'app']):
            path = folder / name
            with ZipFile(path, 'w') as archive:
                archive.writestr(prefix + '/manifest.json', json.dumps({'version': version}))
            (folder / (name + '.sha256')).write_text(
                hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + name + '\n')

    def test_rejects_stale_or_damaged_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.packages(folder, '1.7.4')
            self.assertEqual(len(release.verify(folder, '1.7.4')), 6)
            with self.assertRaises(ValueError):
                release.verify(folder, '1.2.3')
            (folder / release.PACKAGES[0]).write_bytes(b'damaged')
            with self.assertRaises(ValueError):
                release.verify(folder, '1.7.4')

    def test_publication_requires_both_successful_build_jobs(self):
        workflow = (release.ROOT / '.github/workflows/check.yml').read_text()
        self.assertIn('needs: [check, safari]', workflow)
        self.assertIn("github.event_name == 'push' && github.ref == 'refs/heads/main'", workflow)
        self.assertNotIn('continue-on-error', workflow)
        self.assertIn('dist/tibia-anti-ad-chrome.zip*', workflow)
