"""Metadata-only capture and agent-supervised train/gate stages. Never logs API bodies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from tibia_spans import candidates, span_features, context, augmentations, LEGACY_PROJECT
from train_tibia_spans import ROOT, SEED, MODEL, fit, probability, holdout, evaluate

WORK = ROOT / 'local/learning'


class StageError(RuntimeError):
    """A safe diagnostic that contains neither credentials nor remote response text."""


def request_json(url, headers=None, payload=None, form=False, timeout=90):
    body = urllib.parse.urlencode(payload).encode() if form else json.dumps(payload).encode() if payload is not None else None
    hdr = dict(headers or {})
    if body is not None:hdr['Content-Type'] = 'application/x-www-form-urlencoded' if form else 'application/json'
    for attempt in range(4):
        try:
            req=urllib.request.Request(url, data=body, headers=hdr)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            status=error.code
            error.close()
            if status not in {429,500,502,503,504} or attempt==3:
                raise StageError('API request failed (HTTP '+str(status)+')') from None
        except (OSError, ValueError):
            if attempt==3:raise StageError('API request failed or returned invalid JSON') from None
        time.sleep(min(30,2**attempt))
    raise StageError('API retry limit reached')


def required_secret(name):
    value=os.environ.get(name)
    if not value:raise StageError('Missing repository secret: '+name)
    return value


def capture():
    client=required_secret('TWITCH_CLIENT_ID')
    token=request_json('https://id.twitch.tv/oauth2/token',payload={'client_id':client,'client_secret':required_secret('TWITCH_CLIENT_SECRET'),'grant_type':'client_credentials'},form=True)
    if not token.get('access_token'):raise StageError('Twitch token missing')
    headers={'Client-ID':client,'Authorization':'Bearer '+token['access_token']}
    games=request_json('https://api.twitch.tv/helix/games?name=Tibia',headers)
    if len(games.get('data',[]))!=1:raise StageError('Tibia category not resolved uniquely')
    game=games['data'][0]['id'];after=None;seen=set();streams={}
    for _ in range(200):
        params={'game_id':game,'first':100}
        if after:params['after']=after
        page=request_json('https://api.twitch.tv/helix/streams?'+urllib.parse.urlencode(params),headers)
        if not isinstance(page.get('data'),list):raise StageError('Invalid Twitch streams response')
        for row in page['data']:
            if str(row.get('game_id'))!=str(game):raise StageError('Wrong category in capture')
            if not isinstance(row.get('title'),str) or not isinstance(row.get('tags'),list) or not all(isinstance(t,str) for t in row['tags']):raise StageError('Missing title/tags')
            streams[row['id']]={'title':row['title'],'tags':row['tags']}
        after=page.get('pagination',{}).get('cursor')
        if not after:break
        if after in seen:raise StageError('Repeated Twitch pagination cursor')
        seen.add(after)
    else:raise StageError('Twitch pagination exceeded bound')
    if not streams:raise StageError('Empty category capture')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    result={'captured_at':stamp,'source':'Twitch Helix Get Streams','category_id':game,'streams':list(streams.values())}
    (WORK/'captures').mkdir(parents=True,exist_ok=True)
    save(WORK/'captures'/f'{stamp}.json',result);save(WORK/'capture.json',result)


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=True,separators=(',',':'))+'\n')


def input_id(row):
    return hashlib.sha256(json.dumps({'title':row['title'],'tags':sorted(set(row['tags']))},ensure_ascii=True,sort_keys=True).encode()).hexdigest()


def refresh_augmentations(history):
    """Recompute structural features/views without changing source labels."""
    if history.get('augmentation_revision') == 4:
        return
    def legacy_features(features):
        return tuple((key, value) for key, value in features.items()
                     if not key.startswith(('s:protocol_adjacent:', 's:launch:protocol_adjacent:', 's:launch:protocol_length:', 's:protocol_suffix', 's:brand_tail:poke', 's:compound_stem_length:')))
    pending = {row['id']: row for row in history['rows']}
    for path in sorted((WORK / 'captures').glob('*.json')):
        for raw in json.loads(path.read_text())['streams']:
            row = pending.get(input_id(raw))
            if row is None:
                continue
            spans = {}
            # A longer protocol proposal can subsume an older capitalized
            # project span. Recover that annotated span from its source too;
            # migration must retain labels rather than invent a new annotation.
            source_spans = candidates(raw['title'], raw['tags'])
            source_spans += candidates(raw['title'], raw['tags'], project_pattern=LEGACY_PROJECT)
            for span in source_spans:
                spans.setdefault(legacy_features(span_features(span)), []).append(span)
            for candidate in row['candidates']:
                matches = [span for span in spans.get(legacy_features(candidate['features']), [])
                           if all(key not in candidate or candidate[key] == span[key] for key in ('kind', 'field', 'start'))]
                if not matches or any(span_features(span) != span_features(matches[0]) for span in matches[1:]):
                    raise StageError('Retained identifier feature provenance mismatch')
                span = matches[0]
                candidate['features'] = span_features(span)
                candidate['augmentations'] = augmentations(span, positive=candidate['positive'])
            del pending[row['id']]
    if pending:
        raise StageError('A retained label is missing its source capture')
    history['augmentation_revision'] = 4


def prepare():
    seed=json.loads(SEED.read_text());history=json.loads((WORK/'history.json').read_text())
    newest=json.loads((WORK/'newest.json').read_text())['rows'];ids={r['id'] for r in newest}
    train=[r for r in seed['rows'] if r.get('input_id',r['id']) not in ids]+[r for r in history['rows'] if r['id'] not in ids]
    provisional=fit(train)
    # Newest previously unseen metadata is never fitted before this check.
    errors=sum((probability(r,provisional)>.5)!=r['private'] for r in newest)
    report={'newest_rows':len(newest),'newest_errors':errors,'newest_used_in_provisional_training':False,'decisions_sha256':history['decisions_sha256']}
    save(WORK/'gate.json',report)
    if errors:raise StageError('Newest-capture held-out check failed')
    data=fit(seed['rows']+history['rows'])
    data['revision']=json.loads(MODEL.read_text())['revision']+1
    data['training']={'data_sha256':hashlib.sha256((WORK/'history.json').read_bytes()).hexdigest(),'rows':len(seed['rows'])+len(history['rows']),'rules_sha256':history['decisions_sha256']}
    save(MODEL,data)
    evaluate()
    # Refit each fold including scheduled history, removing every occurrence of
    # the held-out name from historical, seed and new rows before fitting.
    held=holdout(seed['rows']+history['rows'],seed['historical_count'],seed['rows'][seed['historical_count']:])
    if len(held['mandatory'])!=6 or not all(r['flagged'] for r in held['mandatory']):raise StageError('Server-name holdout acceptance failed')
    report['server_holdout']=held
    save(WORK/'gate.json',report)
    subprocess.run(['python3','tools/twitch_evidence.py','--write-js'],cwd=ROOT,check=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['capture','prepare']);args=parser.parse_args()
    try:
        globals()[args.stage]()
        print('Learning stage completed: '+args.stage)
    except (StageError,OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        # Exceptions from external services or subprocesses may contain raw data.
        message=str(error) if isinstance(error,StageError) else 'Learning stage failed validation'
        print(message,file=__import__('sys').stderr);raise SystemExit(1)

if __name__=='__main__':main()
