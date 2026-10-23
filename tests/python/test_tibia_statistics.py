"""The learned joint model, rather than a name rule, controls every verdict."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from twitch_evidence import Evidence
from tibia_text import feature_id


class StatisticalDecisionTests(unittest.TestCase):
    def test_piracy_evidence_is_not_diluted_by_uninformative_text(self):
        classifier = Evidence({'model': {'format': 'piracy-presence-logit-v1', 'bias': 0, 'threshold': 2,
            'weights': {feature_id('w:alpha'): [4, 1], feature_id('w:context'): [0, 100]}}})
        original = classifier.classify('alpha', [])
        longer = classifier.classify('alpha context', ['context'])
        self.assertEqual(original[0], 'other')
        self.assertEqual(original[2]['score'], longer[2]['score'])
        self.assertEqual(classifier.classify('context', [])[2]['score']['other'], 0.5)
        self.assertEqual(classifier.classify('unknown', [])[2]['score']['other'], 0.5)

    def test_a_model_with_no_learned_weights_cannot_ban_any_name(self):
        data = {'revision': 2, 'model': {'format': 'joint-text-logistic-v1', 'bias': 0,
                'threshold': 1, 'weights': {}}}
        classifier = Evidence(data)
        for title, tags in [('RubinOT', []), ('Tibia Global', ['rubinot']), ('anything', ['deusot'])]:
            self.assertEqual(classifier.classify(title, tags)[0], 'undetermined')

    def test_channel_names_never_affect_the_statistical_decision(self):
        data = {'revision': 2, 'model': {'format': 'joint-text-logistic-v1', 'bias': 0,
                'threshold': 1, 'weights': {}}}
        classifier = Evidence(copy.deepcopy(data))
        self.assertEqual(classifier.classify('stream', [], channel='rubinot'),
                         classifier.classify('stream', [], channel='anyone'))

    def test_identical_tags_and_a_different_title_change_the_decision(self):
        weights = {feature_id('w:alpha'): [-4, 1], feature_id('w:beta'): [4, 1]}
        classifier = Evidence({'model': {'format': 'joint-text-logistic-v1', 'bias': 0, 'threshold': 1, 'weights': weights}})
        self.assertEqual(classifier.classify('alpha', ['language'])[0], 'tibia')
        self.assertEqual(classifier.classify('beta', ['language'])[0], 'other')
        self.assertEqual(classifier.classify('alpha', ['beta'])[0], 'undetermined')
        self.assertEqual(classifier.classify('neutral', ['beta'])[0], 'other')
        found = classifier.classify('alpha', ['beta'])[2]['model']
        self.assertLess(found['title'], 0)
        self.assertGreater(found['tags'], 0)
        self.assertAlmostEqual(found['logit'], found['title'] + found['tags'], places=5)

    def test_learned_subwords_apply_to_unseen_whole_words_in_either_field(self):
        model = {'format': 'joint-text-logistic-v1', 'bias': 0, 'threshold': 1,
                 'weights': {feature_id('c:abc'): [4, 1]}}
        classifier = Evidence({'model': model})
        self.assertEqual(classifier.classify('abcbrandnew', [])[0], 'other')
        self.assertEqual(classifier.classify('', ['abcbrandnew'])[0], 'other')


if __name__ == '__main__':
    unittest.main()
