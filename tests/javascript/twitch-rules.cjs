// Rule updates must never downgrade the evidence bundled with an extension update.
const assert = require('node:assert/strict');
require('../../extension/src/tibia-evidence.js');
require('../../extension/src/tibia-classify.js');
require('../../extension/src/tibia-rules.js');
const bundled = globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE;
const R = globalThis.TibiaAntiAdRules;
const old = structuredClone(bundled);
delete old.revision;
old.model = { confident: 6, features: {} }; // The old rule-assisted format is incompatible.
assert.equal(R.current({ data: old }), bundled, 'Older cached evidence must fall back to bundled rules');
assert.equal(R.valid(old), false, 'Older downloads must be rejected');
for (const revision of [-1, 1.5, '999', Infinity]) {
  assert.equal(R.valid({ ...bundled, revision }), false, `Invalid revision ${revision}`);
}
const newer = { ...bundled, revision: bundled.revision + 1 };
assert.equal(R.current({ data: newer }), newer, 'Newer compatible rules must still update');
assert.equal(R.valid({ ...bundled, model: { ...bundled.model, format: 'unsupported' } }), false);
assert.equal(R.valid({ ...bundled, model: { ...bundled.model, weights: {} } }), false);
assert.equal(R.current(null), bundled);

(async () => {
  let stored = { tibiaEvidence: { data: newer } };
  const api = { storage: { local: {
    set: async values => { Object.assign(stored, values); },
    remove: async key => { delete stored[key]; },
  } } };
  globalThis.fetch = async () => ({ ok: true, json: async () => old });
  assert.equal((await R.update(api)).ok, false);
  assert.equal(stored.tibiaEvidence.data, newer, 'Rejected update preserves the last good rules');
  globalThis.fetch = async () => ({ ok: true, json: async () => bundled });
  assert.equal((await R.update(api)).ok, true);
  assert.equal(stored.tibiaEvidence.data, bundled);
  assert.equal(stored.tibiaEvidenceError, undefined);
  console.log('PASS evidence revision: old cache/download rejection, newer rules and error recovery');
})().catch(error => { console.error(error); process.exit(1); });
