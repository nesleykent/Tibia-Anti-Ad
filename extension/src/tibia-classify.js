// Tibia Anti-Ad: JavaScript port of Evidence.classify() in tools/twitch_evidence.py.
// Keep the two in step; tests/python/test_twitch_evidence.py checks they agree.
(() => {
    'use strict';

    const COMMAND = '!❗❕';
    const escape = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const normalize = s => s.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/\s+/g, ' ').trim();

    // Whole-word terms; group 1 captures a "!"/"❗" right before the term (a chat command).
    const words = terms => {
        const alt = terms.map(normalize).sort((a, b) => b.length - a.length).map(escape).join('|');
        return new RegExp(`(?<![a-z0-9])([${COMMAND}])?(?:${alt})(?![a-z0-9])`, 'g');
    };

    // "map view" -> map\s*\S{0,2}iew: tolerates OCR noise such as "Map ¥Yiew".
    const fuzzy = term => new RegExp(`${term.slice(0, -3).split(' ').filter(Boolean).map(escape).join('\\s*')}\\s*\\S{0,2}${escape(term.slice(-3))}`);

    const create = data => {
        const officialTitle = words([...data.official.title, ...data.official.worlds]);
        // Worlds that are also ordinary words count in a title only as "[World" or "(World".
        const officialBracketed = new RegExp(`[\\[(]\\s*(?:${data.official.worlds_tags_only.map(escape).join('|')})(?![a-z0-9])`, 'g');
        const officialTags = data.official.tag_patterns.map(p => new RegExp(p));
        const worldTags = new Set([...data.official.worlds, ...data.official.worlds_tags_only].map(normalize));
        const games = Object.entries(data.games).map(([game, spec]) => [
            game, words(spec.words), (spec.title_patterns || []).map(p => new RegExp(p, 'g')), spec.tag_patterns.map(p => new RegExp(p)),
        ]);
        const otUi = data.client_ui.ot_only.map(t => [t, fuzzy(t)]);

        const metadata = (title, tags) => {
            title = normalize(title);
            tags = tags.map(t => normalize(t).replace(/ /g, ''));
            const found = { declared: {}, tagged: {}, commands: {}, official_title: [], official_tags: [] };
            for (const [game, pattern, titlePatterns, tagPatterns] of games) {
                const hits = [...title.matchAll(pattern)].map(m => [m[0], Boolean(m[1])]);
                for (const p of titlePatterns) {
                    for (const m of title.matchAll(p)) { hits.push([m[0], m.index > 0 && COMMAND.includes(title[m.index - 1])]); }
                }
                for (const [text, command] of hits) {
                    const kind = command ? 'commands' : 'declared';
                    (found[kind][game] = found[kind][game] || []).push(text);
                }
                const tagged = tags.filter(t => tagPatterns.some(p => p.test(t)));
                if (tagged.length) { found.tagged[game] = tagged; }
            }
            found.official_title = [...title.matchAll(officialTitle)].filter(m => !m[1]).map(m => m[0])
                .concat([...title.matchAll(officialBracketed)].map(m => m[0]));
            found.official_tags = tags.filter(t => worldTags.has(t) || officialTags.some(p => p.test(t)));
            return found;
        };

        // ocr is the thumbnail text, or null when it was not read.
        return (title, tags, ocr = null) => {
            const found = metadata(title, tags);
            // A "!server" chat command in the title names the server just like plain text.
            const declared = [...new Set([...Object.keys(found.declared), ...Object.keys(found.commands)])].sort();
            const tagged = Object.keys(found.tagged).sort();
            const officialInTitle = found.official_title.length > 0;
            const officialInTags = found.official_tags.length > 0;
            // The title outranks the tags.
            if (declared.length && !officialInTitle) {
                return { verdict: 'other', reason: `declared in title: ${declared.join(', ')}`, found };
            }
            if (!declared.length && !officialInTitle) {
                if (tagged.length && !officialInTags) { return { verdict: 'other', reason: `tagged: ${tagged.join(', ')}`, found }; }
                if (officialInTags && !tagged.length) { return { verdict: 'tibia', reason: 'official world or tibiaglobal tag', found }; }
            }
            if (officialInTitle && !declared.length && !tagged.length) {
                return { verdict: 'tibia', reason: 'official world or Tibia Global in title', found };
            }
            // The screen breaks ties: an OTServer-only client beats a "tibiaglobal" tag.
            if (ocr !== null) {
                const screen = normalize(ocr);
                const ui = otUi.filter(([, p]) => p.test(screen)).map(([t]) => t);
                if (ui.length) {
                    found.screen = ui;
                    return { verdict: 'other', reason: `OTServer-only client on screen: ${ui.join(', ')}`, found };
                }
            }
            if (declared.length || tagged.length) { return { verdict: 'undetermined', reason: 'evidence for Tibia and another game', found }; }
            return { verdict: 'undetermined', reason: 'no decisive evidence', found };
        };
    };

    globalThis.TwitchCleanTibiaClassify = { create, normalize };
})();
