// Twitch Clean: JavaScript port of Evidence.classify() in tools/twitch_evidence.py.
// Keep the two in step; tests/test_twitch_evidence.py checks they agree.
(() => {
  'use strict';

  const escape = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const normalize = s => s.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/\s+/g, ' ').trim();

  // Whole-word terms; group 1 captures a leading "!"/"\u2757" (a chat command).
  const words = terms => {
    const alt = terms.map(normalize).sort((a, b) => b.length - a.length).map(escape).join('|');
    return new RegExp(`(?<![a-z0-9])([!\\u2757\\u2755]\\s*)?(?:${alt})(?![a-z0-9])`, 'g');
  };
  const fuzzy = term => new RegExp(`${term.slice(0, -3).split(' ').filter(Boolean).map(escape).join('\\s*')}\\s*\\S{0,2}${escape(term.slice(-3))}`);
  const create = data => {
    const officialTitle = words([...data.official.title, ...data.official.worlds]);
    const officialTags = data.official.tag_patterns.map(p => new RegExp(p));
    const worldTags = new Set([...data.official.worlds, ...data.official.worlds_tags_only].map(normalize));
    const games = Object.entries(data.games).map(([game, spec]) => [game, words(spec.words), spec.tag_patterns.map(p => new RegExp(p))]);
    const metadata = (title, tags) => {
      title = normalize(title);
      tags = tags.map(t => normalize(t).replace(/ /g, ''));
      const found = {
        declared: {},
        tagged: {},
        commands: {},
        official: []
      };
      for (const [game, pattern, tagPatterns] of games) {
        for (const match of title.matchAll(pattern)) {
          const kind = match[1] ? 'commands' : 'declared';
          (found[kind][game] = found[kind][game] || []).push(match[0]);
        }
        const hits = tags.filter(t => tagPatterns.some(p => p.test(t)));
        if (hits.length) {
          found.tagged[game] = hits;
        }
      }
      found.official = [...title.matchAll(officialTitle)].filter(m => !m[1]).map(m => m[0]).concat(tags.filter(t => worldTags.has(t) || officialTags.some(p => p.test(t))));
      return found;
    };
    return (title, tags) => {
      const found = metadata(title, tags);
      const strong = [...new Set([...Object.keys(found.declared), ...Object.keys(found.tagged)])].sort();
      if (strong.length && !found.official.length) {
        return {
          verdict: 'other',
          reason: `declared/tagged: ${strong.join(', ')}`,
          found
        };
      }
      if (found.official.length && !strong.length) {
        return {
          verdict: 'tibia',
          reason: 'official world or Tibia Global',
          found
        };
      }
      // The screen breaks ties: an OTServer-only client beats a "tibiaglobal" tag.

      if (strong.length) {
        return {
          verdict: 'undetermined',
          reason: 'evidence for Tibia and another game',
          found
        };
      }
      if (Object.keys(found.commands).length) {
        return {
          verdict: 'undetermined',
          reason: 'server only as a chat command',
          found
        };
      }
      return {
        verdict: 'undetermined',
        reason: 'no decisive evidence',
        found
      };
    };
  };
  globalThis.TwitchCleanTibiaClassify = {
    create,
    normalize
  };
})();
