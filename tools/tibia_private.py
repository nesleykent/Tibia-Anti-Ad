"""Private-server evidence with a learned, entity-conditioned context model.

No full-text bag of words. Recognition proposes server references; a supervised
context logit determines their contribution. Without a reference P=0.01 exactly.
This milestone-B module does not replace browser inference until milestone C.
"""
import json
import math
import re
from pathlib import Path
from tibia_text import normalize

BASE = 0.01
FEATURES = (
    'identified_reference', 'title_reference', 'tag_reference', 'server_command',
    'server_domain', 'ot_name', 'protocol', 'launch_context',
    'other_commands', 'command_share', 'late_reference', 'negated_reference',
    'comparison', 'past_reference', 'sponsor_context', 'commercial_context',
    'bracketed_reference', 'multiple_references', 'current_session_relation', 'coordinated_reference', 'commercial_offer', 'separate_session_declaration',
)
DOMAIN = re.compile(r'(?<![a-z0-9])(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[a-z0-9_/-]*)?')
COMMAND = re.compile(r'[!❗]\s*([a-z][a-z0-9_-]+)')
PROTOCOL = re.compile(r'(?<![\w.])(?:[1-9]|1[0-9])\.[0-9]{1,2}(?![\w.])')
OT = re.compile(r'\b[a-z][a-z0-9_-]{2,}[- ]?ot\b')
LAUNCH = re.compile(r'\b(?:launch\w*|opening|open beta|public test|abertura|lancamento|testserver)\b')
DESCRIPTORS = {'online', 'mmorpg', 'server', 'world', 'global', 'rpg'}


def canonical(value):
    return re.sub(r'[^a-z0-9]', '', normalize(value)).translate(str.maketrans('10', 'io'))


def learn_references(rows, sources):
    """Entity candidates from *training* affirmative annotations, never labels of test.

Literal names/aliases come from reviewed spans, commands, domains and their
cited source identifiers. Ordinary catalogue marketing words are not imported.
No per-channel or manually maintained server-name table.
"""
    aliases, domains, phrases = {}, set(), []
    def add(value, command_only=False):
        key = canonical(value)
        if len(key) >= 3 and not key.isdigit():
            aliases[key] = aliases.get(key, True) and command_only
    for row in rows:
        if not row.get('proposed_affirmative_private_evidence'):
            continue
        span = row.get('evidence_span', {}).get('text', '')
        if not span:
            span = ' '.join(m['text'] for m in row.get('mentions', []) if m.get('context') in {'session', 'promotion', 'mixed'}) or row['title']
        text = normalize(span)
        for match in DOMAIN.finditer(text):
            domains.add(match.group().split('/')[0])
        for match in COMMAND.finditer(text):
            add(match[1], True)
        for match in OT.finditer(text):
            add(match.group())
        words = re.findall(r'[a-z0-9]+', text)
        meaningful = [w for w in words if w not in DESCRIPTORS]
        if len(meaningful) == 1 and not meaningful[0].isdigit() and not DOMAIN.search(text):
            add(meaningful[0])
        elif len(meaningful) == 2 and not any(w.isdigit() for w in meaningful):
            phrases.append(meaningful)
        if len(words) > 2 and all(len(w) == 1 for w in words):
            add(''.join(words))
        compact = canonical(text)
        for identifier in row.get('evidence_sources', []):
            source = sources.get(identifier, {})
            if source.get('kind') in {'operator', 'operator_search_cache', 'project_wiki', 'conflicting_self_description'}:
                if 3 <= len(identifier) <= 4 and canonical(identifier) in words:
                    add(identifier)
                host = re.sub(r'^https?://', '', source.get('url', '')).split('/')[0]
                for word in host.split('.'):
                    if len(word) >= 5 and word not in DESCRIPTORS and canonical(word) in compact:
                        add(word)
    # Do not learn adjacent gameplay/context as part of an already known name.
    for words in phrases:
        if not any(canonical(word) in aliases for word in words):
            add(''.join(words))
    return {'aliases': dict(sorted(aliases.items())), 'domains': sorted(domains)}


def references(title, tags, inventory):
    text = normalize(title)
    commands = list(COMMAND.finditer(text))
    matches = []
    def put(kind, start, end, name, field='title'):
        if not any(m['field'] == field and m['start'] == start and m['end'] == end and m['text'] == name for m in matches):
            matches.append({'kind': kind, 'start': start, 'end': end, 'text': name, 'field': field})
    # Names may be spaced/punctuated and use reviewed digit/homoglyph variants.
    for field, value in [('title', text)] + [('tag', normalize(t)) for t in sorted(set(tags))]:
        chars, positions = [], []
        for i, char in enumerate(value):
            c = canonical(char)
            if c:
                chars.append(c); positions.append(i)
        compact = ''.join(chars)
        for alias, command_only in inventory['aliases'].items():
            begin = 0
            while (at := compact.find(alias, begin)) >= 0:
                start, end = positions[at], positions[at + len(alias) - 1] + 1
                begin = at + len(alias)
                if (start and value[start - 1].isalnum()) or (end < len(value) and value[end].isalnum()):
                    continue
                is_command = field == 'title' and any(c.start() <= start and end <= c.end() for c in commands)
                if command_only and not is_command:
                    continue
                put('command' if is_command else 'name', start, end, value[start:end], field)
    for match in OT.finditer(text):
        put('ot_name', match.start(), match.end(), match.group())
    for match in DOMAIN.finditer(text):
        domain = match.group().split('/')[0]
        if domain in inventory['domains'] or LAUNCH.search(text):
            put('domain', match.start(), match.end(), match.group())
    for match in PROTOCOL.finditer(text):
        put('protocol', match.start(), match.end(), match.group())
    return text, commands, matches


def context_features(title, tags, inventory):
    text, commands, matches = references(title, tags, inventory)
    values = dict.fromkeys(FEATURES, 0.0)
    if not matches:
        return values, []
    titles = [m for m in matches if m['field'] == 'title']
    private_commands = [c for c in commands if any(m['start'] >= c.start() and m['end'] <= c.end() for m in titles)]
    first = min((m['start'] for m in titles), default=0)
    prefix = text[:first]
    values.update(
        identified_reference=1.0, title_reference=float(bool(titles)),
        tag_reference=float(any(m['field'] == 'tag' for m in matches)),
        server_command=float(bool(private_commands)),
        server_domain=float(any(m['kind'] == 'domain' for m in titles)),
        ot_name=float(any(OT.fullmatch(m['text']) for m in titles)),
        protocol=float(any(m['kind'] == 'protocol' for m in titles)),
        launch_context=float(bool(LAUNCH.search(text))),
        other_commands=min(6, len(commands) - len(private_commands)) / 6,
        command_share=len(private_commands) / max(1, len(commands)),
        late_reference=first / max(1, len(text)),
        negated_reference=float(bool(re.search(r'\b(?:nao jogo|nao estou|not playing|nao|nunca)\b[^.!;]{0,30}$', prefix))),
        comparison=float(bool(re.search(r'\b(?:vs|versus)\b', text))),
        past_reference=float(bool(re.search(r'\b(?:ex[- ]|histor\w*|document\w*)', text))),
        sponsor_context=float(bool(re.search(r'\b(?:patrocin\w*|sponsor\w*|meu link|link do)\b', text))),
        commercial_context=float(bool(re.search(r'(?:[!❗]\s*(?:loja|shop)|\btc\s*/|\bsub\b)', text))),
        bracketed_reference=float(any(m['start'] and text[m['start'] - 1] == '[' for m in titles)),
        multiple_references=min(3, len({canonical(m['text']) for m in matches})) / 3,
        separate_session_declaration=float(bool(re.search(r'\b(?:tibia global|hoje so|hoje jogo|jogo em)\b', prefix if titles else text))),
        commercial_offer=float(bool(re.search(r'(?:\btc\s*/\s*mes|\bsem sub\b|\bsub\s+[0-9]+)', text))),
        coordinated_reference=float(bool(re.search(r'\b(?:e|and)\s*$', prefix))),
        current_session_relation=float(bool(re.search(r'\b(?:jogo|jogando|estou no|playing|no|on)\s*$', prefix))),
    )
    return values, matches


class PrivateModel:
    def __init__(self, data):
        if data['format'] != 'entity-context-logit-v1':
            raise ValueError('Unsupported private-evidence model')
        self.data = data

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text()))

    def predict(self, title, tags=()):
        values, matches = context_features(title, tags, self.data['references'])
        if not matches:
            probability = BASE
            contributions = []
            raw = None
        else:
            contributions = [{'feature': name, 'value': value,
                              'contribution': value * self.data['weights'][name]}
                             for name, value in values.items() if value]
            raw = sum(item['contribution'] for item in contributions)
            a, b = self.data['calibration']['slope'], self.data['calibration']['intercept']
            logit = a * raw + b
            probability = max(BASE, 1 / (1 + math.exp(-max(-40, min(40, logit)))))
        return {'private_probability': probability, 'display_probability': 1 - probability,
                'hide': probability >= self.data['hide_threshold'], 'references': matches,
                'contributions': sorted(contributions, key=lambda v: -abs(v['contribution'])),
                'raw_logit': raw}
