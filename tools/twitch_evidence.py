"""Combine independent evidence to tell official Tibia from other games on Twitch.

No single signal decides. Text (title/tags) is easy to fake or misread, and a
"!rubinot" command is often just a sponsor, so text alone never hides a stream.
The thumbnail shows the game client actually running:

* ot_only UI (e.g. the "Map View" window or Battle Pass of RubinOT-style clients)
  never appears in the official client, so it is enough on its own.
* tibia_like UI (Skills, Hunt Analyser, ...) appears in the official client *and*
  in OTServers built on it, so it only means "a Tibia-style client".

Verdicts: "other" (hide), "tibia" (keep) or "undetermined" (keep). Anything
contradictory or missing ends up undetermined.

    python3 tools/twitch_evidence.py streams.json               # fetch + OCR thumbnails
    python3 tools/twitch_evidence.py streams.json --ocr-dir DIR # reuse <channel>.txt OCR

Needs the `tesseract` command for live OCR. Input: array of objects with
`channel`, `title` and optional `tags`.
"""
import argparse
import json
import re
import subprocess
import tempfile
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "filters/twitch/tibia-evidence.json"
THUMBNAIL = "https://static-cdn.jtvnw.net/previews-ttv/live_user_{}-1920x1080.jpg"


def normalize(text):
    text = unicodedata.normalize("NFKD", text).casefold()
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


def matcher(terms):
    alt = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    pattern = re.compile(rf"(?<![a-z0-9])(?:{alt})(?![a-z0-9])")
    return lambda text: sorted(set(pattern.findall(text)))


class Evidence:
    def __init__(self, data):
        self.ot_ui = matcher(data["client_ui"]["ot_only"])
        self.tibia_ui = matcher(data["client_ui"]["tibia_like"])
        self.official = matcher(data["official_text"])
        self.servers = {game: matcher(terms) for game, terms in data["server_text"].items()}

    def classify(self, title, tags, ocr):
        """ocr is the thumbnail text, or None when no thumbnail could be read."""
        text = normalize(f"{title} {' '.join(tags)}")
        screen = normalize(ocr or "")
        found = {
            "ot_ui": self.ot_ui(screen),
            "tibia_ui": self.tibia_ui(screen),
            "official_text": self.official(text),
            "server_text": {g: m for g, f in self.servers.items() if (m := f(text))},
        }
        if found["ot_ui"]:
            return "other", "OTServer-only client UI on screen", found
        if found["server_text"] and not found["official_text"] and ocr is not None and not found["tibia_ui"]:
            return "other", "names another game and the screen shows no Tibia-style client", found
        if found["official_text"] and not found["server_text"] and found["tibia_ui"]:
            return "tibia", "official marker in text and a Tibia-style client on screen", found
        return "undetermined", "missing or conflicting evidence", found


def ocr_thumbnail(channel):
    with tempfile.TemporaryDirectory() as tmp:
        image = Path(tmp) / "thumb.jpg"
        try:
            image.write_bytes(urllib.request.urlopen(THUMBNAIL.format(channel), timeout=20).read())
        except OSError:
            return None
        result = subprocess.run(["tesseract", str(image), "-", "--psm", "11"], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("streams")
    parser.add_argument("--ocr-dir", type=Path)
    args = parser.parse_args()
    evidence = Evidence(json.loads(EVIDENCE.read_text()))
    results = []
    for stream in json.loads(Path(args.streams).read_text()):
        channel = stream["channel"]
        if args.ocr_dir:
            path = args.ocr_dir / f"{channel}.txt"
            ocr = path.read_text() if path.exists() else None
        else:
            ocr = ocr_thumbnail(channel)
        verdict, reason, found = evidence.classify(stream.get("title") or "", stream.get("tags") or [], ocr)
        results.append({"channel": channel, "verdict": verdict, "reason": reason, "evidence": found})
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
