"""Build the Chrome variant of Tibia Anti-Ad into dist/tibia-anti-ad-chrome.

The Safari source in extension/src is shared; Chrome only
needs a service-worker background (extension/browsers/chrome) and a
few manifest changes. Load the output
folder with "Load unpacked" in chrome://extensions.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "extension/src"
CHROME = ROOT / "extension/browsers/chrome"
OUTPUT = ROOT / "dist/tibia-anti-ad-chrome"


def build():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(SOURCE, OUTPUT)
    # SF Symbols toolbar assets are for the Apple-platform build only.
    shutil.rmtree(OUTPUT / "icons/safari-toolbar", ignore_errors=True)
    popup = OUTPUT / "popup.html"
    popup.write_text(popup.read_text().replace("icons/safari-toolbar/active-64.png",
                                             "icons/chrome-toolbar/active-128.png"))
    for path in CHROME.iterdir():
        if path.is_dir():
            if path.name == "icons":
                shutil.copytree(path, OUTPUT / "icons", dirs_exist_ok=True)
            continue
        if path.name != "manifest-overrides.json":
            shutil.copy2(path, OUTPUT / path.name)
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    for key, value in json.loads((CHROME / "manifest-overrides.json").read_text()).items():
        if key.startswith("_"):
            continue
        if value is None:
            manifest.pop(key, None)
        else:
            manifest[key] = value
    for script in manifest["content_scripts"]:
        script.pop("css_origin", None)  # Safari-only key.
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    for notice in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / notice, OUTPUT / notice)
    return OUTPUT


if __name__ == "__main__":
    print(build())
