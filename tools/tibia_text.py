"""Server-identity extraction shared with the browser, driven by exported data.

There are deliberately no learned words, subwords, language, gameplay, channel,
viewer or image features. An unknown identity cannot acquire a verdict by
resembling a known word. Whole tags and bounded title phrases are distinct.
"""
import re
import unicodedata


def normalize(text):
    text = unicodedata.normalize('NFKD', str(text))
    return ' '.join(''.join(c for c in text if not unicodedata.category(c).startswith('M')).lower().split())


def feature_fields(title, tags, extractor):
    title = re.sub(extractor['command_pattern'], ' ', normalize(title))
    tags = {normalize(tag) for tag in tags}
    fields = ({}, {})
    for key, spec in sorted(extractor['features'].items()):
        terms = sorted(set(spec['terms']))
        if spec['source'] == 'title':
            matches = [t for t in terms if re.search(r'(?<![a-z0-9])' + re.escape(t) + r'(?![a-z0-9])', title)]
            if matches:
                fields[0][key] = matches
        else:
            matches = sorted(tags.intersection(terms))
            if matches:
                fields[1][key] = matches
    return fields


def features(title, tags, extractor):
    a, b = feature_fields(title, tags, extractor)
    return sorted(a.keys() | b.keys())


def ambiguous_context(title, extractor):
    text = re.sub(extractor['command_pattern'], ' ', normalize(title))
    return bool(re.search(extractor['context_pattern'], text))
