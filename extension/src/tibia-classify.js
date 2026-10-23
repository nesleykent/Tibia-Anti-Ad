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
        if (model?.format !== 'entity-context-logit-v2' || model.base_private_probability !== 0.01
            || !spec?.features?.length || !spec.context || !spec.patterns || !spec.lookalike
            || !model.references?.aliases || !Array.isArray(model.references.domains)
            || !Number.isFinite(model.hide_threshold) || model.hide_threshold <= 0 || model.hide_threshold > 1
            || !Number.isFinite(model.calibration?.slope) || model.calibration.slope <= 0
            || !Number.isFinite(model.calibration.intercept)
            || spec.features.some(f => !Number.isFinite(model.weights?.[f]))) { throw new Error('Invalid private-server model'); }
        const normalize = s => String(s).normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase()
            .split('').map(c => spec.lookalike[c] || c).join('').replace(/[\s\u001c-\u001f]+/g, ' ').trim();
        const canonical = s => normalize(s).replace(/[^a-z0-9]/g, '').replace(/1/g, 'i').replace(/0/g, 'o');
        const pat = spec.patterns;
        const test = (s, p) => regex(p).test(s);
        const references = (title, tags) => {
            const text = normalize(title), commands = matches(text, pat.command), found = [];
            const put = (kind, start, end, name, field = 'title', origin = null) => {
                if (!found.some(m => m.field === field && m.start === start && m.end === end && m.text === name && m.origin === origin)) {
                    found.push({kind, start, end, text: name, field, origin});
                }
            };
            for (const [field, value] of [['title', text], ...[...new Set(tags)].sort().map(t => ['tag', normalize(t)])]) {
                const chars = [], positions = [];
                points(value).forEach((char, i) => { const c = canonical(char); if (c) { chars.push(c); positions.push(i); } });
                const compact = chars.join('');
                for (const [alias, commandOnly] of Object.entries(model.references.aliases)) {
                    let begin = 0, at;
                    while ((at = compact.indexOf(alias, begin)) >= 0) {
                        const start = positions[at], end = positions[at + alias.length - 1] + 1;
                        begin = at + alias.length;
                        if ((start && alphaNumeric(slice(value, start - 1, start))) || (end < length(value) && alphaNumeric(slice(value, end, end + 1)))) { continue; }
                        const command = field === 'title' && commands.some(c => c.start <= start && end <= c.end);
                        if (commandOnly && !command) { continue; }
                        put(command ? 'command' : 'name', start, end, slice(value, start, end), field, field === 'tag' ? value : null);
                    }
                }
            }
            const caseText = String(title).normalize('NFKD').replace(/\p{M}/gu, '').replace(/[\s\u001c-\u001f]+/g, ' ').trim();
            for (const m of matches(caseText, pat.new_ot)) { put('ot_name', m.start, m.end, slice(text, m.start, m.end)); }
            if (test(text, pat.launch) || test(text, pat.protocol)) {
                for (const m of matches(text, pat.ot)) { put('ot_name', m.start, m.end, m.text); }
            }
            for (const m of matches(text, pat.domain)) {
                if (model.references.domains.includes(m.text.split('/')[0]) || test(text, pat.launch)) { put('domain', m.start, m.end, m.text); }
            }
            for (const m of matches(text, pat.protocol)) { put('protocol', m.start, m.end, m.text); }
            const unique = [];
            found.sort((a, b) => a.field.localeCompare(b.field) || (b.end - b.start) - (a.end - a.start) || a.start - b.start);
            for (const m of found) {
                if (!unique.some(n => n.field === m.field && n.origin === m.origin && n.start <= m.start && m.end <= n.end)) { unique.push(m); }
            }
            return {text, commands, found: unique.sort((a, b) => a.field.localeCompare(b.field) || a.start - b.start)};
        };
        const classify = (title, tags = []) => {
            const {text, commands, found} = references(title, tags);
            const values = Object.fromEntries(spec.features.map(f => [f, 0]));
            if (found.length) {
                const titles = found.filter(m => m.field === 'title');
                const prefix = slice(text, 0, titles.length ? Math.min(...titles.map(m => m.start)) : 0);
                const pair = String(title).normalize('NFKC').match(regex('\\b[A-Z][a-z]{3,}\\s*/\\s*[A-Z][a-z]{3,}\\b'));
                Object.assign(values, {
                    identified_reference: 1,
                    competing_named_pair: Number(Boolean(pair && (!titles.length || prefix.includes(normalize(pair[0]))))),
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
            let contributions = spec.features.filter(f => values[f]).map(feature => ({feature, value: values[feature], contribution: values[feature] * model.weights[feature]}));
            const raw = found.length ? sum(contributions.map(c => c.contribution)) : null;
            const p = found.length ? Math.max(model.base_private_probability, 1 / (1 + Math.exp(-Math.max(-40, Math.min(40, model.calibration.slope * raw + model.calibration.intercept))))) : model.base_private_probability;
            contributions = contributions.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
            return {private_probability: p, display_probability: 1 - p, hide: p >= model.hide_threshold,
                references: found, contributions, raw_logit: raw};
        };
        return classify;
    };
    globalThis.TwitchCleanTibiaClassify = {create};
})();
