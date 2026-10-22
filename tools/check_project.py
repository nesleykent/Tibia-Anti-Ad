"""Run the same dependency-free repository checks locally and in CI."""
import hashlib
import json
import struct
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "extension/src"


def run(*command):
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def check_documentation():
    """Check maintained guide links without rewriting historical evidence."""
    documents = [*(ROOT / name for name in ("README.md", "MANIFESTO.md", "CONTRIBUTING.md",
                  "SECURITY.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md")),
                 *ROOT.glob("docs/*.md"),
                 ROOT / "extension/README.md",
                 ROOT / "scripts/twitch/README.md", ROOT / "research/README.md",
                 ROOT / "research/fansites/README.md", ROOT / "research/fansites/friendly/README.md",
                 ROOT / "filters/README.md"]
    failures = []
    for document in documents:
        # Ignore external URLs, fragments and example text inside fenced code.
        content = re.sub(r"```.*?```", "", document.read_text(encoding="utf-8"), flags=re.S)
        for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", content):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            if not (document.parent / unquote(parsed.path)).exists():
                failures.append(f"{document.relative_to(ROOT)}: {target}")
    if failures:
        raise ValueError("Broken documentation links:\n" + "\n".join(failures))
    print(f"Checked local links in {len(documents)} maintained documents", flush=True)


def check_friendly_screenshots():
    directory = ROOT / "research/fansites/friendly"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    listed = set()
    for entry in manifest["entries"]:
        path = directory / entry["screenshot"]
        if path.parent != directory / "screenshots" or path.suffix != ".png" or path in listed:
            raise ValueError(f"Invalid or duplicate screenshot path: {entry['screenshot']}")
        listed.add(path)
        data = path.read_bytes()
        if (data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) != entry["bytes"]
                or hashlib.sha256(data).hexdigest() != entry["sha256"]
                or struct.unpack(">II", data[16:24]) != (entry["width"], entry["height"])):
            raise ValueError(f"Screenshot differs from supplied evidence: {path.name}")
    if listed != set((directory / "screenshots").glob("*.png")):
        raise ValueError("Screenshot inventory differs from its provenance manifest")
    print(f"Verified original bytes and dimensions of {len(listed)} friendly-fansite screenshots", flush=True)


def generated_files():
    paths = [*ROOT.glob("filters/lists/anti-ad-tibia*.txt"),
             EXTENSION / "manifest.json", EXTENSION / "sites.js",
             EXTENSION / "tibia-evidence.js", *EXTENSION.glob("sites/*.*")]
    return {p.relative_to(ROOT): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    check_documentation()
    check_friendly_screenshots()
    scripts = [*EXTENSION.rglob("*.js"), *ROOT.glob("scripts/twitch/*.js"),
               *ROOT.glob("tests/javascript/*.cjs")]
    for script in sorted(scripts):
        run("node", "--check", str(script.relative_to(ROOT)))
    run("node", "tests/javascript/twitch-startup.cjs")
    run("node", "tests/javascript/twitch-settings.cjs")
    run(sys.executable, "-m", "unittest", "discover", "-s", "tests/python", "-v")
    run(sys.executable, "tools/twitch_evidence.py", "--evaluate")
    before = generated_files()
    for builder in ("build_filters.py", "build_extension_sites.py", "twitch_evidence.py"):
        command = [sys.executable, f"tools/{builder}"]
        if builder == "twitch_evidence.py":
            command.append("--write-js")
        run(*command)
    after = generated_files()
    changed = sorted(str(p) for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    if changed:
        raise ValueError("Stale generated files were rebuilt; review and rerun:\n" + "\n".join(changed))
    print("All repository checks passed. Live browser behavior requires separate verification.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
