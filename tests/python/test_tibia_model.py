"""Prevent the same Twitch channel leaking between model training and evaluation."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import train_tibia_model as model


class ModelValidationTests(unittest.TestCase):
    def test_training_uses_audit_labels_not_filter_predictions(self):
        rows = model.observations()
        self.assertEqual(len(rows), 370)
        self.assertTrue(all(set(row) == {'channel', 'title', 'tags', 'label'} for row in rows))
        self.assertEqual(set(model.dataset()), {row['channel'] for row in rows})
        self.assertNotEqual(model.dataset('title'), model.dataset('tags'))

    def test_wilson_interval_does_not_claim_certainty_from_small_samples(self):
        self.assertIsNone(model.wilson_interval(0, 0))
        lower, upper = model.wilson_interval(10, 10)
        self.assertAlmostEqual(lower, 0.722467, places=5)
        self.assertAlmostEqual(upper, 1.0)
        lower, upper = model.wilson_interval(50, 100)
        self.assertAlmostEqual(lower, 0.403832, places=5)
        self.assertAlmostEqual(upper, 0.596168, places=5)

    def test_cross_validation_keeps_all_channel_captures_in_one_fold(self):
        rows = {
            'alice': ({'alice-audit'}, 1), 'live:alice': ({'alice-live'}, 1),
            'bob': ({'bob-audit'}, 0), 'live:bob': ({'bob-live'}, 0),
            'carol': ({'carol-audit'}, 1), 'live:carol': ({'carol-live'}, 1),
        }
        trained = []
        def train(training):
            trained[:] = [feature.split('-')[0] for features, _ in training for feature in features]
            return {}
        def score(_, features):
            channel = next(iter(features)).split('-')[0]
            self.assertNotIn(channel, trained, f'{channel} leaked from training into evaluation')
            return 0
        with patch.object(model, 'train', train), patch.object(model, 'score', score):
            with contextlib.redirect_stdout(io.StringIO()):
                result = model.cross_validate(rows, folds=2, calibrated=False)
        self.assertEqual(len(result), len(rows))

    def test_presence_rates_do_not_learn_absence_of_official_features(self):
        fitted = model.train([({'shared': 1, 'private': 1}, 1), ({'shared': 1, 'official': 1}, 0)])
        self.assertEqual(fitted['bias'], 0)
        self.assertEqual(model.score(fitted, {'shared': 1}), 0)
        self.assertEqual(model.score(fitted, {'unknown': 1}), 0)
        self.assertGreater(model.score(fitted, {'private': 1}), 0)
        self.assertLess(model.score(fitted, {'official': 1}), 0)
        self.assertEqual(model.score(fitted, {'private': 1}), model.score(fitted, {'private': 1, 'shared': 1}))

    def test_calibration_preserves_neutral_odds_and_reduces_overconfidence(self):
        slope = model.calibration_slope([(10, 1), (10, 0), (-10, 0), (-10, 1)])
        self.assertGreaterEqual(slope, 0)
        self.assertLess(slope, 1)

    def test_calibration_uses_inner_held_out_channels(self):
        rows = {f'channel{i}': ({str(i): 1}, i % 2) for i in range(12)}
        training_sets = []
        def train(training):
            names = {key for values, _ in training for key in values}
            training_sets.append(names)
            return {'weights': {}, 'training': names}
        def score(fitted, values):
            self.assertTrue(set(values).isdisjoint(fitted['training']))
            return 1
        with patch.object(model, 'train', train), patch.object(model, 'score', score):
            fitted = model.fit(rows)
        self.assertEqual(len(training_sets), model.CALIBRATION_FOLDS + 1)
        self.assertEqual(fitted['calibration']['method'], 'channel-cross-fitted-zero-intercept-logistic')


if __name__ == '__main__':
    unittest.main()
