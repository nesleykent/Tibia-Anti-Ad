// Prints the extension classifier's verdicts for the audited 2026-10-21 capture,
// for tests/test_twitch_evidence.py to compare with tools/twitch_evidence.py.
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const ext = path.join(root, 'extensions/twitch-clean/extension');
require(path.join(ext, 'tibia-evidence.js'));
require(path.join(ext, 'tibia-classify.js'));
const classify = globalThis.TwitchCleanTibiaClassify.create(globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE);
const audit = JSON.parse(fs.readFileSync(path.join(root, 'research/twitch/data/2026-10-21/analysis/classificacao.json'), 'utf8'));
const out = {};
for (const row of audit.classificacao) {
    const tags = row.tags_originais.split('|').map(t => t.trim()).filter(Boolean);
    out[row.canal] = classify(row.titulo_original, tags).verdict;
}
console.log(JSON.stringify(out));
