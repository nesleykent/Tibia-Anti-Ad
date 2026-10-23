"""Compose Safari-only web presentation with the shared extension resources."""
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'extension/src'
SAFARI_WEB = ROOT / 'extension/browsers/safari/web'


def content_manifest(manifest):
    manifest = copy.deepcopy(manifest)
    for entry in manifest['content_scripts']:
        if 'tibia-filter.js' in entry.get('js', []):
            entry['js'].insert(entry['js'].index('tibia-filter.js'), 'tibia-probability.js')
            entry.setdefault('css', []).append('tibia-probability.css')
    return manifest


def resources():
    for base in (SOURCE, SAFARI_WEB):
        for path in sorted(base.rglob('*')):
            if path.is_file():
                yield path, path.relative_to(base)
