"""Generic text features shared by training and inference; no server lexicon.

Words, adjacent word pairs and character 3/4/5-grams are learned from labels.
Features use FNV-1a identifiers so the exported model contains no raw titles,
channel identifiers or readable names. The JavaScript port is checked for parity.
"""
import re
import unicodedata

LOOKALIKE = dict(zip("авекмнорстухіјѕԁɡαβεικνορτυχᴀʙᴄᴅᴇɢʜɪᴊᴋʟᴍɴᴏᴘʀꜱᴛᴜᴠᴡʏᴢ",
                     "abekmhopctyxijsdgabeikvoptuxabcdeghijklmnoprstuvwyz"))


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text))
    # Every mark (\p{M} in JavaScript), including emoji variation selectors such as "❗️".
    text = "".join(c for c in text if not unicodedata.category(c).startswith("M")).lower()
    return " ".join("".join(LOOKALIKE.get(c, c) for c in text).split())



def feature_id(value):
    result = 2166136261
    for char in value:
        result = ((result ^ ord(char)) * 16777619) & 0xffffffff
    return f"{result:08x}"


def text_features(text):
    tokens = [re.sub(r"[0-9]+", "#", word) for word in re.findall(r"[a-z0-9]+", normalize(text))]
    raw = {"w:" + word for word in tokens}
    raw.update("b:" + a + " " + b for a, b in zip(tokens, tokens[1:]))
    for word in set(tokens):
        padded = "^" + word + "$"
        raw.update("c:" + padded[i:i + n] for n in (3, 4, 5) for i in range(len(padded) - n + 1))
    # A shared character fragment is weaker than a complete word/phrase. This
    # limits confident decisions from a new word merely resembling a known one.
    return {feature_id(value): 0.25 if value.startswith("c:") else 1.0 for value in raw}


def feature_fields(title, tags):
    tag_features = {}
    for tag in tags:
        tag_features.update(text_features(tag))
    return text_features(title), tag_features


def features(title, tags):
    title_features, tag_features = feature_fields(title, tags)
    return title_features | tag_features
