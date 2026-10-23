// Server-identity inference. All entities, feature definitions and fitted
// coefficients come from tibia-evidence.json. Python parity is checked over
// every capture; commands, language and generic gameplay have no features.
(() => {
    'use strict';
    const normalize = text => String(text).normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/\s+/g, ' ').trim();
    const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const rounded = value => Math.round(value * 1000000) / 1000000;
    const featureFields = (title, tags, extractor) => {
        title = normalize(title).replace(new RegExp(extractor.command_pattern, 'g'), ' ');
        const tagSet = new Set(tags.map(normalize));
        const fields = [{}, {}];
        for (const key of Object.keys(extractor.features).sort()) {
            const spec = extractor.features[key];
            const matches = [...new Set(spec.terms)].sort().filter(term => spec.source === 'title'
                ? new RegExp(`(^|[^a-z0-9])${escape(term)}(?=$|[^a-z0-9])`).test(title) : tagSet.has(term));
            if (matches.length) { fields[spec.source === 'title' ? 0 : 1][key] = matches; }
        }
        return fields;
    };
    const create = data => {
        const model = data?.model;
        const extractor = data?.extractor;
        if (model?.format !== 'server-identity-logistic-v1' || !Number.isFinite(model.bias)
            || !(model.official_threshold > 0 && model.official_threshold < model.other_threshold && model.other_threshold < 1)
            || !model.weights || !extractor?.features || Array.isArray(model.weights)
            || Object.keys(model.weights).sort().join(',') !== Object.keys(extractor.features).sort().join(',')) { throw new Error('Invalid server-identity model'); }
        for (const [key, spec] of Object.entries(extractor.features)) {
            if (!/^[a-z_]+$/.test(key) || !Number.isFinite(model.weights[key]) || !['tibia', 'other'].includes(spec.side)
                || !['title', 'tags'].includes(spec.source) || !Array.isArray(spec.terms) || !spec.terms.length
                || spec.terms.some(term => typeof term !== 'string' || !/^[a-z0-9 .-]+$/.test(term))) { throw new Error('Invalid identity feature'); }
        }
        if (extractor.command_pattern !== '[!\u2757\u2755]\\s*[a-z0-9_]+'
            || extractor.context_pattern !== '(^|[^a-z0-9])(?:nao|not|never|ex|vs|versus|depois|luego)(?=$|[^a-z0-9])') { throw new Error('Unsupported extraction policy'); }
        return (title, tags) => {
            const [titleFeatures, tagFeatures] = featureFields(title, tags, extractor);
            const combined = { ...titleFeatures, ...tagFeatures };
            const known = Object.keys(combined).sort();
            const contributions = { title: 0, tags: 0 };
            const signals = [];
            let logit = model.bias;
            for (const key of known) {
                const spec = extractor.features[key];
                const weight = model.weights[key];
                logit += weight;
                contributions[spec.source] += weight;
                signals.push({ side: spec.side, source: spec.source, game: spec.side === 'tibia' ? 'Tibia' : 'Other games',
                    text: combined[key].join(', '), feature: key, weight: rounded(weight) });
            }
            const probability = 1 / (1 + Math.exp(-Math.max(-40, Math.min(40, logit))));
            const sides = new Set(signals.map(s => s.side));
            const context = normalize(title).replace(new RegExp(extractor.command_pattern, 'g'), ' ');
            const blocked = !known.length ? 'no server identity' : sides.size > 1 ? 'conflicting server identities'
                : new RegExp(extractor.context_pattern).test(context) ? 'negation, comparison or temporal context' : '';
            const verdict = blocked ? 'undetermined' : probability >= model.other_threshold ? 'other'
                : probability <= model.official_threshold ? 'tibia' : 'undetermined';
            const score = { other: rounded(probability), tibia: rounded(1 - probability) };
            let reason = blocked || (verdict === 'undetermined' ? 'insufficient confidence' : 'server identity evidence');
            if (known.length) { reason += ': ' + signals.map(s => s.text).join('; '); }
            return { verdict, reason, score, found: { signals,
                model: { logit: rounded(logit), title: rounded(contributions.title), tags: rounded(contributions.tags), bias: model.bias, matched: known.length },
                score, abstention: blocked || null } };
        };
    };
    globalThis.TwitchCleanTibiaClassify = { create, normalize, featureFields };
})();
