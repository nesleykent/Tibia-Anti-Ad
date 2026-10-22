"""Package the built Safari app and a temporary-extension ZIP with checksums."""
import hashlib
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "extension/src"
APP = ROOT / "dist/Tibia Anti-Ad.app"
SOURCE_ZIP = ROOT / "dist/tibia-anti-ad-safari-extension.zip"
APP_ZIP = ROOT / "dist/tibia-anti-ad-safari-macos.zip"


def checksum(path):
    path.with_suffix(".zip.sha256").write_text(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n", encoding="utf-8")


def package_source():
    SOURCE_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE_ZIP, "w", compression=ZIP_DEFLATED) as archive:
        files = [(p, Path("tibia-anti-ad-safari") / p.relative_to(SOURCE))
                 for p in sorted(SOURCE.rglob("*")) if p.is_file()]
        files += [(ROOT / name, Path("tibia-anti-ad-safari") / name)
                  for name in ("LICENSE", "THIRD_PARTY_NOTICES.md")]
        for path, relative in files:
            entry = ZipInfo(relative.as_posix())
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    checksum(SOURCE_ZIP)
    return SOURCE_ZIP


def package_app():
    if not APP.is_dir():
        raise RuntimeError("Build the Safari app first: python3 tools/build_safari_extension.py")
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(APP)], check=True)
    subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(APP), str(APP_ZIP)], check=True)
    checksum(APP_ZIP)
    return APP_ZIP


if __name__ == "__main__":
    print(package_source())
    print(package_app())
