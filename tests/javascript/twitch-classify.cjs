// Prints the extension classifier's verdicts and scores for the audited 2026-10-21 capture
// the 562-stream live capture (keys prefixed live:) and tests/data/tibia-classify-cases.json (case:),
// for tests/python/test_twitch_evidence.py to compare with tools/twitch_evidence.py.
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../..');
const ext = path.join(root, 'extension/src');
require(path.join(ext, 'tibia-evidence.js'));
require(path.join(ext, 'tibia-classify.js'));
const classify = globalThis.TwitchCleanTibiaClassify.create(globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE);
const audit = JSON.parse(fs.readFileSync(path.join(root, 'research/twitch/data/2026-10-21/analysis/classificacao.json'), 'utf8'));
const out = {};
for (const row of audit.classificacao) {
  const tags = row.tags_originais.split('|').map(t => t.trim()).filter(Boolean);
  const r = classify(row.titulo_original, tags, row.canal);
  out[row.canal] = [r.verdict, r.score, r.found.model];
}
const live = JSON.parse(fs.readFileSync(path.join(root, 'research/twitch/data/2026-10-21/live-2115/streams.json'), 'utf8'));
for (const s of live) {
  const r = classify(s.title, s.tags, s.channel);
  out[`live:${s.channel}`] = [r.verdict, r.score, r.found.model];
}
const cases = JSON.parse(fs.readFileSync(path.join(root, 'tests/data/tibia-classify-cases.json'), 'utf8')).cases;
cases.forEach((c, i) => {
  const r = classify(c.title, c.tags || [], c.channel || '');
  out[`case:${i}`] = [r.verdict, r.score, r.found.model];
});
console.log(JSON.stringify(out));
