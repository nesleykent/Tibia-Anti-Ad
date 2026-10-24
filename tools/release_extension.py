"""Publish CI-built extension archives after all build/check jobs have passed."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('tibia-anti-ad-chrome.zip', 'tibia-anti-ad-safari-extension.zip',
            'tibia-anti-ad-safari-macos.zip')


def verify(folder, version):
    assets = []
    for name in PACKAGES:
        archive = folder / name
        checksum = folder / (name + '.sha256')
        expected = hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + name
        if checksum.read_text().strip() != expected:
            raise ValueError('Release checksum mismatch: ' + name)
        assets.extend([archive, checksum])
    for name, prefix in [(PACKAGES[0], 'tibia-anti-ad-chrome'),
                         (PACKAGES[1], 'tibia-anti-ad-safari')]:
        with ZipFile(folder / name) as archive:
            manifest = json.loads(archive.read(prefix + '/manifest.json'))
            if manifest['version'] != version:
                raise ValueError('Release manifest version mismatch: ' + name)
    return assets


def publish():
    version = json.loads((ROOT / 'extension/src/manifest.json').read_text())['version']
    tag = 'v' + version
    folder = ROOT / 'dist/release'
    assets = verify(folder, version)
    # Do not silently replace downloads or move an existing release/tag.
    existing = subprocess.run(['gh', 'release', 'list', '--limit', '100', '--json', 'tagName'],
                              check=True, capture_output=True, text=True)
    if any(release['tagName'] == tag for release in json.loads(existing.stdout)):
        print('Release already published: ' + tag)
        return
    notes = folder / 'release-notes.md'
    notes.write_text('Chrome and Safari downloads built from the verified commit. '
                     'Each ZIP includes a SHA-256 checksum.\n\n'
                     'The public Safari Mac app is ad-hoc signed and requires '
                     'Safari development settings. It does not include the '
                     'maintainer\'s personal signing certificate.\n')
    subprocess.run(['gh', 'release', 'create', tag, '--target', os.environ['GITHUB_SHA'],
                    '--title', 'Tibia Anti-Ad ' + version, '--generate-notes',
                    '--notes-file', str(notes), *map(str, assets)], check=True)


if __name__ == '__main__':
    publish()
