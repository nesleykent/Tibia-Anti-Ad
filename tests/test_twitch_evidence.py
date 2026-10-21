import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from twitch_evidence import EVIDENCE, Evidence
EV = Evidence(json.loads(EVIDENCE.read_text()))

class EvidenceTests(unittest.TestCase):

    def test_ot_client_ui_wins_over_official_text(self):
        verdict, _, _ = EV.classify('King Aslan Global', [], 'Skills Map View Store')
        self.assertEqual(verdict, 'other')

    def test_sponsor_command_with_tibia_client_stays_visible(self):
        self.assertEqual(EV.classify('EK 2500 !rubinot', [], 'Skills Hunt Analyser Stamina')[0], 'undetermined')
        self.assertEqual(EV.classify('[RUBINOT] war !rubinot', [], 'Skills Stamina')[0], 'other')

    def test_extension_evidence_copy_is_current(self):
        from twitch_evidence import EXTENSION_DATA, extension_data
        self.assertEqual(EXTENSION_DATA.read_text(), extension_data(json.loads(EVIDENCE.read_text())))

    def test_other_game_without_tibia_client(self):
        self.assertEqual(EV.classify('[PXG] Jogando Rankeds', [], 'Pokemon Bag Batalha')[0], 'other')

    def test_official_needs_text_and_client(self):
        self.assertEqual(EV.classify('Tibia Global Serdebra EK', [], 'Skills Stamina Prey')[0], 'tibia')
        self.assertEqual(EV.classify('Tibia Global Serdebra EK', [])[0], 'undetermined')

    def test_live_sample_hides_no_official_marked_stream(self):
        data = ROOT / 'research/twitch/data/2026-10-21/live-2015'
        for row in json.loads((data / 'verdicts.json').read_text()):
            if row['verdict'] == 'other':
                self.assertFalse(row['evidence']['official_text'], row['channel'])
