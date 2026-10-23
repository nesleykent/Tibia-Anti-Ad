"""Experiment integrity: no fitting or hard-coded dataset totals."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from tibia_private import FEATURES, PrivateModel, learn_references
from tibia_private_data import load_rows, partitions


class ExperimentIntegrityTests(unittest.TestCase):
    def test_grouped_partitions_and_all_reviewed_examples_are_retained(self):
        rows = load_rows()
        model = PrivateModel.load(ROOT / 'research/twitch/model/private-model.json').data
        split = partitions(rows, model['training']['seed'], promote_test=model['training'].get('previous_test_promoted_to_development', False))
        ids = [{r['id'] for r in subset} for subset in split.values()]
        self.assertEqual(set.union(*ids), {r['id'] for r in rows})
        for i, subset in enumerate(ids):
            for other in ids[i+1:]:
                self.assertFalse(subset & other)
        groups = [{r['group'] for r in subset} for subset in split.values()]
        for i, subset in enumerate(groups):
            for other in groups[i+1:]:
                self.assertFalse(subset & other)
        for name, subset in split.items():
            self.assertEqual([r['id'] for r in subset], model['training']['split'][name])

    def test_identity_inventory_is_derived_from_training_only(self):
        model = PrivateModel.load(ROOT / 'research/twitch/model/private-model.json').data
        rows = {r['id']: r for r in load_rows()}
        sources = json.loads((ROOT / 'research/twitch/rebuild/sources.json').read_text())['sources']
        inventory = learn_references([rows[i] for i in model['training']['split']['train']], {s['id']: s for s in sources})
        self.assertEqual(inventory, model['references'])
        self.assertEqual(set(model['weights']), set(FEATURES))

    def test_development_regression_is_explicit_and_matches_inference(self):
        model = PrivateModel.load(ROOT / 'research/twitch/model/private-model.json')
        results = json.loads((ROOT / 'research/twitch/model/results.json').read_text())
        rows = {r['id']: r for r in load_rows()}
        self.assertEqual({r['id'] for r in results['test_predictions']}, set(model.data['training']['split']['test']))
        self.assertIsNone(results['held_out'])
        self.assertTrue(results['evaluation_status'])
        self.assertEqual({r['id'] for r in results['development_regression_predictions']}, set(model.data['training']['split']['development']))
        for expected in results['development_regression_predictions']:
            row = rows[expected['id']]
            self.assertEqual(model.predict(row['title'], row['tags'])['private_probability'], expected['private_probability'])
            self.assertEqual(row['proposed_stream_private'], expected['truth'])

    def test_reference_names_generalize_to_unseen_ot_names(self):
        model = PrivateModel.load(ROOT / 'research/twitch/model/private-model.json')
        reference = 'NeverSeenExampleOT'
        self.assertNotIn(reference.lower(), model.data['references']['aliases'])
        self.assertGreater(model.predict(reference)['private_probability'], 0.5)


if __name__ == '__main__':
    unittest.main()
