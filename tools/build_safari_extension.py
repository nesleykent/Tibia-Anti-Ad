"""Build a universal Safari app with ad-hoc or explicit local development signing."""
import argparse
import json
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "extension/src"
CONFIG = ROOT / "extension/browsers/safari"
PROJECT_ROOT = ROOT / "dist/safari-project"
PROJECT = PROJECT_ROOT / "Tibia Anti-Ad/Tibia Anti-Ad.xcodeproj"
DERIVED = ROOT / "dist/safari-build"
APP = ROOT / "dist/Tibia Anti-Ad.app"
BUNDLE_ID = "com.nesleykent.tibiaantiad"


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


def build(sign_identity="-"):
    if sys.platform != "darwin":
        raise RuntimeError("Building the Safari app requires macOS and full Xcode.")
    if sign_identity != "-":
        identities = subprocess.check_output(
            ["security", "find-identity", "-v", "-p", "codesigning"], text=True)
        if not sign_identity or not any(sign_identity in line and '"' in line
                                        for line in identities.splitlines()):
            raise RuntimeError("Signing identity is not valid. Check Xcode's certificates and the Apple WWDR intermediate certificate.")
    if PROJECT_ROOT.exists():
        shutil.rmtree(PROJECT_ROOT)
    run("xcrun", "safari-web-extension-converter", SOURCE,
        "--project-location", PROJECT_ROOT, "--app-name", "Tibia Anti-Ad",
        "--bundle-identifier", BUNDLE_ID, "--swift", "--macos-only",
        "--copy-resources", "--no-open", "--no-prompt")
    # The converter derives the host ID from the app's display name, ignoring
    # the supplied ID for that target. Both IDs must share the same prefix.
    project_file = PROJECT / "project.pbxproj"
    project_file.write_text(project_file.read_text().replace('"com.nesleykent.Tibia-Anti-Ad"', BUNDLE_ID))
    # Generated comments must not embed the build machine owner's full name.
    for path in PROJECT_ROOT.rglob("*.swift"):
        path.write_text("\n".join(line for line in path.read_text().splitlines()
                                  if not line.startswith("//  Created by ")) + "\n")
    version = json.loads((SOURCE / "manifest.json").read_text())["version"]
    run("xcodebuild", "-project", PROJECT, "-scheme", "Tibia Anti-Ad",
        "-configuration", "Release", "-derivedDataPath", DERIVED,
        "-destination", "generic/platform=macOS", "ARCHS=arm64 x86_64",
        "ONLY_ACTIVE_ARCH=NO", "MACOSX_DEPLOYMENT_TARGET=14.0",
        f"MARKETING_VERSION={version}", "CURRENT_PROJECT_VERSION=1",
        "CODE_SIGNING_ALLOWED=NO", "build")
    if APP.exists():
        shutil.rmtree(APP)
    shutil.copytree(DERIVED / "Build/Products/Release/Tibia Anti-Ad.app", APP, symlinks=True)
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, APP / "Contents/Resources" / name)
    extensions = list((APP / "Contents/PlugIns").glob("*.appex"))
    if len(extensions) != 1:
        raise RuntimeError("Expected exactly one embedded Safari extension.")
    extension = extensions[0]
    host_info = plistlib.loads((APP / "Contents/Info.plist").read_bytes())
    ext_info = plistlib.loads((extension / "Contents/Info.plist").read_bytes())
    if not ext_info["CFBundleIdentifier"].startswith(host_info["CFBundleIdentifier"] + "."):
        raise RuntimeError("Safari extension bundle identifier does not match its host.")
    resources = extension / "Contents/Resources"
    for original in SOURCE.rglob("*"):
        if original.is_file() and original.read_bytes() != (resources / original.relative_to(SOURCE)).read_bytes():
            raise RuntimeError(f"Packaged extension resource differs: {original.name}")
    for bundle, entitlements in ((extension, "extension.entitlements"), (APP, "host.entitlements")):
        run("codesign", "--force", "--sign", sign_identity,
            "--entitlements", CONFIG / entitlements, bundle)
    run("codesign", "--verify", "--deep", "--strict", APP)
    for bundle, info in ((APP, host_info), (extension, ext_info)):
        binary = bundle / "Contents/MacOS" / info["CFBundleExecutable"]
        architectures = subprocess.check_output(["lipo", "-archs", str(binary)], text=True).split()
        if not {"arm64", "x86_64"}.issubset(architectures):
            raise RuntimeError(f"Expected a universal Mac binary: {binary}")
    return APP


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sign-identity", default="-",
                        help="Local signing identity name or SHA-1; default: ad-hoc (-).")
    print(build(parser.parse_args().sign_identity))
