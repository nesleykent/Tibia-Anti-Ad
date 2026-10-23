"""Fit the reviewed private-evidence model; evaluate a frozen split separately.

Training requires NumPy; inference and dataset loading use the standard library.
The former test is now development regression data after an error-driven fix.
Its rows remain excluded from fitting/calibration; post-fix results must not be
represented as a new independent held-out evaluation.
"""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from tibia_private import BASE, FEATURES, PrivateModel, context_features, learn_references, NONNEGATIVE, NONPOSITIVE
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
    locked = set()
    # Active constraints are chosen from coefficient signs, not example IDs.
    # Context can reduce evidence; an OT-name/command/domain cue cannot do so.
    for _active in range(len(FEATURES) + 1):
        equality = np.vstack([A, np.eye(len(w))[sorted(locked)]]) if locked else A
        for _ in range(150):
            p = np.where(active, sigmoid(X @ w), BASE)
            gradient = X.T @ ((p - y) * active) + 0.005 * w
            hessian = (X.T * (p * (1 - p) * active)) @ X + 0.005 * np.eye(len(w))
            if len(B):
                excess = np.maximum(0, B @ w - cap)
                gradient += 100 * B.T @ excess
                violated = B[excess > 0]
                hessian += 100 * violated.T @ violated
            if len(equality):
                kkt = np.block([[hessian, equality.T], [equality, np.zeros((len(equality), len(equality)))]] )
                delta = np.linalg.lstsq(kkt, np.r_[gradient, equality @ w], rcond=None)[0][:len(w)]
            else:
                delta = np.linalg.solve(hessian, gradient)
            w -= delta * min(1, 5 / max(5, float(np.linalg.norm(delta))))
            if float(np.linalg.norm(delta)) < 1e-8:
                break
        violated_signs = {i for i, name in enumerate(FEATURES)
                          if (name in NONNEGATIVE and w[i] < -1e-9) or (name in NONPOSITIVE and w[i] > 1e-9)}
        if not violated_signs - locked:
            break
        locked |= violated_signs
    for i in locked:
        w[i] = 0.0
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


THRESHOLD_GRID = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.975, 0.99, 0.995, 0.999)
FALSE_HIDE_COST = 50.0


def select_threshold(model, rows):
    # Fixed grid, one stated cost policy, aggregate group loss. No maximum
    # negative score, interpolation, nextafter, or per-stream exception.
    scores = [(r, model.predict(r['title'], r['tags'])['private_probability']) for r in rows
              if r['proposed_stream_private'] in {'private', 'not_private'}]
    candidates = []
    for threshold in THRESHOLD_GRID:
        losses = {}
        false, caught = 0, 0
        for row, probability in scores:
            private = row['proposed_stream_private'] == 'private'
            hide = probability >= threshold
            loss = FALSE_HIDE_COST if hide and not private else 1.0 if private and not hide else 0.0
            losses.setdefault(row['group'], []).append(loss)
            false += int(hide and not private)
            caught += int(hide and private)
        risk = sum(sum(v)/len(v) for v in losses.values()) / max(1, len(losses))
        candidates.append({'threshold': threshold, 'group_mean_cost': risk,
                           'non_private_flagged': false, 'private_caught': caught})
    policy_cutoff = FALSE_HIDE_COST / (FALSE_HIDE_COST + 1)
    selected = min(candidates, key=lambda r: (r['group_mean_cost'], r['threshold'] < policy_cutoff, abs(r['threshold'] - policy_cutoff)))
    return {'method': 'fixed-grid group-mean calibration cost', 'false_hide_cost': FALSE_HIDE_COST,
            'miss_cost': 1, 'tie_break_cost_cutoff': policy_cutoff,
            'tie_break': 'nearest grid value at or above the cost-ratio cutoff, among equal-risk choices',
            'minimum_risk_thresholds': [r['threshold'] for r in candidates if r['group_mean_cost'] == selected['group_mean_cost']],
            'calibration_groups': len({r['group'] for r, _ in scores}),
            'candidates': candidates, 'selected': selected['threshold']}


def fit():
    rows = load_rows(); split = partitions(rows, promote_test=True)
    source_rows = json.loads((ROOT / 'research/twitch/rebuild/sources.json').read_text())['sources']
    inventory = learn_references(split['train'], {r['id']: r for r in source_rows})
    data = {'format': 'entity-context-logit-v2', 'base_private_probability': BASE,
            'references': inventory, 'weights': fit_weights(split['train'], inventory),
            'calibration': {'slope': 1.0, 'intercept': 0.0}, 'hide_threshold': 0.95,
            'training': {'annotations_sha256': hashlib.sha256(ANNOTATIONS.read_bytes()).hexdigest(),
                         'seed': 23102026, 'ridge': 0.005, 'previous_test_promoted_to_development': True,
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
    data['threshold_selection'] = select_threshold(model, split['calibration'])
    data['hide_threshold'] = data['threshold_selection']['selected']
    MODEL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    # Acceptance/regression examples are explicitly development controls.
    print(json.dumps({'split_rows': {k: len(v) for k, v in split.items()},
                      'calibration': data['calibration'], 'hide_threshold': data['hide_threshold'],
                      'threshold_selection': data['threshold_selection'], 'acceptance': acceptance(model)}, ensure_ascii=False, indent=2))


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
    for identifier in splits['development']:
        r = rows[identifier]; out = model.predict(r['title'], r['tags'])
        predictions.append({'id': identifier, 'group': groups[identifier], 'truth': r['proposed_stream_private'],
                            'supervision': r['target'], **out})
    result = {'split_rows': {k: len(v) for k, v in splits.items()},
              'evaluation_status': 'Former test used for error-driven feature correction, now development regression only. These rows remain excluded from fitting and calibration; no untouched post-fix test is available.',
              'held_out': None, 'development_regression': metrics(predictions), 'acceptance': acceptance(model),
              'threshold_selection': data['threshold_selection'],
              'weights': sorted(data['weights'].items(), key=lambda v: -v[1]),
              'recognition_anchors': data['references'], 'test_predictions': [], 'development_regression_predictions': predictions}
    if not all(result['acceptance']['checks'].values()):
        raise ValueError('Acceptance probabilities failed')
    (OUT / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['split_rows','evaluation_status','development_regression','acceptance','weights']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['fit','evaluate']); args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    fit() if args.action == 'fit' else evaluate()
