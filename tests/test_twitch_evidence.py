import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from twitch_evidence import AUDIT, AUDIT_TIBIA, EVIDENCE, EXTENSION_DATA, Evidence, extension_data
EV = Evidence(json.loads(EVIDENCE.read_text()))

def audit_rows():
    for row in json.loads(AUDIT.read_text())['classificacao']:
        yield (row, [t.strip() for t in row['tags_originais'].split('|') if t.strip()])

class EvidenceTests(unittest.TestCase):

    def test_declared_server_or_tag_hides(self):
        self.assertEqual(EV.classify('[RUBINOT] war', [])[0], 'other')
        self.assertEqual(EV.classify('borA >>> farm', ['rubinot', 'Tibia'])[0], 'other')
        self.assertEqual(EV.classify('Infernum 2 war', [])[0], 'other')

    def test_chat_command_alone_does_not_hide(self):
        self.assertEqual(EV.classify('EK 2500 !rubinot !pix', ['Tibia'])[0], 'undetermined')
        self.assertEqual(EV.classify('O BEM SEMPRE VENCE ❗soe ❗rubinot', [])[0], 'undetermined')

    def test_official_world_keeps_and_generic_tibia_tag_does_not(self):
        self.assertEqual(EV.classify('EK 1k', ['Inabra'])[0], 'tibia')
        self.assertEqual(EV.classify('EK 1k', ['Tibia'])[0], 'undetermined')
        self.assertEqual(EV.classify('bom dia galera', [])[0], 'undetermined')

    def test_mixed_evidence_stays_visible(self):
        self.assertEqual(EV.classify('RubinOT RP', ['tibiaglobal'])[0], 'undetermined')

    def test_audit_hides_no_official_stream(self):
        for row, tags in audit_rows():
            if row['categoria'] in AUDIT_TIBIA:
                self.assertNotEqual(EV.classify(row['titulo_original'], tags)[0], 'other', row['canal'])

    def test_extension_classifier_matches_python(self):
        js = json.loads(subprocess.run(['node', str(ROOT / 'tests/twitch-classify.cjs')], check=True, capture_output=True, text=True).stdout)
        for row, tags in audit_rows():
            self.assertEqual(js[row['canal']], EV.classify(row['titulo_original'], tags)[0], row['canal'])

    def test_extension_evidence_copy_is_current(self):
        self.assertEqual(EXTENSION_DATA.read_text(), extension_data(json.loads(EVIDENCE.read_text())))
