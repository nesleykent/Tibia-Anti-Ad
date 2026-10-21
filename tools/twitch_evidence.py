"""Classify full title and tag metadata."""
import argparse
import json
import re
import subprocess
import tempfile
import unicodedata
import urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'filters/twitch/tibia-evidence.json'

def normalize(text):
    text = unicodedata.normalize('NFKD', text).casefold()
    return ' '.join(''.join((c for c in text if not unicodedata.combining(c))).split())

def matcher(terms):
    alt = '|'.join((re.escape(t) for t in sorted(terms, key=len, reverse=True)))
    pattern = re.compile(f'(?<![a-z0-9])(?:{alt})(?![a-z0-9])')
    return lambda text: sorted(set(pattern.findall(text)))

class Evidence:

    def __init__(self, data):
        self.official = matcher(data['official_text'])
        self.servers = {game: matcher(terms) for game, terms in data['server_text'].items()}

    def classify(self, title, tags):
        """Classify full title and tag metadata."""
        text = normalize(f"{title} {' '.join(tags)}")
        found = {'official_text': self.official(text), 'server_text': {g: m for g, f in self.servers.items() if (m := f(text))}}
        if found['official_text'] and (not found['server_text']):
            return ('tibia', 'official marker in text and a Tibia-style client on screen', found)
        return ('undetermined', 'missing or conflicting evidence', found)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('streams')
    args = parser.parse_args()
    evidence = Evidence(json.loads(EVIDENCE.read_text()))
    results = []
    for stream in json.loads(Path(args.streams).read_text()):
        channel = stream['channel']
        verdict, reason, found = evidence.classify(stream.get('title') or '', stream.get('tags') or [])
        results.append({'channel': channel, 'verdict': verdict, 'reason': reason, 'evidence': found})
    print(json.dumps(results, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
