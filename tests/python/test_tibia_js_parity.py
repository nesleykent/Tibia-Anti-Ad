"""Compare browser inference with the frozen Python model, without fitting."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from tibia_private import PrivateModel
from tibia_private_data import load_rows
from twitch_evidence import browser_data


class BrowserParityTests(unittest.TestCase):
    def test_export_and_all_reviewed_inputs(self):
        data = browser_data()
        self.assertEqual(json.loads((ROOT / 'filters/sources/twitch/tibia-evidence.json').read_text()), data)
        rows = [{'title': r['title'], 'tags': r['tags']} for r in load_rows()]
        # Unicode/codepoint offsets and regex boundaries are part of parity too.
        rows.extend({'title': title, 'tags': tags} for title, tags in [
            ('😀 !rubinot', []), ('não jogo RubinOT, só Antica', []),
            ('Tibia Global vs RubinOT', []), ('WAR?? KKKK | !rubinot', ['Português']),
            ('FutureOT', []), ('TRIMERA 7.4 LAUNCH SOON', []),
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
        model = PrivateModel.load(ROOT / 'research/twitch/model/private-model.json')
        for row, js in zip(rows, actual):
            py = model.predict(row['title'], row['tags'])
            with self.subTest(title=row['title']):
                for key in ['references', 'contributions', 'raw_logit', 'hide']:
                    self.assertEqual(js[key], py[key], key)
                for key in ['private_probability', 'display_probability']:
                    self.assertAlmostEqual(js[key], py[key], places=15)
