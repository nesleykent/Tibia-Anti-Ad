// Full-result Python/browser parity over all captures and controls.
const fs = require('node:fs');
require('../../extension/src/tibia-evidence.js');
require('../../extension/src/tibia-classify.js');
const classify = TwitchCleanTibiaClassify.create(TWITCH_CLEAN_TIBIA_EVIDENCE);
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(rows.map(([title, tags]) => classify(title, tags))));
