"""Fit the reviewed private-evidence model; evaluate a frozen split separately.

Training requires NumPy; inference and dataset loading use the standard library.
The fixed seed and model configuration precede held-out evaluation. No test-row
text/labels enter reference discovery, fitting, calibration or threshold choice.
"""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from tibia_private import BASE, FEATURES, PrivateModel, context_features, learn_references
from tibia_private_data import ROOT, ANNOTATIONS, load_rows, partitions

OUT = ROOT / 'research/twitch/model'
MODEL = OUT / 'private-model.json'


def sigmoid(x):
    import numpy as np
    return 1 / (1 + np.exp(-np.clip(x, -40, 40)))


def fit_weights(rows, inventory):
    import numpy as np
    X = np.array([[context_features(r['title'], r['tags'], inventory)[0][f] for f in FEATURES] for r in rows])
    y = np.array([r['target'] for r in rows])
    active = (X[:, 0] != 0).astype(float)
    A = X[[r.get('model_supervision', {}).get('kind') == 'mixed_session' for r in rows]]
    B = X[[r.get('model_supervision', {}).get('kind') == 'no_private_server_evidence' and bool(X[i, 0]) for i, r in enumerate(rows)]]
    cap = math.log(BASE / (1 - BASE))
    w = np.zeros(len(FEATURES))
    # Weak ridge limits sparse-context separation. All rows remain in the loss:
    # no-reference rows have constant prediction 0.01 and zero parameter gradient.
    for _ in range(150):
        p = np.where(active, sigmoid(X @ w), BASE)
        gradient = X.T @ ((p - y) * active) + 0.005 * w
        hessian = (X.T * (p * (1 - p) * active)) @ X + 0.005 * np.eye(len(w))
        if len(B):
            excess = np.maximum(0, B @ w - cap)
            gradient += 100 * B.T @ excess
            violated = B[excess > 0]
            hessian += 100 * violated.T @ violated
        if len(A):
            # Explicit fractional labels impose their supplied log-odds (0 at .5),
            # without a per-input inference override. Temperature preserves .5.
            kkt = np.block([[hessian, A.T], [A, np.zeros((len(A), len(A)))]])
            delta = np.linalg.lstsq(kkt, np.r_[gradient, A @ w], rcond=None)[0][:len(w)]
        else:
            delta = np.linalg.solve(hessian, gradient)
        w -= delta * min(1, 5 / max(5, float(np.linalg.norm(delta))))
        if float(np.linalg.norm(delta)) < 1e-8:
            break
    return dict(zip(FEATURES, map(float, w)))


def temperature(model, rows, minimum_slope):
    # A single monotone scale is preferable to a highly flexible calibrator at
    # this sample size; .5 mixed targets and the hard .01 no-reference gate stay fixed.
    samples = [(model.predict(r['title'], r['tags'])['raw_logit'], r['target']) for r in rows]
    samples = [(z, y) for z, y in samples if z is not None]
    slope = 1.0
    for _ in range(100):
        gradient, hessian = 0.05 * (slope - 1), 0.05
        for z, y in samples:
            p = 1 / (1 + math.exp(-max(-40, min(40, slope * z))))
            gradient += (p - y) * z
            hessian += p * (1 - p) * z * z
        new = max(minimum_slope, min(10, slope - gradient / hessian))
        if abs(new - slope) < 1e-9:
            break
        slope = new
    return {'method': 'temperature', 'slope': slope, 'intercept': 0.0, 'active_calibration_rows': len(samples)}


def fit():
    rows = load_rows(); split = partitions(rows)
    source_rows = json.loads((ROOT / 'research/twitch/rebuild/sources.json').read_text())['sources']
    inventory = learn_references(split['train'], {r['id']: r for r in source_rows})
    data = {'format': 'entity-context-logit-v1', 'base_private_probability': BASE,
            'references': inventory, 'weights': fit_weights(split['train'], inventory),
            'calibration': {'slope': 1.0, 'intercept': 0.0}, 'hide_threshold': 0.95,
            'training': {'annotations_sha256': hashlib.sha256(ANNOTATIONS.read_bytes()).hexdigest(),
                         'seed': 23102026, 'ridge': 0.005,
                         'split': {name: [r['id'] for r in subset] for name, subset in split.items()},
                         'groups': {r['id']: r['group'] for r in rows},
                         'policy': 'All reviewed examples retained. Constructed/historical/user controls are training only. Channel, normalized title template, contrast and parent groups are disjoint across partitions.'}}
    model = PrivateModel(data)
    baseline_logits = [model.predict(r['title'], r['tags'])['raw_logit'] for r in split['train'] if r.get('model_supervision', {}).get('kind') == 'no_private_server_evidence']
    baseline_logits = [z for z in baseline_logits if z is not None]
    if any(z >= 0 for z in baseline_logits):
        raise ValueError('No-evidence training constraint not satisfied')
    minimum_slope = max([0.01] + [math.log(BASE / (1 - BASE)) / z for z in baseline_logits]) + 1e-10
    data['calibration'] = temperature(model, split['calibration'], minimum_slope)
    data['calibration']['minimum_slope_from_training_baseline'] = minimum_slope
    negatives = [model.predict(r['title'], r['tags'])['private_probability'] for r in split['calibration'] if r['proposed_stream_private'] == 'not_private']
    data['hide_threshold'] = max(0.95, math.nextafter(max(negatives, default=0), 1.0))
    MODEL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    # This command intentionally does not infer on test data.
    print(json.dumps({'split_rows': {k: len(v) for k, v in split.items()},
                      'calibration': data['calibration'], 'hide_threshold': data['hide_threshold'],
                      'acceptance': acceptance(model)}, ensure_ascii=False, indent=2))


def acceptance(model):
    rows = {r['id']: r for r in load_rows()}
    fixture = ROOT / 'tests/data/tibia-private-context-acceptance.json'
    cases = json.loads(fixture.read_text())['cases'] + json.loads((ROOT / 'tests/data/tibia-mixed-context-acceptance.json').read_text())['cases']
    baseline = json.loads((ROOT / 'tests/data/tibia-no-private-evidence-acceptance.json').read_text())
    outputs = {c['id']: model.predict(c['title'], c['tags'])['private_probability'] for c in cases}
    outputs.update({i: model.predict(rows[i]['title'], rows[i]['tags'])['private_probability'] for i in baseline['annotation_ids']})
    checks = {c['id']: c['private_probability_min'] <= outputs[c['id']] <= c['private_probability_max'] for c in cases}
    checks['no_evidence_all_at_base'] = all(abs(outputs[i] - BASE) < 1e-12 for i in baseline['annotation_ids'])
    checks['language_invariance'] = all(model.predict(r['title'], r['tags'])['private_probability'] == model.predict(r['title'], r['tags'] + [tag])['private_probability'] for r in rows.values() for tag in ['Português', 'English', 'Español', 'Polski'])
    checks['generic_gameplay'] = all(model.predict(title, ['Português'])['private_probability'] == BASE for title in ['hunt bosses', 'hunt de EK', 'bosses loot quest', '!pix !hunt !comandos', 'farm 24h', 'Medicina e Tibia'])
    return {'checks': checks, 'probabilities': outputs}


def metrics(items, probability_key='private_probability'):
    known = [i for i in items if i['truth'] in {'private', 'not_private'}]
    private = [i for i in known if i['truth'] == 'private']
    negative = [i for i in known if i['truth'] == 'not_private']
    brier = sum((i[probability_key] - (i['truth'] == 'private')) ** 2 for i in known) / max(1, len(known))
    loss = -sum(math.log(max(1e-12, min(1-1e-12, i[probability_key] if i['truth']=='private' else 1-i[probability_key]))) for i in known) / max(1, len(known))
    bins = []
    for low, high in [(0, .1), (.1, .5), (.5, .9), (.9, 1.000001)]:
        bucket = [i for i in known if low <= i[probability_key] < high]
        if bucket:
            bins.append({'range': [low, min(high, 1)], 'n': len(bucket), 'mean_probability': sum(i[probability_key] for i in bucket)/len(bucket), 'fraction_private': sum(i['truth']=='private' for i in bucket)/len(bucket)})
    return {'private_caught': sum(i['hide'] for i in private), 'private_total': len(private),
            'non_private_wrongly_flagged': sum(i['hide'] for i in negative), 'non_private_total': len(negative),
            'brier': brier, 'log_loss': loss, 'calibration_bins': bins,
            'ece': sum(b['n']*abs(b['mean_probability']-b['fraction_private']) for b in bins)/max(1,len(known)),
            'no_evidence_rows': sum(i['truth'] is None for i in items)}


def evaluate():
    data = json.loads(MODEL.read_text()); model = PrivateModel(data); rows = {r['id']: r for r in load_rows()}
    if hashlib.sha256(ANNOTATIONS.read_bytes()).hexdigest() != data['training']['annotations_sha256']:
        raise ValueError('Annotations changed since model fitting')
    groups = data['training']['groups']; splits = data['training']['split']
    group_sets = [{groups[i] for i in subset} for subset in splits.values()]
    for n, group in enumerate(group_sets):
        if any(group & other for other in group_sets[n+1:]):
            raise ValueError('Split leakage')
    predictions = []
    for identifier in splits['test']:
        r = rows[identifier]; out = model.predict(r['title'], r['tags'])
        predictions.append({'id': identifier, 'group': groups[identifier], 'truth': r['proposed_stream_private'],
                            'supervision': r['target'], **out})
    result = {'split_rows': {k: len(v) for k, v in splits.items()},
              'held_out': metrics(predictions), 'acceptance': acceptance(model),
              'weights': sorted(data['weights'].items(), key=lambda v: -v[1]),
              'recognition_anchors': data['references'], 'test_predictions': predictions}
    (OUT / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['split_rows','held_out','acceptance','weights']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['fit','evaluate']); args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    fit() if args.action == 'fit' else evaluate()
