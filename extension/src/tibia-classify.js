// Portable entity/context inference. Parameters, patterns and normalization are
// exported from Python by tools/twitch_evidence.py. No channel enters inference.
(() => {
    'use strict';
    const points = s => Array.from(s);
    const slice = (s, a, b) => points(s).slice(a, b).join('');
    const length = s => points(s).length;
    const alphaNumeric = c => Boolean(c && /[\p{L}\p{N}]/u.test(c));
    // Python's Unicode word boundaries and \w differ from JavaScript's ASCII ones.
    const regex = (pattern, flags = '') => new RegExp(pattern
        .replace(/\\b/g, '(?:(?<![\\p{L}\\p{N}_])(?=[\\p{L}\\p{N}_])|(?<=[\\p{L}\\p{N}_])(?![\\p{L}\\p{N}_]))')
        .replace(/\[\\w\.\]/g, '[\\p{L}\\p{N}_.]')
        .replace(/\\w/g, '[\\p{L}\\p{N}_]'), flags + 'u');
    const matches = (s, pattern) => [...s.matchAll(regex(pattern, 'g'))].map(m => ({
        text: m[0], group: m[1], start: length(s.substring(0, m.index)), end: length(s.substring(0, m.index + m[0].length)),
    }));
    // CPython 3.12+ uses compensated float summation.
    const sum = values => {
        let hi = 0, lo = 0;
        for (const x of values) {
            const t = hi + x;
            lo += Math.abs(hi) >= Math.abs(x) ? (hi - t) + x : (x - t) + hi;
            hi = t;
        }
        return hi + lo;
    };
    const create = data => {
        const model = data?.model, spec = data?.inference;
        if (model?.format !== 'identifier-span-logit-v4' || model.base_private_probability !== 0.01
            || !spec?.features?.length || !spec.context || !spec.patterns || !spec.lookalike
            || !model.identifier_weights || !model.identifier_cutoffs || Object.values(model.identifier_cutoffs).some(w => !Number.isFinite(w))
            || !Array.isArray(spec.languages) || !Array.isArray(spec.domain_second_levels) || spec.hash_size !== 4096
            || Object.values(model.identifier_weights).some(w => !Number.isFinite(w))
            || !Number.isFinite(model.hide_threshold) || model.hide_threshold <= 0 || model.hide_threshold > 1
            || !Number.isFinite(model.calibration?.slope) || model.calibration.slope <= 0
            || !Number.isFinite(model.calibration.intercept)
            || spec.features.some(f => !Number.isFinite(model.weights?.[f]))) { throw new Error('Invalid private-server model'); }
        const normalize = s => String(s).normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase()
            .split('').map(c => spec.lookalike[c] || c).join('').replace(/[\s\u001c-\u001f]+/g, ' ').trim();
        const canonical = s => normalize(s).replace(/[^a-z0-9]/g, '').replace(/1/g, 'i').replace(/0/g, 'o');
        const pat = spec.patterns;
        const test = (s, p) => regex(p).test(s);
        const hash = s => { let h = 2166136261; for (const c of points(s)) { h = Math.imul(h ^ c.codePointAt(0), 16777619) >>> 0; } return h; };
        const spanFeatures = span => {
            let value = span.kind === 'domain' ? span.text.split('/')[0] : span.text;
            const key = canonical(value), padded = '^' + key + '$', grams = new Set();
            for (const n of [2, 3, 4]) { for (let i = 0; i <= padded.length - n; i++) { grams.add(padded.slice(i, i + n)); } }
            const features = {};
            for (const gram of [...grams].sort()) { const i = String(hash('span:' + gram) % spec.hash_size); features[i] = (features[i] || 0) + 1 / Math.sqrt(Math.max(1, grams.size)); }
            const structure = ['bias', 'kind:' + span.kind];
            if (span.protocol_context && ['name', 'domain'].includes(span.kind)) { structure.push('protocol_context:' + span.kind); }
            if (span.protocol_adjacent) {
                structure.push('protocol_adjacent:' + span.kind);
                if (span.launch) {
                    structure.push('launch:protocol_adjacent:' + span.kind);
                    structure.push('launch:protocol_length:' + (value.replace(/[^a-z]/g, '').length <= 6 ? 'short' : 'long'));
                }
            }
            let suffixSource = value;
            if (span.kind === 'domain') {
                const labels = value.split('.');
                if (labels.length > 1) { labels.pop(); }
                if (labels.length > 1 && spec.domain_second_levels.includes(labels.at(-1))) { labels.pop(); }
                suffixSource = labels.at(-1);
            }
            if (span.kind !== 'protocol' && /(?:7[0-9]{1,2}|8[0-9]{1,2})$/.test(suffixSource.replace(/[^a-z0-9]/g, ''))) { structure.push('protocol_suffix', 'protocol_suffix:' + span.kind); }
            for (const [part, pattern] of [['ot', 'ot$'], ['online', 'online'], ['idle', 'idle'], ['poke', '^poke'], ['baiak', 'baiak'], ['server', 'server'], ['arena', 'arena']]) {
                if (test(key, pattern)) {
                    structure.push('part:' + part);
                    if (value.includes(' ') && part !== 'poke') {
                        structure.push('compound:' + part);
                        if (['online', 'idle'].includes(part) && key.endsWith(part)) { features['s:compound_stem_length:' + part] = Math.min(16, key.length - part.length) / 8; }
                    }
                    if (span.launch) { structure.push('launch:' + part); }
                }
            }
            if (key.startsWith('poke') && key.length > (key.startsWith('pokemon') ? 7 : 4) + 2) { structure.push('brand_tail:poke'); }
            if (span.kind === 'domain') { structure.push(span.text.split('/')[0].split('.').length > 2 ? 'domain:multi' : 'domain:single'); }
            for (const name of structure) { features['s:' + name] = 1; }
            return features;
        };
        const references = (title, tags) => {
            const text = normalize(title), commands = matches(text, pat.command), proposed = [];
            const raw = String(title).normalize('NFKD').replace(/\p{M}/gu, '').replace(/[\s\u001c-\u001f]+/g, ' ').trim();
            const put = (kind, m, field, value) => {
                let {start, end} = m, name = m.text;
                if (name.startsWith('ex-')) { start += 3; name = name.slice(3); }
                if (spec.languages.includes(name)) { return; }
                const adjacent = field === 'title' && ['name', 'domain'].includes(kind) && matches(text, pat.protocol).some(p =>
                    end <= p.start && ['', '-', 'v', 'version'].includes(slice(text, end, p.start).trim()));
                const item = {kind, start, end, text: name, field, origin: field === 'tag' ? value : null, launch: test(text, pat.launch), protocol_context: test(text, pat.protocol), protocol_adjacent: adjacent};
                if (!proposed.some(c => JSON.stringify(c) === JSON.stringify(item))) { proposed.push(item); }
            };
            for (const [field, value] of [['title', text], ...[...new Set(tags)].sort().filter(t => !spec.languages.includes(normalize(t))).map(t => ['tag', normalize(t)])]) {
                const occupied = [];
                if (field === 'title') {
                    for (const project of matches(raw, pat.project)) {
                        const name = normalize(project.text);
                        if (slice(value, project.start, project.start + length(name)) === name) {
                            put('name', {start: project.start, end: project.start + length(name), text: name}, field, value);
                        }
                    }
                }
                for (const kind of ['domain', 'command', 'compound', 'spaced', 'protocol']) {
                    for (const m of matches(value, pat[kind])) {
                        if (occupied.some(([a, b]) => a <= m.start && m.end <= b)) { continue; }
                        put(['compound', 'spaced'].includes(kind) ? 'name' : kind, m, field, value);
                        occupied.push([m.start, m.end]);
                    }
                }
                for (const m of matches(value, pat.word)) {
                    if (occupied.some(([a, b]) => a <= m.start && m.end <= b)) { continue; }
                    const c = slice(raw, m.start, m.start + 1);
                    const capital = field === 'title' && c && c.toUpperCase() === c && c.toLowerCase() !== c;
                    const bracket = m.start > 0 && '[({'.includes(slice(value, m.start - 1, m.start));
                    if (field === 'tag' || capital || bracket || test(m.text, pat.parts)) { put('name', m, field, value); }
                }
            }
            const cmp = (a, b) => a < b ? -1 : a > b ? 1 : 0;
            const found = proposed.filter(c => {
                const fs = spanFeatures(c);
                const part = ['ot', 'online', 'idle', 'poke', 'baiak', 'server', 'arena'].find(p => Object.hasOwn(fs, 's:part:' + p));
                let bucket = c.kind;
                if (c.kind === 'name') {
                    bucket = 'name:' + (part || 'other');
                    if (part === 'poke' && Object.hasOwn(fs, 's:brand_tail:poke')) { bucket = 'name:branded:poke'; }
                    else if (part && Object.hasOwn(fs, 's:compound:' + part)) { bucket = 'name:compound:' + part; }
                    if (Object.hasOwn(fs, 's:launch:protocol_adjacent:name')) {
                        bucket = 'name:protocol-launch:' + (Object.hasOwn(fs, 's:launch:protocol_length:short') ? 'short' : 'long');
                    }
                }
                return sum(Object.keys(fs).sort().map(f => fs[f] * (model.identifier_weights[f] || 0))) >= (model.identifier_cutoffs[bucket] || 0);
            });
            found.sort((a, b) => cmp(a.field, b.field) || cmp(a.origin || '', b.origin || '') || a.start - b.start || a.end - b.end);
            return {text, commands, found};
        };
        const classify = (title, tags = []) => {
            const {text, commands, found} = references(title, tags);
            const values = Object.fromEntries(spec.features.map(f => [f, 0]));
            if (found.length) {
                const titles = found.filter(m => m.field === 'title');
                const prefix = slice(text, 0, titles.length ? Math.min(...titles.map(m => m.start)) : 0);
                Object.assign(values, {
                    identified_reference: 1,
                    tag_identifier: Number(found.some(m => m.field === 'tag')),
                    competing_named_pair: 0,
                    server_command: Number(commands.some(c => titles.some(m => m.start >= c.start && m.end <= c.end))),
                    server_domain: Number(titles.some(m => m.kind === 'domain')),
                    ot_name: Number(found.some(m => test(m.text, `^(?:${pat.ot})$`))),
                    protocol: Number(titles.some(m => m.kind === 'protocol')),
                    launch_context: Number(test(text, pat.launch)),
                    bracketed_reference: Number(titles.some(m => m.start && slice(text, m.start - 1, m.start) === '[')),
                });
                for (const [name, pattern] of Object.entries(spec.context)) {
                    const input = ['negated_reference', 'coordinated_reference', 'current_session_relation'].includes(name) ? prefix
                        : name === 'separate_session_declaration' ? (titles.length ? prefix : text) : text;
                    values[name] = Number(test(input, pattern));
                }
            }
            if (!found.some(m => m.field === 'title')) { values.separate_session_declaration = 0; }
            if (found.some(m => m.field === 'tag' || m.kind !== 'command') && !values.sponsor_context) { values.commercial_context = values.commercial_offer = 0; }
            let contributions = spec.features.filter(f => values[f]).map(feature => ({feature, value: values[feature], contribution: values[feature] * model.weights[feature]}));
            const raw = found.length ? sum(contributions.map(c => c.contribution)) : null;
            const p = found.length ? Math.max(model.base_private_probability, 1 / (1 + Math.exp(-Math.max(-40, Math.min(40, model.calibration.slope * raw + model.calibration.intercept))))) : model.base_private_probability;
            contributions = contributions.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
            return {private_probability: p, display_probability: 1 - p, hide: p >= model.hide_threshold,
                references: found, contributions, raw_logit: raw};
        };
        return classify;
    };
    const formatter = new Intl.NumberFormat(undefined, {style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1});
    const formatDisplay = probability => Number.isFinite(probability)
        ? probability < 0.0005 ? `<${formatter.format(0.001)}`
            : probability >= 0.9995 ? `>${formatter.format(0.999)}` : formatter.format(probability) : 'n/a';
    globalThis.TwitchCleanTibiaClassify = {create, formatDisplay};
})();
