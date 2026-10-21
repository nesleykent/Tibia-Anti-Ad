// Twitch Clean: JavaScript port of classify() in tools/twitch_evidence.py.
// Keep the two in step; tests/twitch-classify.cjs checks they agree.
(() => {
    'use strict';

    const escape = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const normalize = s => s.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/\s+/g, ' ').trim();

    const matcher = terms => {
        const alt = [...terms].sort((a, b) => b.length - a.length).map(escape).join('|');
        const re = new RegExp(`(?<![a-z0-9])(?:${alt})(?![a-z0-9])`, 'g');
        return text => [...new Set(text.match(re) || [])].sort();
    };

    // "map view" -> map\s*\S{0,2}iew: tolerates OCR noise such as "Map ¥Yiew".
    const fuzzyMatcher = terms => {
        const compiled = terms.map(t => {
            const head = t.slice(0, -3).split(' ').filter(Boolean).map(escape).join('\\s*');
            return [t, new RegExp(`${head}\\s*\\S{0,2}${escape(t.slice(-3))}`)];
        });
        return text => compiled.filter(([, re]) => re.test(text)).map(([t]) => t).sort();
    };

    const create = data => {
        const otUi = fuzzyMatcher(data.client_ui.ot_only);
        const tibiaUi = matcher(data.client_ui.tibia_like);
        const official = matcher(data.official_text);
        const servers = Object.entries(data.server_text).map(([game, terms]) => [game, matcher(terms)]);

        // ocr is the thumbnail text, or null when no thumbnail could be read.
        return (title, tags, ocr) => {
            const text = normalize(`${title} ${tags.join(' ')}`);
            const screen = normalize(ocr || '');
            const serverText = {};
            for (const [game, match] of servers) {
                const found = match(text);
                if (found.length) { serverText[game] = found; }
            }
            const found = {
                ot_ui: otUi(screen),
                tibia_ui: tibiaUi(screen),
                official_text: official(text),
                server_text: serverText,
            };
            const namesServer = Object.keys(serverText).length > 0;
            // A server named only as a chat command ("!rubinot") is often a sponsor.
            const onlyCommands = namesServer && Object.values(serverText).flat()
                .every(term => new RegExp(`!\\s*${escape(term)}`).test(text) && !new RegExp(`(^|[^!\\w])${escape(term)}`).test(text.replace(new RegExp(`!\\s*${escape(term)}`, 'g'), '')));
            // 1. The screen shows an OTServer-only client.
            if (found.ot_ui.length) {
                return { verdict: 'other', reason: 'OTServer-only client UI on screen', found };
            }
            // 2. Title/tags name another game. Decided instantly, before OCR; OCR
            //    can only overturn it when the server is just a "!command" and the
            //    screen shows a Tibia-style client (a sponsor on an official stream).
            if (namesServer && !found.official_text.length) {
                if (onlyCommands && found.tibia_ui.length) {
                    return { verdict: 'undetermined', reason: 'server only as a chat command, Tibia-style client on screen', found };
                }
                return { verdict: 'other', reason: ocr === null ? 'names another game (text only, screen not read yet)' : 'names another game, screen does not contradict', found };
            }
            if (found.official_text.length && !namesServer && found.tibia_ui.length) {
                return { verdict: 'tibia', reason: 'official marker in text and a Tibia-style client on screen', found };
            }
            return { verdict: 'undetermined', reason: 'missing or conflicting evidence', found };
        };
    };

    globalThis.TwitchCleanTibiaClassify = { create, normalize };
})();
