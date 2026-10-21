// Prints the extension classifier's verdicts for the live sample, for
// tests/test_twitch_evidence.py to compare with tools/twitch_evidence.py.
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const ext = path.join(root, 'extensions/twitch-clean/extension');
require(path.join(ext, 'tibia-evidence.js'));
require(path.join(ext, 'tibia-classify.js'));
const classify = globalThis.TwitchCleanTibiaClassify.create(globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE);
const data = path.join(root, 'research/twitch/data/2026-10-21/live-2015');
const out = {};
for (const s of JSON.parse(fs.readFileSync(path.join(data, 'streams.json'), 'utf8'))) {
    const file = path.join(data, 'ocr', `${s.channel}.txt`);
    const ocr = fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null;
    out[s.channel] = [classify(s.title, s.tags || [], ocr).verdict, classify(s.title, s.tags || [], null).verdict];
}
console.log(JSON.stringify(out));
