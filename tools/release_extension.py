"""Verify extension packages and publish written release notes through the maintainer account."""
import hashlib
import json
import argparse
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


def publish(notes, commit):
    version = json.loads((ROOT / 'extension/src/manifest.json').read_text())['version']
    assets = verify(ROOT / 'dist/release', version)
    if not notes.read_text().strip():
        raise ValueError('Written release notes are required')
    login = subprocess.run(['gh', 'api', 'user', '--jq', '.login'],
                           check=True, capture_output=True, text=True).stdout.strip()
    if login != 'nesleykent':
        raise ValueError('Publish through the maintainer account')
    subprocess.run(['gh', 'release', 'create', 'v' + version, '--target', commit,
                    '--title', 'Tibia Anti-Ad ' + version,
                    '--notes-file', str(notes), *map(str, assets)], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--notes-file', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    publish(args.notes_file, args.commit)
