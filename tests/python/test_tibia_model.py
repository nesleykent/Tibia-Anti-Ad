"""Calibration uses its reserved rows, without refitting the evidence model."""
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from tibia_private import PrivateModel
from tibia_private_data import load_rows
from train_tibia_private import temperature, select_threshold, THRESHOLD_GRID


class CalibrationTests(unittest.TestCase):
    def test_temperature_reproduces_export_from_calibration_rows_only(self):
        model = PrivateModel.load(ROOT / 'research/twitch/model/private-model.json')
        rows = {r['id']: r for r in load_rows()}
        selected = [rows[i] for i in model.data['training']['split']['calibration']]
        seen = []
        class TracedModel:
            def predict(self, title, tags):
                seen.append((title, tags))
                return model.predict(title, tags)
        fitted = temperature(TracedModel(), selected, model.data['calibration']['minimum_slope_from_training_baseline'])
        self.assertEqual(seen, [(r['title'], r['tags']) for r in selected])
        self.assertAlmostEqual(fitted['slope'], model.data['calibration']['slope'], places=10)

    def test_temperature_can_reduce_overconfidence_with_mixed_outcomes(self):
        class FixedModel:
            def predict(self, title, tags):
                return {'raw_logit': 10.0}
        calibration = temperature(FixedModel(), [{'title': '', 'tags': [], 'target': y} for y in [0, 1]], 0.01)
        self.assertGreater(calibration['slope'], 0)
        self.assertLess(calibration['slope'], 1)
        self.assertEqual(calibration['intercept'], 0)

    def test_threshold_uses_all_calibration_groups_and_fixed_grid(self):
        model = PrivateModel.load(ROOT / 'research/twitch/model/private-model.json')
        rows = {r['id']: r for r in load_rows()}
        for r in rows.values():
            r['group'] = model.data['training']['groups'][r['id']]
        selected = [rows[i] for i in model.data['training']['split']['calibration']]
        policy = select_threshold(model, selected)
        self.assertEqual(policy, model.data['threshold_selection'])
        self.assertEqual([r['threshold'] for r in policy['candidates']], list(THRESHOLD_GRID))
        self.assertEqual(policy['calibration_groups'], len({r['group'] for r in selected}))
        selected_cost = next(r['group_mean_cost'] for r in policy['candidates'] if r['threshold'] == policy['selected'])
        self.assertEqual(selected_cost, min(r['group_mean_cost'] for r in policy['candidates']))

    def test_export_parameters_are_finite(self):
        data = json.loads((ROOT / 'research/twitch/model/private-model.json').read_text())
        self.assertTrue(all(math.isfinite(w) for w in data['weights'].values()))
        self.assertGreater(data['hide_threshold'], data['base_private_probability'])
        self.assertLessEqual(data['hide_threshold'], 1)


if __name__ == '__main__':
    unittest.main()
