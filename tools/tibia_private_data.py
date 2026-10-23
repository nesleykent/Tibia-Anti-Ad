"""Load reviewed inputs/targets and create group-disjoint experimental partitions."""
import hashlib
import json
import random
import re
from collections import defaultdict
from pathlib import Path
from tibia_text import normalize

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS = ROOT / 'research/twitch/rebuild/annotation-proposals.json'


def load_rows():
    # Milestone-B authorization supersedes the historical A use_in_training gate;
    # actual fit/calibration/test membership is recorded in the exported model.
    packet = json.loads(ANNOTATIONS.read_text())
    sources = {}
    for key, name in packet['source_files'].items():
        if key == 'cases':
            continue  # inputs frozen in annotations; old fixture is now an index
        raw = json.loads((ROOT / name).read_text())
        if key == 'audit':
            sources[key] = raw['classificacao']
        else:
            sources[key] = raw.get('streams', raw) if isinstance(raw, dict) else raw
    by_id = {r['id']: r for r in packet['annotations']}
    def material(row):
        if 'parent_id' in row:
            title, tags, channel = material(by_id[row['parent_id']])
            return title, tags + [row['operation']['append_language_tag']], channel
        if 'input' in row:
            return row['input']['title'], row['input']['tags'], None
        if row['source_id'] in sources:
            raw = sources[row['source_id']][row['source_index']]
            if row['source_id'] == 'audit':
                return raw['titulo_original'], [x.strip() for x in raw['tags_originais'].split('|') if x.strip()], raw['canal']
            return raw['title'], raw.get('tags', []), raw.get('channel')
        return row['text'], row.get('tags', []), None
    rows = []
    for original in packet['annotations']:
        row = dict(original)
        row['title'], row['tags'], row['channel'] = material(row)
        if 'parent_id' in row:
            original_parent = by_id[row['parent_id']]
            for field in ['evidence_span', 'mentions', 'evidence_sources']:
                if field in original_parent:
                    row[field] = original_parent[field]
        if 'input_sha256' in row:
            digest = hashlib.sha256(json.dumps({'title': row['title'], 'tags': row['tags']}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            if digest != row['input_sha256']:
                raise ValueError('Input provenance mismatch: ' + row['id'])
        supervision = row.get('model_supervision', {})
        if supervision.get('kind') == 'no_private_server_evidence':
            row['target'] = 0.01
        elif 'private_evidence_target' in supervision:
            row['target'] = supervision['private_evidence_target']
        elif row['proposed_stream_private'] in {'private', 'not_private'}:
            row['target'] = float(row['proposed_stream_private'] == 'private')
        else:
            raise ValueError('Missing reviewed supervision: ' + row['id'])
        rows.append(row)
    return rows


def partitions(rows, seed=23102026, promote_test=False):
    parent = {r['id']: r['id'] for r in rows}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def union(a, b):
        parent[find(a)] = find(b)
    keys = {}
    for row in rows:
        group_keys = [('template', re.sub(r'\d+', '#', re.sub(r'[^a-z0-9]+', ' ', normalize(row['title']))).strip())]
        if row['channel']:
            group_keys.append(('channel', row['channel'].lower()))
        if row.get('contrast_group'):
            group_keys.append(('contrast', row['contrast_group']))
        if 'parent_id' in row:
            union(row['id'], row['parent_id'])
        for key in group_keys:
            if key in keys:
                union(row['id'], keys[key])
            keys[key] = row['id']
    groups = defaultdict(list)
    for row in rows:
        groups[find(row['id'])].append(row)
    split = dict(train=[], calibration=[], test=[])
    strata = defaultdict(list)
    for group in groups.values():
        if any(r['data_role'] != 'captured_metadata' or r.get('model_supervision', {}).get('kind') in {'no_private_server_evidence', 'mixed_session'} for r in group):
            split['train'].extend(group)
        else:
            labels = {r['proposed_stream_private'] for r in group}
            key = 'private' if 'private' in labels else 'negative' if 'not_private' in labels else 'baseline' if labels == {None} else 'mixed'
            strata[key].append(group)
    rng = random.Random(seed)
    for label, bucket in sorted(strata.items()):
        bucket.sort(key=lambda group: sorted(r['id'] for r in group))
        rng.shuffle(bucket)
        n = max(1, round(len(bucket) * 0.25)) if len(bucket) >= 3 else 0
        for name, chosen in [('test', bucket[:n]), ('calibration', bucket[n:2*n]), ('train', bucket[2*n:])]:
            for group in chosen:
                split[name].extend(group)
    if promote_test:
        for row in split['test']:
            row['previous_split'] = 'test'
        split['development'] = split.pop('test')
        split['test'] = []
    for name, subset in split.items():
        subset.sort(key=lambda row: row['id'])
        for row in subset:
            row['split'] = name
            row['group'] = hashlib.sha256('\n'.join(sorted(r['id'] for r in groups[find(row['id'])])).encode()).hexdigest()[:16]
    return split
