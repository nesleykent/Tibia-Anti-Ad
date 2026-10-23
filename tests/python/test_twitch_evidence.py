"""Numeric acceptance tests against the frozen milestone-B model and reviewed truth."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from tibia_private import BASE, PrivateModel
from tibia_private_data import load_rows

MODEL = PrivateModel.load(ROOT / 'research/twitch/model/private-model.json')
ROWS = {r['id']: r for r in load_rows()}


class PrivateProbabilityTests(unittest.TestCase):
    def test_context_and_mixed_acceptance_fixtures(self):
        for name in ['tibia-private-context-acceptance.json', 'tibia-mixed-context-acceptance.json']:
            for case in json.loads((ROOT / 'tests/data' / name).read_text())['cases']:
                with self.subTest(case=case['id']):
                    p = MODEL.predict(case['title'], case['tags'])['private_probability']
                    self.assertGreaterEqual(p, case['private_probability_min'])
                    self.assertLessEqual(p, case['private_probability_max'])

    def test_every_reviewed_no_evidence_input_stays_at_base(self):
        fixture = json.loads((ROOT / 'tests/data/tibia-no-private-evidence-acceptance.json').read_text())
        for identifier in fixture['annotation_ids']:
            row = ROWS[identifier]
            self.assertEqual(MODEL.predict(row['title'], row['tags'])['private_probability'], fixture['expected_private_probability'], identifier)

    def test_generic_gameplay_and_commands_do_not_supply_evidence(self):
        for title in ['hunt bosses', 'hunt de EK', 'bosses loot quest', 'farm 24h', '!pix !hunt !comandos', 'Global!', 'Medicina e Tibia']:
            result = MODEL.predict(title, ['Português'])
            self.assertEqual(result['private_probability'], BASE, title)
            self.assertEqual(result['references'], [], title)

    def test_adding_or_removing_language_tags_never_changes_probability(self):
        languages = ['Português', 'English', 'Español', 'Polski', 'PortuguêsBR', 'German']
        for row in ROWS.values():
            tags = [t for t in row['tags'] if t not in languages]
            expected = MODEL.predict(row['title'], tags)['private_probability']
            for language in languages:
                self.assertEqual(MODEL.predict(row['title'], tags + [language])['private_probability'], expected, (row['id'], language))

    def test_tag_order_and_duplicates_do_not_change_probability(self):
        for row in ROWS.values():
            self.assertEqual(MODEL.predict(row['title'], row['tags']), MODEL.predict(row['title'], list(reversed(row['tags'])) + row['tags']))

    def test_historical_fixture_is_only_an_index_to_reviewed_annotations(self):
        fixture = json.loads((ROOT / 'tests/data/tibia-classify-cases.json').read_text())
        for reference in fixture['cases']:
            self.assertEqual(set(reference), {'annotation_id'})
            self.assertIn('input', ROWS[reference['annotation_id']])


if __name__ == '__main__':
    unittest.main()
