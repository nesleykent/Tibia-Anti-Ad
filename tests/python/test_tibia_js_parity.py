"""Compare browser inference with the frozen Python model, without fitting."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from tibia_spans import SpanModel as PrivateModel
from tibia_private_data import load_rows
from twitch_evidence import browser_data


class BrowserParityTests(unittest.TestCase):
    def test_export_and_all_reviewed_inputs(self):
        data = browser_data()
        self.assertEqual(json.loads((ROOT / 'filters/sources/twitch/tibia-evidence.json').read_text()), data)
        rows = [{'title': r['title'], 'tags': r['tags']} for r in load_rows()]
        rows.extend(json.loads((ROOT / 'tests/data/tibia-span-heldout-acceptance.json').read_text())['cases'])
        # Unicode/codepoint offsets and regex boundaries are part of parity too.
        rows.extend({'title': title, 'tags': tags} for title, tags in [
            ('😀 !rubinot', []), ('não jogo RubinOT, só Antica', []),
            ('Tibia Global vs RubinOT', []), ('WAR?? KKKK | !rubinot', ['Português']),
            ('FutureOT', []), ('playing Feruots & Retronic', []), ('TSBot', []), ('TRIMERA 7.4 LAUNCH SOON', []),
            ('DARKORIA 8.60 OPEN BETA', []), ('Olympic74.com', []), ('!Ts /!moedaz !pix !exitlag #tsxhost.com', []),
            ('Examplegame74.com.br', []), ('Padventures - Event Halloween', ['PAD','PadventuresDiamond','Español']),
            ('Olympic Tibia 7.4', ['Gaming4Fun','VenezuelaStreamer']),
            ('olympic tibia 7.4', []), ('OLYMPIC TIBIA 7.4', []),
            ('Hunt Tibia 7.4', []), ('Global Tibia 7.4', []), ('Hunt 7.4', []),
            ('😀 hunt bosses', ['Português']), ('R U B I N O T', ['RUBINIOT']),
            ('xРubinOTy', []), ('aRubinOTz', []), ('50 TC / mês !rubinot', []),
        ])
        script = """
require('./extension/src/tibia-evidence.js');
require('./extension/src/tibia-classify.js');
let text = ''; process.stdin.on('data', d => text += d);
process.stdin.on('end', () => {
 const classify = TwitchCleanTibiaClassify.create(TWITCH_CLEAN_TIBIA_EVIDENCE);
 console.log(JSON.stringify(JSON.parse(text).map(r => classify(r.title, r.tags))));
});
"""
        actual = json.loads(subprocess.run(['node', '-e', script], input=json.dumps(rows),
            capture_output=True, text=True, cwd=ROOT, check=True).stdout)
        model = PrivateModel.load(ROOT / 'research/twitch/model/private-span-model.json')
        for row, js in zip(rows, actual):
            py = model.predict(row['title'], row['tags'])
            with self.subTest(title=row['title']):
                for key in ['references', 'contributions', 'raw_logit', 'hide']:
                    self.assertEqual(js[key], py[key], key)
                for key in ['private_probability', 'display_probability']:
                    self.assertAlmostEqual(js[key], py[key], places=15)
