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
  const create = data => {
    const official = matcher(data.official_text);
    const servers = Object.entries(data.server_text).map(([game, terms]) => [game, matcher(terms)]);
    return (title, tags) => {
      const text = normalize(`${title} ${tags.join(' ')}`);
      const serverText = {};
      for (const [game, match] of servers) {
        const found = match(text);
        if (found.length) {
          serverText[game] = found;
        }
      }
      const found = {
        official_text: official(text),
        server_text: serverText
      };
      const namesServer = Object.keys(serverText).length > 0;
      // A server named only as a chat command ("!rubinot") is often a sponsor.
      const onlyCommands = namesServer && Object.values(serverText).flat().every(term => new RegExp(`!\\s*${escape(term)}`).test(text) && !new RegExp(`(^|[^!\\w])${escape(term)}`).test(text.replace(new RegExp(`!\\s*${escape(term)}`, 'g'), '')));
      // 1. The screen shows an OTServer-only client.

      //    can only overturn it when the server is just a "!command" and the
      //    screen shows a Tibia-style client (a sponsor on an official stream).
      if (namesServer && !found.official_text.length) {
        if (onlyCommands) {
          return {
            verdict: 'undetermined',
            reason: 'server only as a chat command, Tibia-style client on screen',
            found
          };
        }
        return {
          verdict: 'other',
          reason: 'names another game (text only, screen not read yet)',
          found
        };
      }
      if (found.official_text.length && !namesServer) {
        return {
          verdict: 'tibia',
          reason: 'official marker in text and a Tibia-style client on screen',
          found
        };
      }
      return {
        verdict: 'undetermined',
        reason: 'missing or conflicting evidence',
        found
      };
    };
  };
  globalThis.TwitchCleanTibiaClassify = {
    create,
    normalize
  };
})();
