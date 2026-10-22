"""Build the ready-to-install Chrome ZIP and its SHA-256 checksum."""
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from build_chrome_extension import build

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "dist/tibia-anti-ad-chrome.zip"


def package():
    folder = build()
    with ZipFile(ARCHIVE, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                entry = ZipInfo((Path("tibia-anti-ad-chrome") / path.relative_to(folder)).as_posix())
                entry.compress_type = ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes())
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    ARCHIVE.with_suffix(".zip.sha256").write_text(f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    return ARCHIVE


if __name__ == "__main__":
    print(package())
