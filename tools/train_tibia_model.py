"""Fit a small supervised identity model, calibrate separately, evaluate once.

The frozen annotation overlay and group split are reviewable inputs. Training
never accesses test labels. Export does not refit on calibration/test channels.
No third-party runtime or training dependencies.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
from tibia_text import features
from twitch_evidence import AUDIT, EVIDENCE, Evidence, extension_data, EXTENSION_DATA

DIRECTORY = AUDIT.parents[3] / 'model'
L2 = 0.01  # Sum-loss penalty, weak regularization for six prespecified features.
OTHER_THRESHOLD = 0.98  # False hide costs 49x a missed other stream.
OFFICIAL_THRESHOLD = 0.10  # Visible positive attribution; abstention also stays visible.


def observations():
    audit = json.loads(AUDIT.read_text())['classificacao']
    overlay = json.loads((DIRECTORY / 'label-audit.json').read_text())
    if hashlib.sha256(AUDIT.read_bytes()).hexdigest() != overlay['source_sha256']:
        raise ValueError('Audit source changed; review labels again')
    assignments = json.loads((DIRECTORY / 'split.json').read_text())['assignments']
    return [{'id': a['id'], 'channel': row['canal'], 'title': row['titulo_original'],
             'tags': [t.strip() for t in row['tags_originais'].split('|') if t.strip()],
             'label': a['label'], 'split': assignments[a['id']]} for a, row in zip(overlay['rows'], audit, strict=True)]


def sigmoid(value):
    return 1 / (1 + math.exp(-max(-40, min(40, value))))


def optimize(rows, size, penalty):
    """Deterministic full-batch convex logistic sum loss with L2 regularization.

    No class balancing: calibration must reflect the sampled class prevalence.
    Bias is unpenalized. A conservative Lipschitz step ensures convergence.
    """
    weights = [0.0] * size
    step = 1 / (0.25 * sum(sum(x*x for x in values) for values, _ in rows) + penalty)
    for _ in range(30000):
        gradient = [0.0] + [penalty*w for w in weights[1:]]
        for values, label in rows:
            error = sigmoid(sum(v*w for v,w in zip(values,weights))) - label
            for j, value in enumerate(values):
                gradient[j] += error*value
        if max(abs(g) for g in gradient) < 1e-7:
            break
        weights = [w-step*g for w,g in zip(weights, gradient)]
    return weights


def fit(training, calibration, extractor):
    names = sorted(extractor['features'])
    vector = lambda row: [1.0] + [int(k in features(row['title'],row['tags'],extractor)) for k in names]
    base = optimize([(vector(r), r['label']) for r in training], len(names)+1, L2)
    raw = lambda row: sum(a*b for a,b in zip(vector(row),base))
    # Platt sigmoid fitted only on disjoint calibration groups. Weak regularization
    # prevents separation from yielding infinite odds in this small sample.
    intercept, slope = optimize([([1.0,raw(r)],r['label']) for r in calibration],2,0.1)
    if slope <= 0:
        raise ValueError('Calibration has reversed the evidence ranking')
    return {'format':'server-identity-logistic-v1','bias':round(intercept+slope*base[0],10),
            'weights':{k:round(slope*w,10) for k,w in zip(names,base[1:])},
            'official_threshold':OFFICIAL_THRESHOLD,'other_threshold':OTHER_THRESHOLD,
            'calibration':{'method':'disjoint-group Platt sigmoid, empirical prevalence, L2=0.1',
                           'intercept':intercept,'slope':slope},
            'uncalibrated':{'bias':base[0],'weights':dict(zip(names,base[1:]))}}


def wilson_interval(successes, total):
    if not total:
        return None
    z=1.959963984540054;p=successes/total;d=1+z*z/total
    center=(p+z*z/(2*total))/d
    radius=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [max(0,center-radius),min(1,center+radius)]


def metrics(rows, evidence):
    results=[]
    for row in rows:
        verdict,_,found=evidence.classify(row['title'],row['tags'])
        results.append((row['label'],verdict,found['score']['other']))
    bins=[]
    for lower in (0,0.2,0.4,0.6,0.8):
        subset=[(y,p) for y,_,p in results if lower<=p and (p<lower+0.2 or lower==0.8)]
        if subset:
            bins.append({'lower':lower,'n':len(subset),'mean_probability':sum(p for _,p in subset)/len(subset),
                         'observed_other':sum(y for y,_ in subset)/len(subset)})
    n=len(results);official=sum(y==0 for y,_,_ in results);other=n-official
    hidden_official=sum(y==0 and v=='other' for y,v,_ in results)
    hidden_other=sum(y==1 and v=='other' for y,v,_ in results)
    accepted=sum(v!='undetermined' for _,v,_ in results)
    wrong=sum((v=='other' and y==0) or (v=='tibia' and y==1) for y,v,_ in results)
    return {'n':n,'official':official,'other':other,'hidden_official':hidden_official,'hidden_other':hidden_other,
            'other_recall':hidden_other/other if other else None,
            'hide_precision':hidden_other/(hidden_other+hidden_official) if hidden_other+hidden_official else None,
            'hidden_official_rate_wilson95':wilson_interval(hidden_official,official),
            'abstained':n-accepted,'coverage':accepted/n,'selective_error':wrong/accepted if accepted else None,
            'brier':sum((p-y)**2 for y,_,p in results)/n,
            'log_loss':-sum(y*math.log(max(p,1e-6))+(1-y)*math.log(max(1-p,1e-6)) for y,_,p in results)/n,
            'ece_5_equal_width':sum(b['n']*abs(b['mean_probability']-b['observed_other']) for b in bins)/n,
            'reliability_bins':bins,
            'confusion':{f'{y}:{v}':sum(a==y and b==v for a,b,_ in results) for y in (0,1) for v in ('tibia','other','undetermined')}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    rows=observations();data=json.loads(EVIDENCE.read_text())
    labelled=[r for r in rows if r['label'] is not None]
    training=[r for r in labelled if r['split']=='train'];calibration=[r for r in labelled if r['split']=='calibration']
    model=fit(training,calibration,data['extractor'])
    data['model']=model
    data['training']={'target':'non-official stream versus official Tibia, including unrelated games',
                      'label_quality':'audited metadata-supported proxy labels, not verified active gameplay',
                      'observations':len(training),'calibration_observations':len(calibration),
                      'l2_sum_loss':L2,'features':'six prespecified server-identity types; no channel decisions',
                      'fit_ids':[r['id'] for r in training],'calibration_ids':[r['id'] for r in calibration],
                      'source_sha256':hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
                      'audit_sha256':hashlib.sha256((DIRECTORY/'label-audit.json').read_bytes()).hexdigest(),
                      'split_sha256':hashlib.sha256((DIRECTORY/'split.json').read_bytes()).hexdigest()}
    evidence=Evidence(data)
    test=[r for r in labelled if r['split']=='test']
    uncalibrated=json.loads(json.dumps(data));uncalibrated['model'].update(model['uncalibrated'])
    report={'evaluation':'Frozen channel/exact-metadata-group holdout; no refit after evaluation; retrospective same-day proxy labels',
            'composition':{split:{str(label):sum(r['split']==split and r['label']==label for r in rows) for label in (0,1,None)} for split in ('train','calibration','test')},
            'held_out':metrics(test,evidence),'held_out_uncalibrated':metrics(test,Evidence(uncalibrated)),
            'unresolved_test':dict(collections.Counter(evidence.classify(r['title'],r['tags'])[0] for r in rows if r['split']=='test' and r['label'] is None)),
            'signals':sorted(model['weights'].items(),key=lambda item:item[1]),
            'test_predictions':[{'id':r['id'],'label':r['label'],'verdict':evidence.classify(r['title'],r['tags'])[0],
                                 'p_other':evidence.classify(r['title'],r['tags'])[2]['score']['other']} for r in test]}
    if args.write:
        EVIDENCE.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');EXTENSION_DATA.write_text(extension_data(data))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('composition','held_out','signals')},indent=2))


if __name__=='__main__':
    main()
