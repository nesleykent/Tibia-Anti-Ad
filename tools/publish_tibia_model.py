"""Publish only verified model files, using a compare-and-swap GitHub ref update."""
import base64
import json
import os
import sys
from pathlib import Path
from tibia_learning import ROOT, StageError, request_json, required_secret

FILES=('research/twitch/model/private-span-model.json','filters/sources/twitch/tibia-evidence.json','extension/src/tibia-evidence.js')


def publish():
    token=required_secret('MODEL_PUBLISH_TOKEN')
    headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    repo=os.environ['GITHUB_REPOSITORY'];api='https://api.github.com/repos/'+repo
    staging=ROOT/'local/publication';base=(staging/'base-sha').read_text().strip()
    import re
    if not re.fullmatch('[0-9a-f]{40}',base):raise StageError('Invalid publication base')
    actual={p.relative_to(staging).as_posix() for p in staging.rglob('*') if p.is_file()}
    if actual!=set(FILES)|{'base-sha'}:raise StageError('Unexpected publication content')
    latest=request_json(api+'/git/ref/heads/main',headers)
    if latest['object']['sha']!=base:raise StageError('Main advanced after validation; publication cancelled')
    parent=request_json(api+'/git/commits/'+base,headers)
    tree=[]
    for name in FILES:
        blob=request_json(api+'/git/blobs',headers,{'content':base64.b64encode((staging/name).read_bytes()).decode(),'encoding':'base64'})
        tree.append({'path':name,'mode':'100644','type':'blob','sha':blob['sha']})
    result=request_json(api+'/git/trees',headers,{'base_tree':parent['tree']['sha'],'tree':tree})
    if result['sha']==parent['tree']['sha']:
        print('Published model already current');return
    commit=request_json(api+'/git/commits',headers,{'message':'Update learned Tibia identifier model after acceptance gates','tree':result['sha'],'parents':[base]})
    # Non-forced update is rejected if another writer moves main after the check.
    # PATCH is needed for refs, unlike the POST requests used for git objects.
    import urllib.request,urllib.error
    url=api+'/git/refs/heads/main'
    req=urllib.request.Request(url,data=json.dumps({'sha':commit['sha'],'force':False}).encode(),headers={**headers,'Content-Type':'application/json'},method='PATCH')
    try:
        with urllib.request.urlopen(req,timeout=60) as response:json.load(response)
    except (OSError,ValueError):raise StageError('Model publication rejected; main was not force-updated') from None
    print('Verified model published')


if __name__=='__main__':
    try:publish()
    except (StageError,OSError,ValueError,KeyError,TypeError) as error:
        print(str(error) if isinstance(error,StageError) else 'Publication validation failed',file=sys.stderr);raise SystemExit(1)
