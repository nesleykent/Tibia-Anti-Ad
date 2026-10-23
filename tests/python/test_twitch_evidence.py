import json
import math
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from twitch_evidence import AUDIT, AUDIT_TIBIA, EVIDENCE, EXTENSION_DATA, Evidence, extension_data
from tibia_text import feature_fields
DATA = json.loads(EVIDENCE.read_text())
EV = Evidence(DATA)
CASES = ROOT / 'tests/data/tibia-classify-cases.json'

def audit_rows():
    for row in json.loads(AUDIT.read_text())['classificacao']:
        yield (row, [t.strip() for t in row['tags_originais'].split('|') if t.strip()])

class EvidenceTests(unittest.TestCase):

    def test_full_title_changes_the_result_with_identical_language_tags(self):
        official = EV.classify('Tibia Global Antica hunt bosses', ['Português'])
        other = EV.classify('DROPS ON SHINY CATCH EVENT', ['Português'])
        self.assertEqual(official[0], 'tibia')
        self.assertEqual(other[0], 'other')
        self.assertLess(official[2]['model']['title'], 0)
        self.assertGreater(other[2]['model']['title'], 0)
        self.assertNotEqual(other[2]['model']['tags'], 0)

    def test_both_fields_contribute_to_the_joint_logit(self):
        for title, tags in [('hunt bosses', ['pokemon']), ('Tibia Global', ['Português'])]:
            found = EV.classify(title, tags)[2]
            detail = found['model']
            self.assertNotEqual(detail['title'], 0)
            self.assertNotEqual(detail['tags'], 0)
            self.assertAlmostEqual(detail['logit'], detail['title'] + detail['tags'] + detail['bias'], places=5)
            self.assertTrue(all((s['source'] == 'model' for s in found['signals'])))

    def test_no_manual_name_or_channel_decision_tables_are_shipped(self):
        self.assertEqual(set(DATA), {'revision', '_comment', 'training', 'model'})
        self.assertEqual(DATA['model']['format'], 'joint-text-logistic-v1')
        self.assertTrue(DATA['model']['weights'])
        for key in DATA['model']['weights']:
            self.assertRegex(key, '^[0-9a-f]{8}$')
        a = EV.classify('hunt bosses', ['Português'], channel='anyone')
        b = EV.classify('hunt bosses', ['Português'], channel='rubinot')
        self.assertEqual(a, b)

    def test_duplicate_or_reordered_tags_do_not_count_twice(self):
        a = EV.classify('hunt bosses', ['Português', 'Tibia'])
        self.assertEqual(a, EV.classify('hunt bosses', ['Tibia', 'Português', 'Tibia']))

    def test_empty_and_out_of_vocabulary_text_abstain(self):
        for title, tags in [('', []), ('🦋', ['🎉']), ('qxzvkjqzzq', [])]:
            verdict, _, found = EV.classify(title, tags)
            self.assertEqual(verdict, 'undetermined')
            self.assertTrue(math.isfinite(found['score']['other']))

    def test_existing_official_and_ambiguous_controls_remain_visible(self):
        for case in json.loads(CASES.read_text())['cases']:
            if case['expect'] in ('tibia', 'undetermined'):
                self.assertNotEqual(EV.classify(case['title'], case.get('tags', []))[0], 'other', case['title'])

    def test_audit_hides_no_official_stream(self):
        for row, tags in audit_rows():
            if row['categoria'] in AUDIT_TIBIA:
                self.assertNotEqual(EV.classify(row['titulo_original'], tags)[0], 'other', row['canal'])

    def test_exported_feature_ids_match_browser_for_both_fields(self):
        samples = [['𝐓𝐢𝐛𝐢𝐚 2500 !hunt', ['Português', 'tibiaglobal']], ['abc-brandnew', ['abcbrandnew']], ['', []]]
        script = "require('./extension/src/tibia-classify.js'); console.log(JSON.stringify(" + json.dumps(samples) + '.map(([title,tags])=>TwitchCleanTibiaClassify.featureFields(title,tags).map(s=>[...s].sort()))));'
        js = json.loads(subprocess.run(['node', '-e', script], cwd=ROOT, check=True, capture_output=True, text=True).stdout)
        self.assertEqual(js, [[sorted(t), sorted(g)] for t, g in (feature_fields(*s) for s in samples)])

    def test_extension_evidence_copy_is_current(self):
        self.assertEqual(EXTENSION_DATA.read_text(), extension_data(DATA))
