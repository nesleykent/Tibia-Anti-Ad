"""Tell official Tibia from other games in Twitch's Tibia category.

Follows the 2026-10-21 audit (research/twitch/data/2026-10-21/analysis):

* The title outranks the tags. A server declared in the title (not as a
  !command), including domains such as xxxot.com, hides a stream unless the
  title also names an official world or Tibia Global, whatever the tags say.
* With neither in the title, a server tag (rubinot, pka, baiakidle...) hides and
  an official world or tibiaglobal tag keeps.
* A "!server" chat command in the title (!rubinot) counts like the server's
  name. The generic "Tibia" tag proves nothing.
* Streams with strong evidence both ways (e.g. a rubinot tag next to a
  tibiaglobal tag), or only weak evidence, stay undetermined. Their thumbnail
  can then be read (OCR): an OTServer-only client element ("Map View", Battle
  Pass) marks them as another game.

Verdicts: "other" (hide), "tibia" or "undetermined" (both stay visible).

    python3 tools/twitch_evidence.py streams.json               # metadata, OCR undetermined via tesseract
    python3 tools/twitch_evidence.py streams.json --ocr-dir DIR # reuse <channel>.txt OCR
    python3 tools/twitch_evidence.py --evaluate                 # score against the audited 456 channels
    python3 tools/twitch_evidence.py --write-js                 # refresh the extension copy

Input: array of objects with `channel`, `title` and `tags`.
"""
import argparse
import collections
import json
import re
import subprocess
import tempfile
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "filters/twitch/tibia-evidence.json"
EXTENSION_DATA = ROOT / "extensions/tibia-anti-ad/extension/tibia-evidence.js"
AUDIT = ROOT / "research/twitch/data/2026-10-21/analysis/classificacao.json"
THUMBNAIL = "https://static-cdn.jtvnw.net/previews-ttv/live_user_{}-1920x1080.jpg"
# Audit categories that name a game other than Tibia, and the official one.
AUDIT_OTHER = {"RubinOT", "PokeAlliance (PKA)", "PokeXGames (PXG)", "Outros OTServers", "Jogos Idle",
               "DeusOT / DeusOld", "Outros Pokémon", "Pokémon misto", "Outros jogos"}
AUDIT_TIBIA = {"Tibia"}


def normalize(text):
    text = unicodedata.normalize("NFKD", text).casefold()
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


def words(terms):
    alt = "|".join(re.escape(normalize(t)) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<![a-z0-9])([!\u2757\u2755])?(?:{alt})(?![a-z0-9])")


def fuzzy(term):
    # "map view" -> map\s*\S{0,2}iew: tolerates OCR noise such as "Map ¥Yiew".
    head = r"\s*".join(re.escape(w) for w in term[:-3].split())
    return re.compile(rf"{head}\s*\S{{0,2}}{re.escape(term[-3:])}")


class Evidence:
    def __init__(self, data):
        official = data["official"]
        self.official_title = words(official["title"] + official["worlds"])
        # Worlds that are also ordinary words count in a title only as "[World" or "(World".
        alt = "|".join(re.escape(w) for w in official["worlds_tags_only"])
        self.official_bracketed = re.compile(rf"[\[(]\s*(?:{alt})(?![a-z0-9])")
        self.official_tags = [re.compile(p) for p in official["tag_patterns"]]
        self.world_tags = {normalize(w) for w in official["worlds"] + official["worlds_tags_only"]}
        self.games = {
            game: (words(spec["words"]), [re.compile(p) for p in spec.get("title_patterns", [])],
                   [re.compile(p) for p in spec["tag_patterns"]])
            for game, spec in data["games"].items()
        }
        self.ot_ui = [(t, fuzzy(t)) for t in data["client_ui"]["ot_only"]]

    def metadata(self, title, tags):
        title = normalize(title)
        tags = [normalize(t).replace(" ", "") for t in tags]
        found = {"declared": {}, "tagged": {}, "commands": {}, "official_title": [], "official_tags": []}
        for game, (pattern, title_patterns, tag_patterns) in self.games.items():
            hits = [(m.group(0), bool(m.group(1))) for m in pattern.finditer(title)]
            hits += [(m.group(0), m.start() > 0 and title[m.start() - 1] in "!\u2757\u2755")
                     for p in title_patterns for m in p.finditer(title)]
            for text, command in hits:
                found["commands" if command else "declared"].setdefault(game, []).append(text)
            tagged = [t for t in tags if any(p.search(t) for p in tag_patterns)]
            if tagged:
                found["tagged"][game] = tagged
        found["official_title"] = [m.group(0) for m in self.official_title.finditer(title) if not m.group(1)]
        found["official_title"] += self.official_bracketed.findall(title)
        found["official_tags"] = [t for t in tags if t in self.world_tags or any(p.search(t) for p in self.official_tags)]
        return found

    def classify(self, title, tags, ocr=None):
        """ocr is the thumbnail text, or None when it was not read."""
        found = self.metadata(title, tags)
        # A "!server" chat command in the title names the server just like plain text.
        declared = sorted(set(found["declared"]) | set(found["commands"]))
        tagged = sorted(found["tagged"])
        official_title, official_tags = found["official_title"], found["official_tags"]
        # The title outranks the tags.
        if declared and not official_title:
            return "other", f"declared in title: {', '.join(declared)}", found
        if not declared and not official_title:
            if tagged and not official_tags:
                return "other", f"tagged: {', '.join(tagged)}", found
            if official_tags and not tagged:
                return "tibia", "official world or tibiaglobal tag", found
        if official_title and not declared and not tagged:
            return "tibia", "official world or Tibia Global in title", found
        # The screen breaks ties: an OTServer-only client beats a "tibiaglobal" tag.
        if ocr is not None:
            screen = normalize(ocr)
            ui = [t for t, p in self.ot_ui if p.search(screen)]
            if ui:
                found["screen"] = ui
                return "other", f"OTServer-only client on screen: {', '.join(ui)}", found
        if declared or tagged:
            return "undetermined", "evidence for Tibia and another game", found
        return "undetermined", "no decisive evidence", found


def ocr_thumbnail(channel):
    with tempfile.TemporaryDirectory() as tmp:
        image = Path(tmp) / "thumb.jpg"
        try:
            image.write_bytes(urllib.request.urlopen(THUMBNAIL.format(channel), timeout=20).read())
        except OSError:
            return None
        result = subprocess.run(["tesseract", str(image), "-", "--psm", "11"], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None


def evaluate(evidence):
    """Compare metadata verdicts with the audit's categories; returns official streams hidden."""
    table = collections.Counter()
    wrong = []
    for row in json.loads(AUDIT.read_text())["classificacao"]:
        tags = [t.strip() for t in row["tags_originais"].split("|") if t.strip()]
        verdict, reason, _ = evidence.classify(row["titulo_original"], tags)
        truth = "other" if row["categoria"] in AUDIT_OTHER else "tibia" if row["categoria"] in AUDIT_TIBIA else "unclear"
        table[(truth, verdict)] += 1
        if verdict == "other" and truth != "other":
            wrong.append((truth, row["canal"], reason, row["titulo_original"][:70], row["tags_originais"]))
    for truth in ("other", "tibia", "unclear"):
        print(truth.ljust(8), {v: table[(truth, v)] for v in ("other", "undetermined", "tibia")})
    for item in wrong:
        print("HIDDEN", *item, sep=" | ")
    return [w for w in wrong if w[0] == "tibia"]


def extension_data(data):
    return (
        "// Generated by tools/twitch_evidence.py --write-js from filters/twitch/tibia-evidence.json. Do not edit.\n"
        f"globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE = {json.dumps(data, ensure_ascii=False, indent=2)};\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("streams", nargs="?")
    parser.add_argument("--ocr-dir", type=Path)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--write-js", action="store_true")
    args = parser.parse_args()
    data = json.loads(EVIDENCE.read_text())
    evidence = Evidence(data)
    if args.write_js:
        EXTENSION_DATA.write_text(extension_data(data))
        return
    if args.evaluate:
        raise SystemExit(1 if evaluate(evidence) else 0)
    if not args.streams:
        parser.error("streams is required")
    results = []
    for stream in json.loads(Path(args.streams).read_text()):
        channel, title, tags = stream["channel"], stream.get("title") or "", stream.get("tags") or []
        verdict, reason, found = evidence.classify(title, tags)
        if verdict == "undetermined":
            if args.ocr_dir:
                path = args.ocr_dir / f"{channel}.txt"
                ocr = path.read_text() if path.exists() else None
            else:
                ocr = ocr_thumbnail(channel)
            verdict, reason, found = evidence.classify(title, tags, ocr)
        results.append({"channel": channel, "verdict": verdict, "reason": reason, "evidence": found})
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
