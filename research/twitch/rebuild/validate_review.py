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
        assert row['approval'] in {'pending', 'maintainer_confirmed', 'maintainer_bulk_approved', 'maintainer_baseline_confirmed'} and not row['use_in_training'], row['id']
        if row['approval'] == 'maintainer_confirmed':
            assert row['review_source'] in known_sources, row['id']
            assert next(source for source in sources if source['id'] == row['review_source'])['kind'] == 'explicit_maintainer_label_review'
        if row['approval'] == 'maintainer_bulk_approved':
            assert row['proposed_stream_private'] in {'private', 'not_private'}
            assert row['review_source'] in known_sources
            assert next(source for source in sources if source['id'] == row['review_source'])['kind'] in {'explicit_maintainer_bulk_label_review', 'explicit_maintainer_label_review'}
            assert row['bulk_approval_basis']
        assert row['proposed_context'] in {'session', 'promotion', 'negation', 'comparison', 'unresolved', 'no_evidence', 'mixed'}
        assert row['proposed_stream_private'] in {'private', 'not_private', 'mixed', None}
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
    assert {'raw1400:16', 'maintainer-example:0', 'audit:155', 'audit:132'} <= set(confirmed)
    assert confirmed['audit:155']['proposed_stream_private'] == 'not_private'
    assert confirmed['audit:132']['proposed_stream_private'] == 'private'
    assert confirmed['raw1400:16']['proposed_context'] == 'session'
    assert confirmed['raw1400:16']['proposed_stream_private'] == 'private'
    assert confirmed['raw1400:16']['proposed_affirmative_private_evidence'] is True
    assert confirmed['raw1400:16']['review_history'][0]['previous']['proposed_context'] == 'unresolved'
    assert confirmed['maintainer-example:0']['proposed_context'] == 'promotion'
    assert confirmed['maintainer-example:0']['proposed_stream_private'] == 'not_private'
    assert confirmed['maintainer-example:0']['proposed_affirmative_private_evidence'] is False
    assert confirmed['raw1400:16']['contrast_group'] == confirmed['maintainer-example:0']['contrast_group']
    assert sum(row['data_role'] == 'historical_control' for row in annotations) == 65
    queue = json.loads((DIRECTORY / 'review-queue.json').read_text())
    queued = [identifier for group in queue['groups'] for identifier in group['ids']]
    assert len(queued) == len(set(queued)) == 131
    assert len(queue['groups']) == 122
    assert [group['category'] for group in queue['groups']] == sorted(group['category'] for group in queue['groups'])
    by_id = {row['id']: row for row in annotations}
    assert {row['id'] for row in annotations if row['proposed_stream_private'] in {None, 'not_private'}} <= set(queued)
    assert set(queue['bulk_approved_ids']) == {row['id'] for row in annotations if row['approval'] == 'maintainer_bulk_approved'}
    assert len(queue['round1_bulk_approved_ids']) == 89
    assert set(queued).isdisjoint(queue['round1_bulk_approved_ids'])
    assert set(queued) | set(queue['round1_bulk_approved_ids']) | set(queue['deferred_ids']) == ids
    assert queue['deferred_ids'] == ['audit:7']
    assert by_id['audit:7']['approval'] == 'maintainer_baseline_confirmed'
    for group in queue['groups']:
        for identifier in group['ids']:
            row = by_id[identifier]
            assert row['proposed_stream_private'] == group['proposed_label']
            assert row['proposed_context'] == group['context']
    for row in annotations:
        if row['approval'] == 'maintainer_bulk_approved' and 'parent_id' in row:
            assert by_id[row['parent_id']]['approval'] == 'maintainer_bulk_approved'
    real = [row for row in annotations if row['data_role'] in {'captured_metadata', 'maintainer_reported_stream_example'}]
    assert len(real) == 115
    assert Counter(row['proposed_context'] for row in real) == {'session': 87, 'promotion': 17, 'no_evidence': 8, 'mixed': 1, 'unresolved': 1, 'comparison': 1}
    assert [row['id'] for row in real if row['proposed_context'] == 'promotion' and row['proposed_stream_private'] == 'not_private'] == ['audit:42', 'audit:179', 'audit:218', 'maintainer-example:0']
    for group in queue['groups']:
        expected_links = set()
        for identifier in group['ids']:
            row = by_id[identifier]
            if 'parent_id' in row:
                row = by_id[row['parent_id']]
            if row['data_role'] == 'captured_metadata':
                original = corpus[row['source_id']][row['source_index']]
                channel = original.get('canal', original.get('channel'))
                url = original.get('url') or 'https://www.twitch.tv/' + channel
                expected_links.add((channel, url, row['source_id'], row['source_index']))
        actual_links = {(link['channel'], link['url'], link['source_id'], link['source_index']) for link in group['source_links']}
        assert actual_links == expected_links
    baseline = json.loads((ROOT / 'tests/data/tibia-no-private-evidence-acceptance.json').read_text())
    assert baseline['expected_private_probability'] == packet['no_private_evidence_contract']['private_probability'] == 0.01
    assert len(baseline['annotation_ids']) == len(set(baseline['annotation_ids'])) == 35
    assert set(baseline['annotation_ids']) == set(queue['no_private_evidence_ids'])
    assert {row['id'] for row in annotations if row['proposed_stream_private'] is None} | {'audit:7'} == set(baseline['annotation_ids'])
    for identifier in baseline['annotation_ids']:
        supervision = by_id[identifier]['model_supervision']
        assert supervision['kind'] == 'no_private_server_evidence'
        assert supervision['expected_private_probability'] == 0.01
        assert supervision['private_evidence_target'] == 0
        assert supervision['must_preserve_in_dataset'] is True
        assert supervision['source'] in known_sources
        assert by_id[identifier]['proposed_affirmative_private_evidence'] is False
    assert not queue['pending_decision_ids']
    assert queue['mixed_session_ids'] == ['audit:384']
    mixed = by_id['audit:384']
    assert mixed['proposed_stream_private'] == mixed['proposed_context'] == 'mixed'
    assert mixed['model_supervision']['private_evidence_target'] == 0.5
    assert mixed['model_supervision']['expected_private_probability'] == 0.5
    assert mixed['model_supervision']['must_preserve_in_dataset'] is True
    assert mixed['approval'] == 'maintainer_confirmed'
    assert 'audit:384' not in baseline['annotation_ids']
    mixed_fixture = json.loads((ROOT / 'tests/data/tibia-mixed-context-acceptance.json').read_text())['cases'][0]
    assert mixed_fixture['id'] == 'audit:384'
    assert mixed_fixture['private_probability_min'] <= 0.5 <= mixed_fixture['private_probability_max']
    for identifier in ['audit:179', 'cases:3', 'audit:218', 'audit:351']:
        assert by_id[identifier]['proposed_stream_private'] == 'not_private'
    for identifier in ['audit:283', 'audit:433', 'audit:450', 'cases:8', 'audit:452']:
        assert by_id[identifier]['proposed_stream_private'] == 'private'
    assert by_id['cases:4']['model_supervision']['expected_private_probability'] == 0.01
    catalogue = json.loads((DIRECTORY / 'catalogue-candidates.json').read_text())
    assert len(catalogue['entries']) == 50
    assert all(not row['approved'] and row['catalogue_url'].startswith('https://otservlist.net/') for row in catalogue['entries'])
    print(f'PASS {len(annotations)} review records with current maintainer adjudications and 35 mandatory 1% baseline cases and one 50% mixed-session target, 122 compact groups / 131 records, exact source spans/hashes, 50 unapproved catalogue facts; no training approvals')


if __name__ == '__main__':
    main()
