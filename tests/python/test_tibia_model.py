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
                result = model.cross_validate(rows, folds=2)
        self.assertEqual(len(result), len(rows))


if __name__ == '__main__':
    unittest.main()
