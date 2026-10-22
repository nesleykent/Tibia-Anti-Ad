import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from twitch_evidence import AUDIT, AUDIT_TIBIA, EVIDENCE, EXTENSION_DATA, Evidence, extension_data
EV = Evidence(json.loads(EVIDENCE.read_text()))
CASES = ROOT / 'tests/data/tibia-classify-cases.json'

def audit_rows():
    for row in json.loads(AUDIT.read_text())['classificacao']:
        yield (row, [t.strip() for t in row['tags_originais'].split('|') if t.strip()])

class EvidenceTests(unittest.TestCase):

    def test_declared_server_or_tag_hides(self):
        self.assertEqual(EV.classify('[RUBINOT] war', [])[0], 'other')
        self.assertEqual(EV.classify('borA >>> farm', ['rubinot', 'Tibia'])[0], 'other')
        self.assertEqual(EV.classify('Infernum 2 war', [])[0], 'other')

    def test_chat_command_names_the_server(self):
        self.assertEqual(EV.classify('EK 2500 !rubinot !pix', ['Tibia'])[0], 'other')
        self.assertEqual(EV.classify('O BEM SEMPRE VENCE ❗soe ❗rubinot', [])[0], 'other')
        self.assertEqual(EV.classify('Tibia Global Etebra !rubinot', [])[0], 'tibia')

    def test_official_world_keeps_and_generic_tibia_tag_does_not(self):
        self.assertEqual(EV.classify('EK 1k', ['Inabra'])[0], 'tibia')
        self.assertEqual(EV.classify('EK 1k', ['Tibia'])[0], 'undetermined')
        self.assertEqual(EV.classify('bom dia galera', [])[0], 'undetermined')

    def test_title_outranks_tags(self):
        self.assertEqual(EV.classify('King Aslan - farm', ['tibiaglobal', 'global'])[0], 'other')
        self.assertEqual(EV.classify('paulistinhaot.com ON', ['lutabra'])[0], 'other')
        self.assertEqual(EV.classify('RASTEIBRA monk do 0', ['rubinot'])[0], 'undetermined')
        self.assertEqual(EV.classify('Global! de 0 a 500', ['rubinot'])[0], 'undetermined')

    def test_ambiguous_world_in_brackets_and_boss_tag(self):
        self.assertEqual(EV.classify('[CELEBRA - RP 1700+] !comandos', ['Bakragore'])[0], 'tibia')
        self.assertEqual(EV.classify('um newba !! PXG Magma', [])[0], 'other')

    def test_spelling_variants_normalize_to_the_server_name(self):
        for title in ('rubinot', 'RUBINOTTT', 'rub1n0t', 'r u b i n o t', 'ʀᴜʙɪɴᴏᴛ', '𝐫𝐮𝐛𝐢𝐧𝐨𝐭'):
            found = EV.classify(title, [])[2]['signals']
            self.assertEqual([(s['game'], s['distance']) for s in found if s['source'] == 'title'], [('RubinOT', 0)], title)

    def test_audit_hides_no_official_stream(self):
        for row, tags in audit_rows():
            if row['categoria'] in AUDIT_TIBIA:
                self.assertNotEqual(EV.classify(row['titulo_original'], tags)[0], 'other', row['canal'])

    def test_extension_evidence_copy_is_current(self):
        self.assertEqual(EXTENSION_DATA.read_text(), extension_data(json.loads(EVIDENCE.read_text())))
