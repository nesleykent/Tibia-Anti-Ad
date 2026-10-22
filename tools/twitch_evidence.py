"""Tell official Tibia from other games in Twitch's Tibia category.

Follows the 2026-10-21 audit (research/twitch/data/2026-10-21/analysis):

* Text is normalized (accents, lookalike letters, fancy fonts, leetspeak,
  repeated and spaced-out letters). Server names, RubinOT worlds, domains such
  as xxxot.com, !server chat commands, tags and the channel name become weighted
  signals for "other"; official worlds, Tibia Global and official tags for
  "tibia". Fuzzy names also match a spelling mistake (rubimot, pokealianca).
* Words before a mention weaken it: negation ("nao", "sem"), leaving ("ex",
  "sai do"), comparison ("vs") or another time ("depois"). Weak context
  (server rates, old client versions, "OT", Pokemon words) never decides alone.
* Signals combine with diminishing returns. A side wins at decision.threshold
  with a lead of decision.margin; otherwise the stream stays undetermined.
  Official tags count half against a server in the title (the title outranks
  the tags). The generic "Tibia" tag proves nothing.
* Undetermined streams can then be read from the thumbnail (OCR): an
  OTServer-only client element ("Map View", Battle Pass) or a server name on
  screen adds its signal.

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
import math
import re
import subprocess
import tempfile
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "filters/sources/twitch/tibia-evidence.json"
EXTENSION_DATA = ROOT / "extension/src/tibia-evidence.js"
AUDIT = ROOT / "research/twitch/data/2026-10-21/analysis/classificacao.json"
THUMBNAIL = "https://static-cdn.jtvnw.net/previews-ttv/live_user_{}-1920x1080.jpg"
# Audit categories that name a game other than Tibia, and the official one.
AUDIT_OTHER = {"RubinOT", "PokeAlliance (PKA)", "PokeXGames (PXG)", "Outros OTServers", "Jogos Idle",
               "DeusOT / DeusOld", "Outros Pokémon", "Pokémon misto", "Outros jogos"}
AUDIT_TIBIA = {"Tibia"}


COMMAND = "!❗❕"
# Lookalike letters NFKD keeps: Cyrillic, Greek and small capitals.
LOOKALIKE = dict(zip("авекмнорстухіјѕԁɡαβεικνορτυχᴀʙᴄᴅᴇɢʜɪᴊᴋʟᴍɴᴏᴘʀꜱᴛᴜᴠᴡʏᴢ",
                     "abekmhopctyxijsdgabeikvoptuxabcdeghijklmnoprstuvwyz"))
LEET = str.maketrans("013457", "oieast")


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text))
    # Every mark (\p{M} in JavaScript), including emoji variation selectors such as "❗️".
    text = "".join(c for c in text if not unicodedata.category(c).startswith("M")).lower()
    return " ".join("".join(LOOKALIKE.get(c, c) for c in text).split())


def squeeze(text):
    return re.sub(r"([a-z])\1+", r"\1", text)


def leet(text):
    return text.translate(LEET) if re.search(r"[a-z]", text) and re.search(r"[0-9]", text) else text


def words(terms):
    return re.compile(r"(?:^| )(?:" + "|".join(re.escape(t) for t in terms) + r")(?: |$)")


def distance(a, b, limit):
    """Optimal string alignment distance, or limit + 1 once it exceeds limit."""
    before, previous = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        row = [i]
        for j in range(1, len(b) + 1):
            value = min(previous[j] + 1, row[j - 1] + 1, previous[j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                value = min(value, before[j - 2] + 1)
            row.append(value)
        if min(row) > limit:
            return limit + 1
        before, previous = previous, row
    return previous[len(b)]


def tokenize(text):
    """Words with position, a "!" (chat command) or "[" / "(" right before, and spaced-out letters joined."""
    raw = [{"text": m.group(0), "start": m.start(), "end": m.end(),
            "command": m.start() > 0 and text[m.start() - 1] in COMMAND,
            "bracket": text[:m.start()].rstrip().endswith(("[", "("))} for m in re.finditer(r"[a-z0-9]+", text)]
    tokens, i = [], 0
    while i < len(raw):
        j = i
        while (j + 1 < len(raw) and len(raw[j]["text"]) == 1 and len(raw[j + 1]["text"]) == 1
               and raw[j + 1]["start"] - raw[j]["end"] == 1 and text[raw[j]["end"]] in " .-_*·•"):
            j += 1
        if j - i >= 3:
            tokens.append({**raw[i], "text": "".join(t["text"] for t in raw[i:j + 1]), "end": raw[j]["end"]})
            i = j + 1
        else:
            tokens.append(raw[i])
            i += 1
    return tokens


def fuzzy_ui(term):
    # "map view" -> map\s*\S{0,2}iew: tolerates OCR noise such as "Map ¥Yiew".
    head = r"\s*".join(re.escape(w) for w in term[:-3].split())
    return re.compile(rf"{head}\s*\S{{0,2}}{re.escape(term[-3:])}")


def signal(side, source, game, text, weight, **extra):
    return {"side": side, "source": source, "game": game, "text": text, "weight": weight, **extra}


def combine(signals):
    """Strongest + half the next + a quarter the next...; each text counts once."""
    best = {}
    for s in signals:
        key = f"{s['source']}|{s['text']}"
        best[key] = max(best.get(key, s["weight"]), s["weight"])
    total = 0
    for i, w in enumerate(sorted(best.values(), reverse=True)):
        total += w / 2 ** i
    return total


def describe(s):
    if s["source"] == "screen":
        return f"{'OTServer-only client' if s['game'] == 'OTServer client' else s['game']} on screen: {s['text']}"
    if s["source"] == "context":
        return s["game"]
    if s["source"] == "channel":
        return f"{s['game']} in channel name"
    if s["source"] == "command":
        return f"!{s['text'].lstrip(COMMAND)} command"
    if s["source"] == "tag":
        return f"{'official' if s['game'] == 'Tibia' else s['game']} tag {s['text']}"
    if s["side"] == "tibia":
        return f"{s['text']} in title"
    return f"{s['game']}{' world' if s.get('kind') == 'world' else ''} in title{' (\"%s\")' % s['text'] if s.get('distance') else ''}"


def js_round(value):
    return math.floor(value * 100 + 0.5) / 100


class Evidence:
    def __init__(self, data):
        self.w = data["weights"]
        self.threshold, self.margin = data["decision"]["threshold"], data["decision"]["margin"]
        self.stale_tags = data["decision"]["stale_tags"]
        self.protected = {squeeze(normalize(w)) for w in data["fuzzy"]["protected"]}
        self.singles, self.phrases, self.fuzzy = {}, {}, []

        def add(term, entry, is_fuzzy=False):
            parts = [squeeze(p) for p in re.split(r"[^a-z0-9]+", normalize(term)) if p]
            key = squeeze("".join(parts))
            if len(parts) > 1:
                self.phrases.setdefault(" ".join(parts), entry)
                if len(key) < 8:
                    return
            self.singles.setdefault(key, entry)
            if is_fuzzy and len(key) >= 6:
                self.fuzzy.append((key, entry))

        official = data["official"]
        # Official first: a spelling mistake equally close to a world and a server counts as the world.
        for term in official["title"]:
            add(term, {"side": "tibia", "kind": "global" if normalize(term) == "global" else "official", "game": "Tibia"})
        for world in official["worlds"]:
            add(world, {"side": "tibia", "kind": "official", "game": "Tibia"}, True)
        for world in official["worlds_tags_only"]:
            add(world, {"side": "tibia", "kind": "bracketed", "game": "Tibia"})
        self.games = []
        for game, spec in data["games"].items():
            fuzzy_names = {normalize(t) for t in spec.get("fuzzy", [])}
            for term in spec["words"]:
                add(term, {"side": "other", "kind": "name", "game": game}, normalize(term) in fuzzy_names)
            for term in spec.get("fuzzy", []):
                add(term, {"side": "other", "kind": "name", "game": game}, True)
            for world in spec.get("worlds", []):
                add(world, {"side": "other", "kind": "world", "game": game})
            self.games.append((game, [re.compile(p) for p in spec.get("title_patterns", [])],
                               [re.compile(p) for p in spec["tag_patterns"]]))
        self.longest = max([3] + [len(k.split(" ")) for k in self.phrases])
        self.channel_keys = sorted(((k, e) for k, e in self.singles.items() if e["side"] == "other" and len(k) >= 6),
                                   key=lambda item: -len(item[0]))
        self.official_tags = [re.compile(p) for p in official["tag_patterns"]]
        self.world_tags = {normalize(w) for w in official["worlds"] + official["worlds_tags_only"]}
        self.contexts = [dict(c, side=side, re=re.compile(c["pattern"])) for side in ("other", "tibia") for c in data["context"][side]]
        self.modifiers = [(m["factor"], words(m["words"]), words(m["after"]) if m.get("after") else None)
                          for name, m in data["context"]["modifiers"].items() if not name.startswith("_")]
        self.ot_ui = [(t, fuzzy_ui(t)) for t in data["client_ui"]["ot_only"]]

    def misspelling(self, key, max_distance):
        """The closest fuzzy name to a word, if it is a plausible misspelling."""
        if len(key) < 5 or key in self.protected or key in self.singles:
            return None
        best = None
        for fkey, entry in self.fuzzy:
            limit = min(max_distance, 2 if len(fkey) >= 10 else 1)
            if fkey[0] != key[0] or abs(len(fkey) - len(key)) > limit:
                continue
            d = distance(key, fkey, limit)
            if d <= limit and (best is None or d < best["distance"]):
                best = {"entry": entry, "distance": d}
        return best

    def mentions(self, tokens, max_distance):
        """Every lexicon mention in the tokens, longest first."""
        found, i = [], 0
        while i < len(tokens):
            match = None
            for n in range(min(self.longest, len(tokens) - i), 0, -1):
                parts = [squeeze(t["text"]) for t in tokens[i:i + n]]
                key = squeeze("".join(parts))
                if n == 1:
                    entry = self.singles.get(key) or self.singles.get(squeeze(leet(tokens[i]["text"])))
                else:
                    entry = self.phrases.get(" ".join(parts)) or (self.singles.get(key) if len(key) >= 8 else None)
                if entry:
                    match = {"entry": entry, "n": n, "distance": 0}
                    break
            if not match:
                near = self.misspelling(squeeze(leet(tokens[i]["text"])), max_distance)
                if near:
                    match = {**near, "n": 1}
            if match:
                last = tokens[i + match["n"] - 1]
                found.append({**match["entry"], "distance": match["distance"], "index": i, "n": match["n"],
                              "start": tokens[i]["start"], "end": last["end"],
                              "text": " ".join(t["text"] for t in tokens[i:i + match["n"]]),
                              "command": tokens[i]["command"], "bracket": tokens[i]["bracket"]})
                i += match["n"]
            else:
                i += 1
        return found

    def modifier(self, text, tokens, m):
        """The strongest weakening word around a mention: 1 when there is none."""
        start = tokens[max(0, m["index"] - 2)]["start"] if m["index"] else m["start"]
        clause = re.split(r"[|/,.;:!?()\[\]{}\u2757\u2755]", text[start:m["start"]])[-1]
        before = " ".join(re.findall(r"[a-z0-9]+", clause))
        after = " ".join(t["text"] for t in tokens[m["index"] + m["n"]:m["index"] + m["n"] + 1])
        factor = 1
        for value, before_re, after_re in self.modifiers:
            if before_re.search(before) or (after_re and after_re.search(after)):
                factor = min(factor, value)
        return factor

    def title_signals(self, title):
        w = self.w
        tokens = tokenize(title)
        found = self.mentions(tokens, 2)
        servers = [m for m in found if m["side"] == "other"]
        signals = []
        for m in found:
            if m["side"] == "other":
                weight = (w["world"] if m["kind"] == "world" else w["title"] if m["distance"] == 0
                          else w["title_fuzzy"] if m["distance"] == 1 else w["title_far"])
                if m["command"]:
                    weight -= w["title"] - w["command"]
            else:
                if m["command"] or (m["kind"] == "bracketed" and not m["bracket"]):
                    continue
                # "Future OT Global": "global" right after a server is part of its name.
                if m["kind"] == "global" and any(s["index"] + s["n"] == m["index"] and not title[s["end"]:m["start"]].strip()
                                                 for s in servers):
                    continue
                weight = (w["official_fuzzy"] if m["distance"] else w["official_global"] if m["kind"] == "global"
                          else w["official_bracketed"] if m["kind"] == "bracketed" else w["official_title"])
            source = "command" if m["side"] == "other" and m["command"] else "title"
            signals.append(signal(m["side"], source, m["game"], m["text"], weight * self.modifier(title, tokens, m),
                                  kind=m["kind"], distance=m["distance"]))

        def overlaps(start, end):
            return any(start < m["end"] and m["start"] < end for m in found)

        for game, title_patterns, _ in self.games:
            for p in title_patterns:
                for m in p.finditer(title):
                    if overlaps(m.start(), m.end()):
                        continue
                    command = m.start() > 0 and title[m.start() - 1] in COMMAND
                    signals.append(signal("other", "command" if command else "title", game, m.group(0),
                                          w["command"] if command else w["pattern"]))
        for c in self.contexts:
            m = next((x for x in c["re"].finditer(title) if not overlaps(x.start(), x.end())), None)
            if m:
                signals.append(signal(c["side"], "context", c["label"], m.group(0), c["weight"]))
        return signals

    def tag_signals(self, tags):
        w = self.w
        signals = []
        for tag in dict.fromkeys(normalize(t).replace(" ", "") for t in tags):
            if tag in self.world_tags:
                signals.append(signal("tibia", "tag", "Tibia", tag, w["official_tag_world"]))
            elif any(p.search(tag) for p in self.official_tags):
                signals.append(signal("tibia", "tag", "Tibia", tag, w["official_tag"]))
            game = next((g for g, _, tag_patterns in self.games if any(p.search(tag) for p in tag_patterns)), None)
            if game:
                signals.append(signal("other", "tag", game, tag, w["tag"]))
                continue
            near = tag not in self.world_tags and self.misspelling(squeeze(leet(tag)), 1)
            if near and near["entry"]["side"] == "other":
                signals.append(signal("other", "tag", near["entry"]["game"], tag, w["tag_fuzzy"]))
        return signals

    def channel_signals(self, channel):
        name = squeeze(re.sub(r"[^a-z0-9]", "", normalize(channel or "")))
        hit = next(((k, e) for k, e in self.channel_keys if k in name), None)
        return [signal("other", "channel", hit[1]["game"], channel, self.w["channel"])] if hit else []

    def screen_signals(self, ocr):
        screen = normalize(ocr)
        signals = [signal("other", "screen", "OTServer client", t, self.w["screen_ui"]) for t, p in self.ot_ui if p.search(screen)]
        for m in self.mentions(tokenize(screen), 1):
            if m["side"] == "other":
                signals.append(signal("other", "screen", m["game"], m["text"], self.w["screen_fuzzy"] if m["distance"] else self.w["screen"]))
        return signals

    def decide(self, signals):
        title_other = combine([s for s in signals if s["side"] == "other" and s["source"] in ("title", "command")])
        title_tibia = any(s["side"] == "tibia" and s["source"] == "title" for s in signals)
        # Official tags are often stale or generic: they count less against a server in the title.
        stale = title_other >= self.threshold and not title_tibia
        weighted = [dict(s, weight=s["weight"] * self.stale_tags) if stale and s["side"] == "tibia" and s["source"] == "tag" else s
                    for s in signals]
        other = combine([s for s in weighted if s["side"] == "other"])
        tibia = combine([s for s in weighted if s["side"] == "tibia"])

        def top(side):
            ranked = sorted((s for s in weighted if s["side"] == side), key=lambda s: -s["weight"])
            return ", ".join(list(dict.fromkeys(describe(s) for s in ranked))[:3])

        score = {"other": js_round(other), "tibia": js_round(tibia)}
        if other >= self.threshold and other - tibia >= self.margin:
            return "other", top("other"), score
        if tibia >= self.threshold and tibia - other >= self.margin:
            return "tibia", top("tibia"), score
        if other >= self.threshold or tibia >= self.threshold:
            return "undetermined", "evidence for Tibia and another game", score
        return "undetermined", "not enough evidence" if other or tibia else "no decisive evidence", score

    def classify(self, title, tags, ocr=None, channel=""):
        """ocr is the thumbnail text, or None when it was not read; it is used only
        when the title, tags and channel name leave the stream undetermined."""
        signals = self.title_signals(normalize(title)) + self.tag_signals(tags) + self.channel_signals(channel)
        verdict, reason, score = self.decide(signals)
        if verdict == "undetermined" and ocr is not None:
            screen = self.screen_signals(ocr)
            if screen:
                signals += screen
                verdict, reason, score = self.decide(signals)
        found = {"signals": [dict(s, weight=js_round(s["weight"])) for s in signals], "score": score}
        return verdict, reason, found


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
        verdict, reason, _ = evidence.classify(row["titulo_original"], tags, channel=row["canal"])
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
        "// Generated by tools/twitch_evidence.py --write-js from filters/sources/twitch/tibia-evidence.json. Do not edit.\n"
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
        verdict, reason, found = evidence.classify(title, tags, channel=channel)
        if verdict == "undetermined":
            if args.ocr_dir:
                path = args.ocr_dir / f"{channel}.txt"
                ocr = path.read_text() if path.exists() else None
            else:
                ocr = ocr_thumbnail(channel)
            verdict, reason, found = evidence.classify(title, tags, ocr, channel)
        results.append({"channel": channel, "verdict": verdict, "reason": reason, "evidence": found})
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
