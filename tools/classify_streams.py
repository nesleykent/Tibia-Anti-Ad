"""Conservative offline demonstration. Never enables automatic stream hiding."""
import argparse
import json
import re
import unicodedata
from pathlib import Path

OT = {"otserv", "otserver", "open tibia"}
OFFICIAL = {"official tibia", "tibia global"}


def normalize(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def classify(stream):
    if not isinstance(stream, dict):
        raise ValueError("Each stream must be an object")
    title = stream.get("title", "")
    tags = stream.get("tags", [])
    title = "" if title is None else title
    tags = [] if tags is None else tags
    if not isinstance(title, str) or not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        raise ValueError("title must be a string and tags must be an array of strings")
    title = normalize(title)
    tags = {normalize(tag) for tag in tags}
    label = "undetermined"
    reason = "Missing, ambiguous or insufficient corroborated declarations"
    # Check for contradictions even inside a longer tag, such as 'OTServ English'.
    text = " ".join([title, *sorted(tags)])
    ot_mention = re.search(r"\b(?:otserv|otserver|open tibia)\b", text)
    official_mention = re.search(r"\b(?:official tibia|tibia global)\b", text)
    if ot_mention and official_mention:
        reason = "Conflicting official Tibia and OTServ declarations"
    elif title in OT and tags & OT:
        label, reason = "OTServ", "Matching explicit title and tag declarations; unvalidated prototype"
    elif title in OFFICIAL and tags & OFFICIAL:
        label, reason = "Tibia", "Matching explicit title and tag declarations; unvalidated prototype"
    return {"classification": label, "hide": False, "reason": reason}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON array of stream objects")
    args = parser.parse_args()
    try:
        records = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError("Input must be a JSON array")
        results = [{"stream": item, **classify(item)} for item in records]
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
