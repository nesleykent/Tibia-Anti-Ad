"""Run the same dependency-free repository checks locally and in CI."""
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "extensions/tibia-anti-ad/extension"


def run(*command):
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def check_documentation():
    """Check maintained guide links without rewriting historical evidence."""
    documents = [*(ROOT / name for name in ("README.md", "MANIFESTO.md", "CONTRIBUTING.md",
                  "SECURITY.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md")),
                 *ROOT.glob("docs/*.md"),
                 ROOT / "extensions/tibia-anti-ad/README.md",
                 ROOT / "scripts/twitch/README.md", ROOT / "research/README.md"]
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


def generated_files():
    paths = [*ROOT.glob("filters/anti-ad-tibia*.txt"),
             EXTENSION / "manifest.json", EXTENSION / "sites.js",
             EXTENSION / "tibia-evidence.js", *EXTENSION.glob("sites/*.*")]
    return {p.relative_to(ROOT): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    check_documentation()
    scripts = [*EXTENSION.rglob("*.js"), *ROOT.glob("scripts/twitch/*.js"),
               *ROOT.glob("tests/*.cjs")]
    for script in sorted(scripts):
        run("node", "--check", str(script.relative_to(ROOT)))
    run("node", "tests/twitch-startup.cjs")
    run("node", "tests/twitch-settings.cjs")
    run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
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
