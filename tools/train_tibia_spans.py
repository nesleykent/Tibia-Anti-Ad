"""Fit only annotated identifier-span features; audit leave-one-server-out."""
import argparse
import hashlib
import json
from pathlib import Path
from tibia_spans import BASE, FEATURES, SpanModel, score, accepted, feature_bucket
from train_tibia_private import fit_weights, acceptance
ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / 'research/twitch/model/span-supervision.json'
MODEL = ROOT / 'research/twitch/model/private-span-model.json'
CHAR_RIDGE = 3e-05
STRUCTURE_RIDGE = 1e-05
ITERATIONS = 2000
STEP = 8

def fit_identifier(rows):
    import numpy as np
    examples = {}
    for row in rows:
        for c in row['candidates']:
            key = tuple(c['features'].items())
            examples[key] = max(examples.get(key, 0), int(c['positive']))
            if c['positive']:
                for variant in c.get('augmentations', []):
                    examples[tuple(variant.items())] = 1
    names = sorted({f for fs in examples for f, _ in fs})
    lookup = {f: i for i, f in enumerate(names)}
    rr, cc, vv = ([], [], [])
    for i, fs in enumerate(examples):
        for f, v in fs:
            rr.append(i)
            cc.append(lookup[f])
            vv.append(v)
    rr = np.array(rr)
    cc = np.array(cc)
    vv = np.array(vv)
    y = np.array(list(examples.values()), dtype=float)
    balance = np.where(y, 0.5 / max(1, sum(y)), 0.5 / max(1, len(y) - sum(y)))
    w = np.zeros(len(names))
    ridge = np.array([STRUCTURE_RIDGE if name.startswith('s:') else CHAR_RIDGE for name in names])
    for _ in range(ITERATIONS):
        z = np.bincount(rr, weights=vv * w[cc], minlength=len(y))
        p = 1 / (1 + np.exp(-np.clip(z, -40, 40)))
        g = np.bincount(cc, weights=vv * ((p - y) * balance)[rr], minlength=len(w)) + ridge * w
        w -= STEP * g
    return dict(zip(names, map(float, w)))

def vector(candidates):
    if not candidates:
        return dict.fromkeys(FEATURES, 0.0)
    values = {f: max((c['context'][f] for c in candidates)) for f in FEATURES}
    first = min((c for c in candidates if c['field'] == 'title'), key=lambda c: c['start'], default=None)
    for f in ('negated_reference', 'coordinated_reference', 'current_session_relation', 'separate_session_declaration'):
        values[f] = first['context'][f] if first else max((c['context'][f] for c in candidates))
    independent = any((c['field'] == 'tag' or c['kind'] != 'command' for c in candidates))
    if independent and (not values['sponsor_context']):
        values['commercial_context'] = values['commercial_offer'] = 0.0
    return values

def selected(row, model):
    return [c for c in row['candidates'] if accepted(c['features'], c['kind'], model)]

def probability(row, model):
    import math
    cs = selected(row, model)
    if not cs:
        return BASE
    x = vector(cs)
    z = sum((x[f] * model['weights'][f] for f in FEATURES))
    return max(BASE, 1 / (1 + math.exp(-max(-40, min(40, z)))))

def fit(rows):
    data = {'format': 'identifier-span-logit-v3', 'base_private_probability': BASE, 'identifier_weights': fit_identifier(rows), 'identifier_cutoffs': {}, 'fitting': {'character_ridge': CHAR_RIDGE, 'structure_ridge': STRUCTURE_RIDGE, 'iterations': ITERATIONS, 'step': STEP, 'cutoffs': 'training negative-only metadata maxima within identifier shape'}, 'weights': {}, 'hide_threshold': 0.95, 'calibration': {'slope': 1.0, 'intercept': 0.0}}
    for r in rows:
        if any((c['positive'] for c in r['candidates'])):
            continue
        for c in r['candidates']:
            key = feature_bucket(c['kind'], c['features'])
            data['identifier_cutoffs'][key] = max(data['identifier_cutoffs'].get(key, 0.0), score(c['features'], data['identifier_weights']) + 1e-08)
    matrix = [list(vector(selected(r, data)).values()) for r in rows]
    supervision = [{'target': r['target'], 'model_supervision': {'kind': r['supervision']}} for r in rows]
    data['weights'] = fit_weights(supervision, None, matrix, FEATURES)
    import math
    negatives = [sum((x[i] * data['weights'][f] for i, f in enumerate(FEATURES))) for x, r in zip(matrix, rows) if r['supervision'] == 'no_private_server_evidence' and x[0]]
    if any((z >= 0 for z in negatives)):
        raise ValueError('Inconsistent baseline constraints')
    slope = max([1.0] + [math.log(BASE / (1 - BASE)) / z for z in negatives]) + 1e-10
    data['weights'] = {f: w * slope for f, w in data['weights'].items()}
    return data

def holdout(rows, export_start, evaluation_rows=None):
    evaluation_rows = rows[export_start:] if evaluation_rows is None else evaluation_rows
    groups = sorted({g for r in evaluation_rows if r['private'] for g in r['groups']})
    results = []
    required = json.loads((ROOT / 'tests/data/tibia-span-heldout-acceptance.json').read_text())['cases']
    mandatory = []
    for group in groups:
        train = [r for r in rows if group not in r['groups'] and all((c['group'] != group for c in r['candidates']))]
        test = [r for r in evaluation_rows if r['private'] and group in r['groups']]
        if not train or not test:
            raise ValueError('Empty server holdout')
        try:
            model = fit(train)
        except ValueError as error:
            raise ValueError('Server fold ' + group + ': ' + str(error)) from None
        for case in required:
            if hashlib.sha256(case['server'].encode()).hexdigest() == group:
                mandatory.append({'server': group, 'flagged': SpanModel(model).predict(case['title'], case['tags'])['private_probability'] > 0.5})
        results.append({'server': group, 'train_rows': len(train), 'private_total': len(test), 'caught': sum((probability(r, model) > 0.5 for r in test))})
    return {'method': 'leave-one-server-identity-out; every matching historical and new example excluded before fit', 'mandatory': mandatory, 'folds': results, 'caught': sum((r['caught'] for r in results)), 'private_total': sum((r['private_total'] for r in results))}

def evaluate():
    model = SpanModel.load(MODEL)
    result = acceptance(model)
    if not all(result['checks'].values()):
        raise ValueError('Active identifier acceptance failed: ' + str(result['checks']))
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['fit', 'evaluate', 'holdout'])
    parser.add_argument('--data', type=Path, default=SEED)
    args = parser.parse_args()
    pack = json.loads(args.data.read_text())
    rows = pack['rows']
    if args.action == 'fit':
        data = fit(rows)
        data['revision'] = 5
        data['training'] = {'data_sha256': hashlib.sha256(args.data.read_bytes()).hexdigest(), 'rows': len(rows), 'features': 'candidate identifier characters and structure only; no channel, language or whole-title vocabulary'}
        MODEL.write_text(json.dumps(data, indent=2) + '\n')
        print('Identifier model fitted')
    elif args.action == 'evaluate':
        evaluate()
        print('Identifier acceptance passed')
    else:
        result = holdout(rows, pack['historical_count'])
        (ROOT / 'research/twitch/model/span-holdout.json').write_text(json.dumps(result, indent=2) + '\n')
        print('Server holdout evaluated')
if __name__ == '__main__':
    main()
