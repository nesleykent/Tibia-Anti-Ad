"""Identifier-span recognition. Only characters inside candidate spans are learned."""
import math
import re
from tibia_text import normalize, feature_id
from tibia_private import BASE, FEATURES as CONTEXT_FEATURES, CONTEXT, DOMAIN, COMMAND, PROTOCOL, OT, LAUNCH, portable_sum

# Language metadata is discarded before feature extraction, independently of fit.
LANGUAGES = 'portugues portuguesbr portuguesbrasil portuguese english ingles espanhol espanol spanish polski polish polska svensk svenska swedish deutsch german francais french italiano italian nederlands dutch catalan catala turkce turkish norsk norwegian dansk danish suomi finnish russian russkiy ukrainian arabic japanese korean chinese pt br en eng esp es pl swe ptbr'.split()
LANGUAGES = sorted(set(LANGUAGES + [normalize(v) for v in ('Englisch|EspañolLatinoamerica|EspañolLatinoamericano|SpanishAndEnglish|EnglishOnly|PolishOnly|Portoguês|PortuguêsBrasil|PortuguêsPT|PortugueseBR|Brasileiro|Inglés|PolishLanguage|Čeština|Czech|Ελληνικά|Greek|Magyar|Hungarian|Bahasa Indonesia|Indonesian|Bahasa Melayu|Malay|ไทย|Thai|Tiếng Việt|Vietnamese|Română|Romanian|Русский|Українська|العربية|日本語|한국어|中文|漢語|简体中文|繁體中文|Türkçe|Turkish|Català|Norsk|Suomi|Dansk|Filipino|Tagalog|Slovenčina|Slovak|Hrvatski|Croatian|Српски|Serbian|Български|Bulgarian|עברית|Hebrew|हिन्दी|Hindi').split('|')]))
PATTERNS = {
 'domain': DOMAIN.pattern, 'command': COMMAND.pattern, 'protocol': PROTOCOL.pattern,
 'word': r'(?<![a-z0-9])[a-z][a-z0-9_-]{2,}(?![a-z0-9])',
 'compound': r'\b(?:[a-z][a-z0-9_-]*\s+(?:online|idle|idd le|ot)|(?:poke|pokemon|baiak|idle)\s+[a-z][a-z0-9_-]*(?:\s+(?:world|moon))?)\b',
 'spaced': r'\b(?:[a-z]\s+){3,}[a-z]\b',
 'project': r'\b(?:[A-Z][a-z]+(?:\s+(?:of\s+)?[A-Z][a-z]+){1,2}|[A-Z]{3,}\s+[A-Z]{3,})\b',
 'parts': r'(?:ot$|^ot|online|idle|^poke|baiak|server|arena)',
 'launch': LAUNCH.pattern,
}
SIZE = 4096
FEATURES = CONTEXT_FEATURES + ('tag_identifier',)


def candidates(title, tags=()):
    text = normalize(title)
    found = []
    def put(kind, m, field, value):
        start, end = m.span()
        name = m.group()
        if name.startswith('ex-'):
            start += 3
            name = name[3:]
        if name in LANGUAGES:
            return
        item = dict(kind=kind, start=start, end=end, text=name, field=field, origin=value if field == 'tag' else None, launch=bool(LAUNCH.search(text)), protocol_context=bool(PROTOCOL.search(text)))
        if item not in found:
            found.append(item)
    # Capitalization is used only to propose a span, never as a language feature.
    import unicodedata
    raw = ' '.join(''.join(c for c in unicodedata.normalize('NFKD', str(title)) if not unicodedata.category(c).startswith('M')).split())
    for field, value in [('title', text)] + [('tag', normalize(t)) for t in sorted(set(tags)) if normalize(t) not in LANGUAGES]:
        occupied = []
        if field == 'title':
            for project in re.finditer(PATTERNS['project'], raw):
                m = re.compile(re.escape(normalize(project.group()))).search(value, project.start())
                if m and m.start() == project.start():
                    put('name', m, field, value)
        for kind in ('domain', 'command', 'compound', 'spaced', 'protocol'):
            for m in re.finditer(PATTERNS[kind], value):
                if any(a <= m.start() and m.end() <= b for a, b in occupied):
                    continue
                put('name' if kind in {'compound', 'spaced'} else kind, m, field, value)
                occupied.append(m.span())
        for m in re.finditer(PATTERNS['word'], value):
            if any(a <= m.start() and m.end() <= b for a, b in occupied):
                continue
            capital = field == 'title' and m.start() < len(raw) and raw[m.start()].isupper()
            bracket = m.start() > 0 and value[m.start()-1] in '[({'
            if field == 'tag' or capital or bracket or re.search(PATTERNS['parts'], m.group()):
                put('name', m, field, value)
    return sorted(found, key=lambda m: (m['field'], m['origin'] or '', m['start'], m['end']))


def span_features(span):
    value = span['text']
    if span['kind'] == 'domain':
        value = value.split('/')[0]
    key = re.sub('[^a-z0-9]', '', value).translate(str.maketrans('10', 'io'))
    padded = '^' + key + '$'
    grams = sorted({padded[i:i+n] for n in (2, 3, 4) for i in range(len(padded)-n+1)})
    values = {}
    for gram in grams:
        index = str(int(feature_id('span:' + gram), 16) % SIZE)
        values[index] = values.get(index, 0) + 1 / math.sqrt(max(1, len(grams)))
    # Structural priors are fitted from labels, not assigned probabilities.
    structure = ['bias', 'kind:' + span['kind']]
    if span.get('protocol_context') and span['kind'] in {'name','domain'}:
        structure.append('protocol_context:' + span['kind'])
    for part, pattern in [('ot', r'ot$'), ('online', 'online'), ('idle', 'idle'), ('poke', r'^poke'), ('baiak', 'baiak'), ('server', 'server'), ('arena', 'arena')]:
        if re.search(pattern, key):
            structure.append('part:' + part)
            if ' ' in value and part != 'poke':structure.append('compound:' + part)
            if span.get('launch'):structure.append('launch:' + part)
    if span['kind'] == 'domain':
        host = span['text'].split('/')[0]
        structure.extend(['domain:multi' if host.count('.') > 1 else 'domain:single'])
    for name in structure:
        values['s:' + name] = 1.0
    return dict(sorted(values.items()))


def augmentations(span, positive=True):
    """Train identity-preserving spelling/transport variants within each fold.

    A server domain and its bare brand identify the same entity. These examples
    are generated only from annotated training spans, never a runtime alias list.
    Negative identifiers receive the same transformation to preserve tool/shop
    controls. The public suffix shape stays a separate structural feature.
    """
    value = span['text'].lstrip('!').split('/')[0]
    variants = set()
    if span['kind'] == 'domain':
        labels = value.split('.')
        if len(labels) > 1:
            labels.pop()  # TLD
            if len(labels) > 1 and labels[-1] in {'co', 'com', 'net', 'org', 'gov', 'edu', 'ac'}:
                labels.pop()
            brand = labels[-1]
            variants.add(brand)
            if value.endswith('.online'):
                variants.add(brand + ' online')
    if not positive and span['kind'] != 'domain':
        return []
    for part in ('online', 'idle', 'ot'):
        if value.endswith(part) and len(value) > len(part) + 2 and ' ' not in value and '.' not in value:
            variants.add(value[:-len(part)] + ' ' + part)
    return [span_features(dict(span, text=v, kind='name')) for v in sorted(variants)]


def bucket(span):
    return feature_bucket(span['kind'], span_features(span))


def feature_bucket(kind, features):
    if kind != 'name':return kind
    for part in ('ot','online','idle','poke','baiak','server','arena'):
        if 's:part:'+part in features:return 'name:'+part
    return 'name:other'


def accepted(features, kind, data):
    return score(features,data['identifier_weights']) >= data['identifier_cutoffs'].get(feature_bucket(kind,features),0.0)


def score(features, weights):
    return portable_sum(value * weights.get(name, 0.0) for name, value in features.items())


def context(title, matches):
    text = normalize(title)
    values = dict.fromkeys(FEATURES, 0.0)
    if not matches:
        return values
    titles = [m for m in matches if m['field'] == 'title']
    prefix = text[:min((m['start'] for m in titles), default=0)]
    commands = list(COMMAND.finditer(text))
    values.update(identified_reference=1.0, tag_identifier=float(any(m['field']=='tag' for m in matches)),
        server_command=float(any(c.start() <= m['start'] and m['end'] <= c.end() for c in commands for m in titles)),
        server_domain=float(any(m['kind'] == 'domain' for m in titles)),
        ot_name=float(any(OT.fullmatch(m['text']) for m in matches)),
        protocol=float(any(m['kind'] == 'protocol' for m in titles)),
        launch_context=float(bool(LAUNCH.search(text))),
        bracketed_reference=float(any(m['start'] and text[m['start']-1] == '[' for m in titles)))
    for name, pattern in CONTEXT.items():
        source = prefix if name in {'negated_reference', 'coordinated_reference', 'current_session_relation'} else prefix if name == 'separate_session_declaration' and titles else text
        values[name] = float(bool(re.search(pattern, source)))
    # Commercial terms modify command-only/sponsor references. An independent
    # server declaration or server tag remains affirmative evidence.
    independent = any(m['field'] == 'tag' or m['kind'] not in {'command'} for m in matches)
    if not titles:
        values['separate_session_declaration']=0.0
    if independent and not values['sponsor_context']:
        values['commercial_context'] = values['commercial_offer'] = 0.0
    return values


class SpanModel:
    def __init__(self, data):
        if data['format'] != 'identifier-span-logit-v3':
            raise ValueError('Unsupported identifier model')
        self.data = data

    @classmethod
    def load(cls, path):
        import json
        from pathlib import Path
        return cls(json.loads(Path(path).read_text()))

    def predict(self, title, tags=()):
        found = [m for m in candidates(title, tags) if accepted(span_features(m), m['kind'], self.data)]
        values = context(title, found)
        contributions = [dict(feature=f, value=v, contribution=v*self.data['weights'][f]) for f, v in values.items() if v]
        raw = portable_sum(c['contribution'] for c in contributions) if found else None
        p = max(BASE, 1/(1+math.exp(-max(-40,min(40,raw))))) if found else BASE
        return dict(private_probability=p, display_probability=1-p, hide=p >= self.data['hide_threshold'], references=found, contributions=sorted(contributions,key=lambda c:-abs(c['contribution'])), raw_logit=raw)
