"""Check new Python/JS inference outputs against the context acceptance contract.

Usage: python3 research/twitch/rebuild/check_context_acceptance.py predictions.json
The input maps each fixture id to its inferred P(private server). This checker
never trains a model. Passing it is an acceptance result, not held-out metrics.
Both runtimes must run the exact fixture title/tags and submit their own outputs.
"""
import json
import math
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[3] / 'tests/data/tibia-private-context-acceptance.json'


def check(predictions):
    cases = json.loads(FIXTURES.read_text())['cases']
    if set(predictions) != {case['id'] for case in cases}:
        raise AssertionError('Predictions must cover exactly the context acceptance cases')
    for case in cases:
        probability = predictions[case['id']]
        if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not math.isfinite(probability):
            raise AssertionError(f"{case['id']}: invalid probability")
        if not case['private_probability_min'] <= probability <= case['private_probability_max']:
            raise AssertionError(f"{case['id']}: P(private)={probability} outside acceptance bounds")
    print('PASS both context-dependent private-probability acceptance cases')


if __name__ == '__main__':
    check(json.loads(Path(sys.argv[1]).read_text()))
