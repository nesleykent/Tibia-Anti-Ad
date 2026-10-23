"""Server-neutral metadata must be mathematically inert."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from twitch_evidence import Evidence, EVIDENCE


class InvarianceTests(unittest.TestCase):
    def test_server_neutral_inputs_have_identical_outputs(self):
        classifier = Evidence(json.loads(EVIDENCE.read_text()))
        for title in ('', 'Tibia Global Antica', 'RubinOT'):
            original = classifier.classify(title, [])
            for neutral in ('hunt bosses', 'Português', 'English', 'Español', '!rubinot !deusot !hunt !pix', 'DROPS ON SHINY CATCH EVENT'):
                result = classifier.classify(title + ' ' + neutral, ['Português', 'English'])
                self.assertEqual(original[0], result[0])
                self.assertEqual(original[2]['score'], result[2]['score'])
