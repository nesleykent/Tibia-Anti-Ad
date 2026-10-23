// Portable joint TF-IDF logistic inference. Weights are learned from labelled
// titles and tags; no name list, channel feature or heuristic decides a card.
// Keep feature extraction and scoring in step with tools/tibia_text.py and
// tools/twitch_evidence.py; the full captures are checked for numeric parity.
(() => {
  'use strict';

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
  const normalize = s => String(s).normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(LOOKALIKE_RE, c => LOOKALIKE[c]).replace(/\s+/g, ' ').trim();
  const featureId = text => {
    let result = 2166136261;
    for (let i = 0; i < text.length; i++) {
      result = Math.imul(result ^ text.charCodeAt(i), 16777619) >>> 0;
    }
    return result.toString(16).padStart(8, '0');
  };
  const textFeatures = text => {
    const tokens = (normalize(text).match(/[a-z0-9]+/g) || []).map(word => word.replace(/[0-9]+/g, '#'));
    const raw = new Set(tokens.map(word => `w:${word}`));
    for (let i = 1; i < tokens.length; i++) {
      raw.add(`b:${tokens[i - 1]} ${tokens[i]}`);
    }
    for (const word of new Set(tokens)) {
      const padded = `^${word}$`;
      for (const n of [3, 4, 5]) {
        for (let i = 0; i <= padded.length - n; i++) {
          raw.add(`c:${padded.slice(i, i + n)}`);
        }
      }
    }
    return new Set([...raw].map(featureId));
  };
  const featureFields = (title, tags) => {
    const tagFeatures = new Set();
    for (const tag of tags) {
      for (const feature of textFeatures(tag)) {
        tagFeatures.add(feature);
      }
    }
    return [textFeatures(title), tagFeatures];
  };
  const rounded = value => Math.round(value * 1000000) / 1000000;
  const create = data => {
    const model = data?.model;
    if (model?.format !== 'joint-text-logistic-v1' || !Number.isFinite(model.bias) || !Number.isFinite(model.threshold) || model.threshold <= 0 || !model.weights || typeof model.weights !== 'object' || Array.isArray(model.weights)) {
      throw new Error('Invalid statistical model');
    }
    for (const [key, value] of Object.entries(model.weights)) {
      if (!/^[0-9a-f]{8}$/.test(key) || !Array.isArray(value) || value.length !== 2 || !value.every(Number.isFinite) || value[1] <= 0) {
        throw new Error('Invalid statistical model weights');
      }
    }
    const classify = (title, tags, channel = '') => {
      const [titleFeatures, tagFeatures] = featureFields(title, tags);
      const known = [...new Set([...titleFeatures, ...tagFeatures])].filter(key => Object.hasOwn(model.weights, key)).sort();
      const norm = Math.sqrt(known.reduce((sum, key) => sum + model.weights[key][1] ** 2, 0));
      let titleValue = 0,
        tagValue = 0;
      for (const key of known) {
        const value = model.weights[key][0] / norm;
        const shared = titleFeatures.has(key) && tagFeatures.has(key);
        if (titleFeatures.has(key)) {
          titleValue += value / (shared ? 2 : 1);
        }
        if (tagFeatures.has(key)) {
          tagValue += value / (shared ? 2 : 1);
        }
      }
      const logit = model.bias + titleValue + tagValue;
      const probability = 1 / (1 + Math.exp(-Math.max(-40, Math.min(40, logit))));
      const verdict = known.length && logit >= model.threshold ? 'other' : known.length && logit <= -model.threshold ? 'tibia' : 'undetermined';
      const score = {
        other: rounded(probability),
        tibia: rounded(1 - probability)
      };
      const inputs = titleFeatures.size && tagFeatures.size ? 'title and tags' : titleFeatures.size ? 'title' : tagFeatures.size ? 'tags' : 'no text';
      const reason = `statistical model from ${inputs}: ${Math.round(probability * 100)}% other-game estimate`;
      return {
        verdict,
        reason,
        score,
        found: {
          signals: [{
            side: logit >= 0 ? 'other' : 'tibia',
            source: 'model',
            game: logit >= 0 ? 'Other games' : 'Tibia',
            text: inputs,
            weight: rounded(Math.abs(logit))
          }],
          model: {
            logit: rounded(logit),
            title: rounded(titleValue),
            tags: rounded(tagValue),
            bias: model.bias,
            matched: known.length
          },
          score
        }
      };
    };
    return classify;
  };
  globalThis.TwitchCleanTibiaClassify = {
    create,
    normalize,
    featureFields
  };
})();
