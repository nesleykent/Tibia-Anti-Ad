// Tibia Anti-Ad: JavaScript port of Evidence.classify() in tools/twitch_evidence.py.
// Keep the two in step; tests/python/test_twitch_evidence.py checks they agree.
//
// Text is normalized (accents, lookalike letters, fancy fonts, leetspeak,
// repeated and spaced-out letters), then every server, world or official
// mention becomes a weighted signal for "other" or "tibia". Names listed as
// fuzzy also match one spelling mistake away (two for long names). Words just
// before a mention weaken it ("n\u00e3o", "ex", "vs"...). Signals of one side combine
// with diminishing returns, so weak context never decides alone; a side wins
// when it reaches the threshold and leads by the margin.
(() => {
  'use strict';

  const COMMAND = '!\u2757\u2755';
  // Lookalike letters NFKD keeps: Cyrillic, Greek and small capitals.
  const LOOKALIKE = {
    \u0430: 'a',
    \u0432: 'b',
    \u0435: 'e',
    \u043a: 'k',
    \u043c: 'm',
    \u043d: 'h',
    \u043e: 'o',
    \u0440: 'p',
    \u0441: 'c',
    \u0442: 't',
    \u0443: 'y',
    \u0445: 'x',
    \u0456: 'i',
    \u0458: 'j',
    \u0455: 's',
    \u0501: 'd',
    \u0261: 'g',
    \u03b1: 'a',
    \u03b2: 'b',
    \u03b5: 'e',
    \u03b9: 'i',
    \u03ba: 'k',
    \u03bd: 'v',
    \u03bf: 'o',
    \u03c1: 'p',
    \u03c4: 't',
    \u03c5: 'u',
    \u03c7: 'x',
    \u1d00: 'a',
    \u0299: 'b',
    \u1d04: 'c',
    \u1d05: 'd',
    \u1d07: 'e',
    \u0262: 'g',
    \u029c: 'h',
    \u026a: 'i',
    \u1d0a: 'j',
    \u1d0b: 'k',
    \u029f: 'l',
    \u1d0d: 'm',
    \u0274: 'n',
    \u1d0f: 'o',
    \u1d18: 'p',
    \u0280: 'r',
    \ua731: 's',
    \u1d1b: 't',
    \u1d1c: 'u',
    \u1d20: 'v',
    \u1d21: 'w',
    \u028f: 'y',
    \u1d22: 'z'
  };
  const LOOKALIKE_RE = new RegExp(`[${Object.keys(LOOKALIKE).join('')}]`, 'g');
  const LEET = {
    0: 'o',
    1: 'i',
    3: 'e',
    4: 'a',
    5: 's',
    7: 't'
  };
  const escape = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const normalize = s => String(s).normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(LOOKALIKE_RE, c => LOOKALIKE[c]).replace(/\s+/g, ' ').trim();
  const squeeze = s => s.replace(/([a-z])\1+/g, '$1');
  const leet = s => /[a-z]/.test(s) && /[0-9]/.test(s) ? s.replace(/[013457]/g, d => LEET[d]) : s;
  const words = list => new RegExp(`(?:^| )(?:${list.map(escape).join('|')})(?: |$)`);

  // Optimal string alignment distance, or limit + 1 once it exceeds limit.
  const distance = (a, b, limit) => {
    let before = null;
    let previous = Array.from({
      length: b.length + 1
    }, (_, j) => j);
    for (let i = 1; i <= a.length; i++) {
      const row = [i];
      let least = i;
      for (let j = 1; j <= b.length; j++) {
        let value = Math.min(previous[j] + 1, row[j - 1] + 1, previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          value = Math.min(value, before[j - 2] + 1);
        }
        row.push(value);
        least = Math.min(least, value);
      }
      if (least > limit) {
        return limit + 1;
      }
      before = previous;
      previous = row;
    }
    return previous[b.length];
  };

  // Words of the text with their position, whether a "!" (chat command) or a
  // "[" / "(" comes right before, and runs of spaced-out letters joined.
  const tokenize = text => {
    const raw = [...text.matchAll(/[a-z0-9]+/g)].map(m => {
      const before = text.slice(0, m.index).trimEnd();
      return {
        text: m[0],
        start: m.index,
        end: m.index + m[0].length,
        command: m.index > 0 && COMMAND.includes(text[m.index - 1]),
        bracket: before.endsWith('[') || before.endsWith('(')
      };
    });
    const tokens = [];
    for (let i = 0; i < raw.length;) {
      let j = i;
      while (j + 1 < raw.length && raw[j].text.length === 1 && raw[j + 1].text.length === 1 && raw[j + 1].start - raw[j].end === 1 && ' .-_*\u00b7\u2022'.includes(text[raw[j].end])) {
        j++;
      }
      if (j - i >= 3) {
        tokens.push({
          ...raw[i],
          text: raw.slice(i, j + 1).map(t => t.text).join(''),
          end: raw[j].end
        });
        i = j + 1;
      } else {
        tokens.push(raw[i]);
        i++;
      }
    }
    return tokens;
  };
  const create = data => {
    const W = data.weights;
    const {
      threshold,
      margin,
      stale_tags: staleTags
    } = data.decision;
    const protectedWords = new Set(data.fuzzy.protected.map(w => squeeze(normalize(w))));

    // One lexicon for every mention: single words by squeezed spelling,
    // phrases by their squeezed words; phrases of 8+ letters also match written together.
    const singles = new Map();
    const phrases = new Map();
    const fuzzy = [];
    const add = (term, entry, isFuzzy) => {
      const parts = normalize(term).split(/[^a-z0-9]+/).filter(Boolean).map(squeeze);
      const key = squeeze(parts.join(''));
      if (parts.length > 1) {
        if (!phrases.has(parts.join(' '))) {
          phrases.set(parts.join(' '), entry);
        }
        if (key.length < 8) {
          return;
        }
      }
      if (!singles.has(key)) {
        singles.set(key, entry);
      }
      if (isFuzzy && key.length >= 6) {
        fuzzy.push({
          key,
          entry
        });
      }
    };
    // Official first: a spelling mistake equally close to a world and a server counts as the world.
    for (const term of data.official.title) {
      add(term, {
        side: 'tibia',
        kind: normalize(term) === 'global' ? 'global' : 'official',
        game: 'Tibia'
      });
    }
    for (const world of data.official.worlds) {
      add(world, {
        side: 'tibia',
        kind: 'official',
        game: 'Tibia'
      }, true);
    }
    for (const world of data.official.worlds_tags_only) {
      add(world, {
        side: 'tibia',
        kind: 'bracketed',
        game: 'Tibia'
      });
    }
    const games = Object.entries(data.games).map(([game, spec]) => {
      const fuzzyNames = new Set((spec.fuzzy || []).map(normalize));
      for (const term of spec.words) {
        add(term, {
          side: 'other',
          kind: 'name',
          game
        }, fuzzyNames.has(normalize(term)));
      }
      for (const term of spec.fuzzy || []) {
        add(term, {
          side: 'other',
          kind: 'name',
          game
        }, true);
      }
      for (const world of spec.worlds || []) {
        add(world, {
          side: 'other',
          kind: 'world',
          game
        });
      }
      return {
        game,
        titlePatterns: (spec.title_patterns || []).map(p => new RegExp(p, 'g')),
        tagPatterns: spec.tag_patterns.map(p => new RegExp(p))
      };
    });
    const longest = Math.max(3, ...[...phrases.keys()].map(k => k.split(' ').length));
    // A server's name written with "ot" (hegalot, deusot): the server itself.
    const server = key => {
      const entry = singles.get(key);
      if (entry) {
        return entry;
      }
      const name = key.endsWith('ot') && key.length >= 6 ? singles.get(key.slice(0, -2)) : undefined;
      return name && name.side === 'other' ? name : undefined;
    };
    const D = data.context.domains;
    const domainRe = new RegExp(`(?<![a-z0-9@._-])((?:[a-z0-9-]+\\.)+(?:${D.tlds.join('|')}))(?![a-z0-9-])`, 'g');
    const within = (domain, list) => list.some(d => domain === d || domain.endsWith(`.${d}`));
    const channelKeys = [...singles].filter(([key, entry]) => entry.side === 'other' && key.length >= 6).sort((a, b) => b[0].length - a[0].length);
    const officialTags = data.official.tag_patterns.map(p => new RegExp(p));
    const worldTags = new Set([...data.official.worlds, ...data.official.worlds_tags_only].map(normalize));
    const context = side => data.context[side].map(c => ({
      ...c,
      side,
      re: new RegExp(c.pattern, 'g')
    }));
    const contexts = [...context('other'), ...context('tibia')];
    const modifiers = Object.entries(data.context.modifiers).filter(([name]) => !name.startsWith('_')).map(([name, m]) => ({
      name,
      factor: m.factor,
      before: words(m.words),
      after: m.after ? words(m.after) : null
    }));
    const fuzzyUi = term => new RegExp(`${term.slice(0, -3).split(' ').filter(Boolean).map(escape).join('\\s*')}\\s*\\S{0,2}${escape(term.slice(-3))}`);
    // The closest fuzzy name to a word, if it is a plausible misspelling.
    const misspelling = (key, maxDistance) => {
      if (key.length < 5 || protectedWords.has(key) || singles.has(key)) {
        return null;
      }
      let best = null;
      for (const f of fuzzy) {
        const limit = Math.min(maxDistance, f.key.length >= 10 ? 2 : 1);
        if (f.key[0] !== key[0] || Math.abs(f.key.length - key.length) > limit) {
          continue;
        }
        const d = distance(key, f.key, limit);
        if (d <= limit && (!best || d < best.distance)) {
          best = {
            entry: f.entry,
            distance: d
          };
        }
      }
      return best;
    };

    // Every lexicon mention in the tokens, longest first.
    const mentions = (tokens, maxDistance) => {
      const found = [];
      for (let i = 0; i < tokens.length;) {
        let match = null;
        for (let n = Math.min(longest, tokens.length - i); n >= 1 && !match; n--) {
          const parts = tokens.slice(i, i + n).map(t => squeeze(t.text));
          const key = squeeze(parts.join(''));
          const entry = n === 1 ? server(key) || server(squeeze(leet(tokens[i].text))) : phrases.get(parts.join(' ')) || (key.length >= 8 ? singles.get(key) : undefined);
          if (entry) {
            match = {
              entry,
              n,
              distance: 0
            };
          }
        }
        if (!match) {
          const near = misspelling(squeeze(leet(tokens[i].text)), maxDistance);
          if (near) {
            match = {
              ...near,
              n: 1
            };
          }
        }
        if (match) {
          const last = tokens[i + match.n - 1];
          found.push({
            ...match.entry,
            distance: match.distance,
            index: i,
            n: match.n,
            start: tokens[i].start,
            end: last.end,
            text: tokens.slice(i, i + match.n).map(t => t.text).join(' '),
            command: tokens[i].command,
            bracket: tokens[i].bracket
          });
          i += match.n;
        } else {
          i++;
        }
      }
      return found;
    };

    // The strongest weakening word around a mention: 1 when there is none.
    const modifier = (text, tokens, mention) => {
      const from = mention.index ? tokens[Math.max(0, mention.index - 2)].start : mention.start;
      const clause = text.slice(from, mention.start).split(/[|/,.;:!?()[\]{}\u2757\u2755]/).pop();
      const before = (clause.match(/[a-z0-9]+/g) || []).join(' ');
      const after = tokens.slice(mention.index + mention.n, mention.index + mention.n + 1).map(t => t.text).join(' ');
      let factor = 1;
      for (const m of modifiers) {
        if (m.before.test(before) || m.after && m.after.test(after)) {
          factor = Math.min(factor, m.factor);
        }
      }
      return factor;
    };
    const signal = (side, source, game, text, weight) => ({
      side,
      source,
      game,
      text,
      weight
    });
    const titleSignals = title => {
      const tokens = tokenize(title);
      const found = mentions(tokens, 2);
      const signals = [];
      const servers = found.filter(m => m.side === 'other');
      for (const m of found) {
        let weight;
        if (m.side === 'other') {
          weight = m.kind === 'world' ? W.world : m.distance === 0 ? W.title : m.distance === 1 ? W.title_fuzzy : W.title_far;
          if (m.command) {
            weight -= W.title - W.command;
          }
        } else {
          if (m.command || m.kind === 'bracketed' && !m.bracket) {
            continue;
          }
          // "Future OT Global": "global" right after a server is part of its name.
          if (m.kind === 'global' && servers.some(s => s.index + s.n === m.index && !title.slice(s.end, m.start).trim())) {
            continue;
          }
          weight = m.distance ? W.official_fuzzy : m.kind === 'global' ? W.official_global : m.kind === 'bracketed' ? W.official_bracketed : W.official_title;
        }
        const source = m.side === 'other' && m.command ? 'command' : 'title';
        signals.push({
          ...signal(m.side, source, m.game, m.text, weight * modifier(title, tokens, m)),
          kind: m.kind,
          distance: m.distance
        });
      }
      const spans = [...found];
      const overlaps = (start, end) => spans.some(m => start < m.end && m.start < end);
      for (const {
        game,
        titlePatterns
      } of games) {
        for (const p of titlePatterns) {
          for (const m of title.matchAll(p)) {
            if (overlaps(m.index, m.index + m[0].length)) {
              continue;
            }
            spans.push({
              start: m.index,
              end: m.index + m[0].length
            });
            const command = m.index > 0 && COMMAND.includes(title[m.index - 1]);
            signals.push(signal('other', command ? 'command' : 'title', game, m[0], command ? W.command : W.pattern));
          }
        }
      }
      // Websites: an OTServer's own site, or a self-hosted (dynamic DNS) server.
      for (const m of title.matchAll(domainRe)) {
        const domain = m[1];
        if (overlaps(m.index, m.index + domain.length) || within(domain, D.ignore)) {
          continue;
        }
        signals.push(within(domain, D.self_hosted) ? signal('other', 'title', 'Other OTServers', domain, D.self_hosted_weight) : signal('other', 'context', 'server website', domain, D.weight));
      }
      for (const c of contexts) {
        const m = [...title.matchAll(c.re)].find(x => !overlaps(x.index, x.index + x[0].length));
        if (m) {
          signals.push(signal(c.side, 'context', c.label, m[0], c.weight));
        }
      }
      return signals;
    };
    const tagSignals = tags => {
      const signals = [];
      for (const tag of new Set(tags.map(t => normalize(t).replace(/ /g, '')))) {
        if (worldTags.has(tag)) {
          signals.push(signal('tibia', 'tag', 'Tibia', tag, W.official_tag_world));
        } else if (officialTags.some(p => p.test(tag))) {
          signals.push(signal('tibia', 'tag', 'Tibia', tag, W.official_tag));
        }
        const game = games.find(g => g.tagPatterns.some(p => p.test(tag)));
        if (game) {
          signals.push(signal('other', 'tag', game.game, tag, W.tag));
          continue;
        }
        // Any server name or server world as a tag (hegal, infernum).
        const named = server(squeeze(leet(tag)));
        if (named && named.side === 'other') {
          signals.push(signal('other', 'tag', named.game, tag, W.tag));
          continue;
        }
        const near = !worldTags.has(tag) && misspelling(squeeze(leet(tag)), 1);
        if (near && near.entry.side === 'other') {
          signals.push(signal('other', 'tag', near.entry.game, tag, W.tag_fuzzy));
        }
      }
      return signals;
    };
    const channelSignals = channel => {
      const name = squeeze(normalize(channel || '').replace(/[^a-z0-9]/g, ''));
      const hit = channelKeys.find(([key]) => name.includes(key));
      return hit ? [signal('other', 'channel', hit[1].game, channel, W.channel)] : [];
    };
    // Strongest + half the next + a quarter the next...; each text counts once.
    const combine = signals => {
      const best = new Map();
      for (const s of signals) {
        const key = `${s.source}|${s.text}`;
        if (!best.has(key) || best.get(key) < s.weight) {
          best.set(key, s.weight);
        }
      }
      return [...best.values()].sort((a, b) => b - a).reduce((sum, w, i) => sum + w / 2 ** i, 0);
    };
    const describe = s => s.source === 'screen' ? `${s.game === 'OTServer client' ? 'OTServer-only client' : s.game} on screen: ${s.text}` : s.source === 'context' ? s.game : s.source === 'channel' ? `${s.game} in channel name` : s.source === 'command' ? `!${s.text.replace(/^[!\u2757\u2755]/, '')} command` : s.source === 'tag' ? `${s.game === 'Tibia' ? 'official' : s.game} tag ${s.text}` : s.side === 'tibia' ? `${s.text} in title` : `${s.game}${s.kind === 'world' ? ' world' : ''} in title${s.distance ? ` ("${s.text}")` : ''}`;
    const decide = signals => {
      const titleOther = combine(signals.filter(s => s.side === 'other' && (s.source === 'title' || s.source === 'command')));
      const titleTibia = signals.some(s => s.side === 'tibia' && s.source === 'title');
      // Official tags are often stale or generic: they count less against a server in the title.
      const stale = titleOther >= threshold && !titleTibia;
      const weighted = signals.map(s => stale && s.side === 'tibia' && s.source === 'tag' ? {
        ...s,
        weight: s.weight * staleTags
      } : s);
      const other = combine(weighted.filter(s => s.side === 'other'));
      const tibia = combine(weighted.filter(s => s.side === 'tibia'));
      const top = side => [...new Set(weighted.filter(s => s.side === side).sort((a, b) => b.weight - a.weight).map(describe))].slice(0, 3).join(', ');
      const score = {
        other: Math.round(other * 100) / 100,
        tibia: Math.round(tibia * 100) / 100
      };
      if (other >= threshold && other - tibia >= margin) {
        return {
          verdict: 'other',
          reason: top('other'),
          score
        };
      }
      if (tibia >= threshold && tibia - other >= margin) {
        return {
          verdict: 'tibia',
          reason: top('tibia'),
          score
        };
      }
      const reason = other >= threshold || tibia >= threshold ? 'evidence for Tibia and another game' : other || tibia ? 'not enough evidence' : 'no decisive evidence';
      return {
        verdict: 'undetermined',
        reason,
        score
      };
    };

    // when the title, tags and channel name leave the stream undetermined.
    return (title, tags, channel = '') => {
      const signals = [...titleSignals(normalize(title)), ...tagSignals(tags), ...channelSignals(channel)];
      let result = decide(signals);
      return {
        ...result,
        found: {
          signals: signals.map(s => ({
            ...s,
            weight: Math.round(s.weight * 100) / 100
          })),
          score: result.score
        }
      };
    };
  };
  globalThis.TwitchCleanTibiaClassify = {
    create,
    normalize
  };
})();
