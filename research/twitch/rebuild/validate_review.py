"""Validate the review packet's provenance and approval gate. Never fits a model."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = Path(__file__).resolve().parent


def main():
    packet = json.loads((DIRECTORY / 'annotation-proposals.json').read_text())
    sources = json.loads((DIRECTORY / 'sources.json').read_text())['sources']
    corpus = {}
    for source in sources:
        if 'path' not in source:
            continue
        path = ROOT / source['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'], source['id']
        raw = json.loads(path.read_text())
        corpus[source['id']] = raw['classificacao'] if source['id'] == 'audit' else raw['cases'] if source['id'] == 'cases' else raw
        assert len(corpus[source['id']]) == source['records']
    annotations = packet['annotations']
    assert len({row['id'] for row in annotations}) == len(annotations)
    known_sources = {row['id'] for row in sources}
    ids = {row['id'] for row in annotations}
    for row in annotations:
        assert row['source_id'] in known_sources, row['id']
        assert row['approval'] in {'pending', 'maintainer_confirmed'} and not row['use_in_training'], row['id']
        if row['approval'] == 'maintainer_confirmed':
            assert row['review_source'] in known_sources, row['id']
            assert next(source for source in sources if source['id'] == row['review_source'])['kind'] == 'explicit_maintainer_label_review'
        assert row['proposed_context'] in {'session', 'promotion', 'negation', 'comparison', 'unresolved', 'no_evidence'}
        assert row['proposed_stream_private'] in {'private', 'not_private', None}
        assert row['proposed_affirmative_private_evidence'] in {True, False, None}
        assert set(row.get('evidence_sources', [])) <= known_sources, row['id']
        assert row['reason']
        if row['source_id'] in corpus:
            original = corpus[row['source_id']][row['source_index']]
            title = original['titulo_original'] if row['source_id'] == 'audit' else original['title']
            tags = [t.strip() for t in original['tags_originais'].split('|') if t.strip()] if row['source_id'] == 'audit' else original.get('tags', [])
            digest = hashlib.sha256(json.dumps({'title': title, 'tags': tags}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            assert digest == row['input_sha256'], row['id']
            span = row['evidence_span']
            fields = [title] if span['field'] == 'title' else tags
            assert any(text[span['start']:span['end']] == span['text'] for text in fields), row['id']
            for mention in row.get('mentions', []):
                mention_fields = [title] if mention['field'] == 'title' else tags
                assert any(text[mention['start']:mention['end']] == mention['text'] for text in mention_fields), row['id']
            expected = original['categoria'] if row['source_id'] == 'audit' else original['expect'] if row['source_id'] == 'cases' else None
            assert row['original_label'] == expected, row['id']
        if 'parent_id' in row:
            assert row['parent_id'] in ids
    assert packet['counts']['total'] == len(annotations)
    assert packet['counts']['contexts'] == dict(Counter(row['proposed_context'] for row in annotations))
    assert packet['counts']['private_proposals'] == dict(Counter(str(row['proposed_stream_private']) for row in annotations))
    assert packet['counts']['affirmative_evidence'] == dict(Counter(str(row['proposed_affirmative_private_evidence']) for row in annotations))
    assert packet['counts']['review_status'] == dict(Counter(row['approval'] for row in annotations))
    confirmed = {row['id']: row for row in annotations if row['approval'] == 'maintainer_confirmed'}
    assert set(confirmed) == {'raw1400:16', 'maintainer-example:0'}
    assert confirmed['raw1400:16']['proposed_context'] == 'session'
    assert confirmed['raw1400:16']['proposed_stream_private'] == 'private'
    assert confirmed['raw1400:16']['proposed_affirmative_private_evidence'] is True
    assert confirmed['raw1400:16']['review_history'][0]['previous']['proposed_context'] == 'unresolved'
    assert confirmed['maintainer-example:0']['proposed_context'] == 'promotion'
    assert confirmed['maintainer-example:0']['proposed_stream_private'] == 'not_private'
    assert confirmed['maintainer-example:0']['proposed_affirmative_private_evidence'] is False
    assert confirmed['raw1400:16']['contrast_group'] == confirmed['maintainer-example:0']['contrast_group']
    assert sum(row['data_role'] == 'historical_control' for row in annotations) == 65
    catalogue = json.loads((DIRECTORY / 'catalogue-candidates.json').read_text())
    assert len(catalogue['entries']) == 50
    assert all(not row['approved'] and row['catalogue_url'].startswith('https://otservlist.net/') for row in catalogue['entries'])
    print(f'PASS {len(annotations)} review records (2 maintainer-confirmed), exact source spans/hashes, 50 unapproved catalogue facts; no training approvals')


if __name__ == '__main__':
    main()
