"""Update the installed personal Safari app using a valid identity from its team.

Run from the current local checkout. This does not fetch code or publish assets.
"""
import hashlib
import plistlib
import re
import shutil
import ssl
import subprocess
import tempfile
from pathlib import Path

from build_safari_extension import BUNDLE_ID, ROOT, WEB_EXTENSION_ID, build, hide_from_system, remove_build_files

# Version 1.3 briefly shipped a second, toolbar extension; an installed app
# that still has it is accepted as the one being replaced.
TOOLBAR_ID = BUNDLE_ID + ".Toolbar"

INSTALLED = Path("/Applications/Tibia Anti-Ad.app")
BACKUP = ROOT / "local/safari/previous.noindex/Tibia Anti-Ad.app"


def output(*args):
    return subprocess.check_output([str(arg) for arg in args], text=True,
                                   stderr=subprocess.STDOUT)


def bundle_identifier(bundle):
    return plistlib.loads((bundle / "Contents/Info.plist").read_bytes())["CFBundleIdentifier"]


def verify_app(app, expected_team=None):
    """Check that the app and its extensions are signed by one Apple Development team.

    The web extension is required; an installed app that still has the former
    toolbar extension is accepted as the one being replaced.
    """
    output("codesign", "--verify", "--deep", "--strict", app)
    extensions = {bundle_identifier(bundle): bundle for bundle in (app / "Contents/PlugIns").glob("*.appex")}
    if WEB_EXTENSION_ID not in extensions or not set(extensions) <= {WEB_EXTENSION_ID, TOOLBAR_ID}:
        raise RuntimeError(f"Unexpected Safari extensions in {app}: {sorted(extensions)}")
    if bundle_identifier(app) != BUNDLE_ID:
        raise RuntimeError(f"Unexpected app identifier in {app}.")
    team = expected_team
    for bundle in [app, *extensions.values()]:
        signature = output("codesign", "-dvv", bundle)
        match = re.search(r"^TeamIdentifier=([A-Z0-9]+)$", signature, re.M)
        if not match or "Authority=Apple Development:" not in signature:
            raise RuntimeError("Expected a personally signed Tibia Anti-Ad app and extensions.")
        team = team or match[1]
        if match[1] != team:
            raise RuntimeError("Update signing team differs from the installed app.")
    return team


def find_identity(team):
    valid = output("security", "find-identity", "-v", "-p", "codesigning")
    fingerprints = set(re.findall(r'\) ([A-Fa-f0-9]{40}) "Apple Development:', valid))
    certificates = output("security", "find-certificate", "-a", "-c", "Apple Development", "-p")
    for pem in re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", certificates, re.S):
        der = ssl.PEM_cert_to_DER_cert(pem)
        fingerprint = hashlib.sha1(der).hexdigest().upper()
        if fingerprint not in fingerprints:
            continue
        subject = subprocess.check_output(
            ["openssl", "x509", "-inform", "DER", "-noout", "-subject", "-nameopt", "RFC2253"],
            input=der).decode()
        if re.search(r"(?:^|,)OU=" + re.escape(team) + r"(?:,|$)", subject):
            return fingerprint
    raise RuntimeError("No valid Apple Development identity for the installed team. Renew the certificate in Xcode; the installed app has not been replaced.")


def install(built, installed, team):
    """Stage and verify before swapping; retain the previous app for rollback."""
    with tempfile.TemporaryDirectory(prefix="tibia-update-", dir=installed.parent) as temporary:
        stage = Path(temporary)
        candidate, previous = stage / installed.name, stage / "previous.app"
        shutil.copytree(built, candidate, symlinks=True)
        verify_app(candidate, team)
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        if BACKUP.exists():
            shutil.rmtree(BACKUP)
        shutil.copytree(installed, BACKUP, symlinks=True)
        installed.rename(previous)
        try:
            candidate.rename(installed)
            verify_app(installed, team)
        except BaseException:
            if installed.exists():
                shutil.rmtree(installed)
            previous.rename(installed)
            raise
    return BACKUP


LSREGISTER = ("/System/Library/Frameworks/CoreServices.framework/Frameworks/"
              "LaunchServices.framework/Support/lsregister")


def containing_app(path):
    for parent in Path(path).parents:
        if parent.suffix == ".app":
            return parent
    return None


def stale_copies(listing, installed=INSTALLED):
    """Other Tibia Anti-Ad apps whose extensions Safari can still see, from
    `pluginkit -mAvvv` output. Safari lists one extension entry per copy."""
    apps = {containing_app(path) for path in re.findall(r"^\s*Path = (.+\.appex)$", listing, re.M)}
    return sorted(app for app in apps if app and app.resolve() != installed.resolve())


def remove_stale_copies():
    """Unregister and trash every other copy (old builds, downloaded previews,
    backups), so Safari shows Tibia Anti-Ad once."""
    listing = "".join(subprocess.run(["pluginkit", "-mAvvv", "-i", identifier], capture_output=True, text=True).stdout
                      for identifier in (WEB_EXTENSION_ID, TOOLBAR_ID))
    trash = Path.home() / ".Trash"
    for app in stale_copies(listing):
        for appex in (app / "Contents/PlugIns").glob("*.appex"):
            subprocess.run(["pluginkit", "-r", str(appex)], check=False)
        subprocess.run([LSREGISTER, "-u", str(app)], check=False)
        if app.exists():
            target = trash / f"{app.stem} {hashlib.sha1(str(app).encode()).hexdigest()[:8]}.app"
            shutil.move(str(app), str(target))
            print(f"Moved an old copy to the Trash: {app}")


def archive_backup(backup):
    """Keep the rollback copy as a ZIP: an .app on disk would show up in Safari
    as a second Tibia Anti-Ad extension."""
    archive = backup.with_suffix(".zip")
    if archive.exists():
        archive.unlink()
    subprocess.run(["ditto", "-c", "-k", "--keepParent", str(backup), str(archive)], check=True)
    subprocess.run([LSREGISTER, "-u", str(backup)], check=False)
    shutil.rmtree(backup)
    return archive


def main():
    if not INSTALLED.is_dir():
        raise RuntimeError("Install and personally sign the app once before using this updater.")
    # Serialize agent updates; never race another updater replacing the same app.
    import fcntl
    lock_path = ROOT / "local/safari/update.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another personal Safari update is already running.") from None
        team = verify_app(INSTALLED)
        identity = find_identity(team)
        built = build(identity)
        verify_app(built, team)
        # A closed host app is safe to replace. Do not close the user's Safari tabs.
        subprocess.run(["pkill", "-x", "Tibia Anti-Ad"], check=False)
        backup = install(built, INSTALLED, team)
        subprocess.run(["open", str(INSTALLED)], check=True)
        # The backup is for rollback only; keep it out of Launchpad and Safari.
        hide_from_system(backup)
        backup = archive_backup(backup)
        remove_stale_copies()
        # The installed app is all that is needed; the build cache is about 1 GB.
        remove_build_files()
        print(f"Updated and verified: {INSTALLED}\nPrevious app: {backup}")
        print("Safari was left running. Reload affected pages; a Safari restart may be needed to activate the update.")


if __name__ == "__main__":
    main()
