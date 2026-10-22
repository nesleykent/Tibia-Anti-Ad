"""Classify full title and tag metadata."""
import json
import shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'extensions/tibia-anti-ad/extension'
CHROME = ROOT / 'extensions/tibia-anti-ad/chrome'
OUTPUT = ROOT / 'dist/tibia-anti-ad-chrome'

def build():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(SOURCE, OUTPUT)
    for path in CHROME.iterdir():
        if path.name != 'manifest-overrides.json':
            shutil.copy2(path, OUTPUT / path.name)
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    for key, value in json.loads((CHROME / 'manifest-overrides.json').read_text()).items():
        if key.startswith('_'):
            continue
        if value is None:
            manifest.pop(key, None)
        else:
            manifest[key] = value
    for script in manifest['content_scripts']:
        script.pop('css_origin', None)
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    return OUTPUT
if __name__ == '__main__':
    print(build())
