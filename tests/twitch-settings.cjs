// Mocked settings checks for Tibia Anti-Ad; no browser and no network.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const EXT = path.join(__dirname, '..', 'extensions/tibia-anti-ad/extension');
const read = name => fs.readFileSync(path.join(EXT, name), 'utf8');
// Objects from a vm context have another realm's prototypes; compare plain copies.
const plain = value => JSON.parse(JSON.stringify(value));
const settingsSource = read('settings.js');

const loadSettings = (context = vm.createContext({})) => {
  vm.runInContext(settingsSource, context);
  return context.TibiaAntiAdSettings;
};

// settings.js: defaults, master switch, CSS groups and rulesets.
{
  const S = loadSettings();
  const defaults = S.resolve();
  assert.equal(defaults.enabled, true);
  assert.equal(defaults.hideAdBreakBanner, false);
  assert.deepEqual(plain(S.resolve({ blockAds: 'no', tibiaFilter: false, unknown: true })), { ...plain(defaults), tibiaFilter: false });
  assert.deepEqual(plain(S.cssState(defaults)), { off: [], on: [] });
  assert.deepEqual(plain(S.cssState({ ...defaults, hideUpsells: false, hideAdBreakBanner: true }).off), ['upsells']);
  assert.deepEqual(plain(S.cssState({ ...defaults, hideAdBreakBanner: true }).on), ['adbreak']);
  const paused = { ...defaults, enabled: false, hideAdBreakBanner: true };
  assert.deepEqual(plain(S.cssState(paused).off), plain(Object.values(S.CSS_OPT_OUT)));
  assert.deepEqual(plain(S.cssState(paused).on), []);
  assert.deepEqual(plain((S.rulesetState(defaults))), { enableRulesetIds: ['twitch_ads', 'twitch_tracking'], disableRulesetIds: [] });
  assert.deepEqual(plain((S.rulesetState({ ...defaults, blockTracking: false }))), { enableRulesetIds: ['twitch_ads'], disableRulesetIds: ['twitch_tracking'] });
  assert.deepEqual(plain((S.rulesetState(paused))), { enableRulesetIds: [], disableRulesetIds: ['twitch_ads', 'twitch_tracking'] });
  console.log('PASS settings.js: defaults, master switch, CSS groups and rulesets');
}

// settings-bridge.js: cached copy first, then storage, then live changes.
(async () => {
  const pageStorage = new Map([['tibia-anti-ad:settings', JSON.stringify({ hideUpsells: false })]]);
  const attributes = new Map();
  let stored = { hideCookieBanner: false };
  const listeners = [];
  const context = vm.createContext({
    location: { hostname: 'www.twitch.tv' },
    document: {
      documentElement: {
        setAttribute: (name, value) => attributes.set(name, value),
        removeAttribute: name => attributes.delete(name),
      },
    },
    localStorage: {
      getItem: key => pageStorage.get(key) ?? null,
      setItem: (key, value) => pageStorage.set(key, String(value)),
    },
    chrome: {
      storage: {
        local: { get: defaults => Promise.resolve({ ...defaults, ...stored }) },
        onChanged: { addListener: listener => listeners.push(listener) },
      },
    },
  });
  loadSettings(context);
  vm.runInContext(read('settings-bridge.js'), context);
  assert.equal(attributes.get('data-tibia-anti-ad-off'), 'upsells', 'cached copy applies synchronously');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(attributes.get('data-tibia-anti-ad-off'), 'cookies');
  assert.equal(JSON.parse(pageStorage.get('tibia-anti-ad:settings')).hideCookieBanner, false);
  assert.ok(!Object.keys(JSON.parse(pageStorage.get('tibia-anti-ad:settings'))).some(key => key.startsWith('site:')), 'fansite switches stay out of Twitch');
  stored = { removeStreamAds: false, hideAdBreakBanner: true };
  listeners.forEach(listener => listener({ removeStreamAds: { newValue: false } }, 'local'));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(attributes.has('data-tibia-anti-ad-off'), false);
  assert.equal(attributes.get('data-tibia-anti-ad-on'), 'adbreak');
  assert.equal(JSON.parse(pageStorage.get('tibia-anti-ad:settings')).removeStreamAds, false);
  stored = { enabled: false };
  listeners.forEach(listener => listener({ enabled: { newValue: false } }, 'local'));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(attributes.get('data-tibia-anti-ad-off'), 'ads upsells prompts signup cookies tibia');
  console.log('PASS settings-bridge.js: cached copy, storage, live changes and master switch');
})().then(() => {
  // page.js: each part follows the mirrored settings.
  const page = read('page.js');
  const run = mirrored => {
    const storage = new Map();
    if (mirrored !== undefined) { storage.set('tibia-anti-ad:settings', mirrored); }
    class OriginalWorker { constructor(url) { this.url = url; } addEventListener() {} postMessage() {} }
    const originalFetch = async () => { throw new Error('Unexpected network request'); };
    const document = {
      readyState: 'complete',
      get hidden() { return true; },
      get webkitHidden() { return true; },
      addEventListener() {},
      querySelector() { return null; },
      getElementsByTagName() { return []; },
    };
    const sandbox = {
      Worker: OriginalWorker, fetch: originalFetch, document,
      navigator: { userAgent: 'Safari mock' },
      localStorage: { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, String(value)) },
      addEventListener() {}, setInterval() { return 1; }, setTimeout() { return 1; }, clearInterval() {}, clearTimeout() {},
      URL, Blob, console: { log() {}, warn() {}, error() {} },
    };
    sandbox.window = sandbox;
    vm.runInContext(page, vm.createContext(sandbox), { timeout: 3000 });
    return {
      vaft: sandbox.Worker !== OriginalWorker && sandbox.fetch !== originalFetch && sandbox.twitchAdSolutionsVersion === 24,
      quality: storage.get('video-quality') === '{"default":"chunked"}',
      hidden: document.hidden,
    };
  };
  assert.deepEqual(run(undefined), { vaft: true, quality: true, hidden: false });
  assert.deepEqual(run('not json'), { vaft: true, quality: true, hidden: false });
  assert.deepEqual(run('{"sourceQuality":false}'), { vaft: true, quality: false, hidden: false });
  assert.deepEqual(run('{"removeStreamAds":false}'), { vaft: false, quality: true, hidden: false });
  assert.deepEqual(run('{"removeStreamAds":false,"backgroundQuality":false}'), { vaft: false, quality: true, hidden: true });
  assert.deepEqual(run('{"enabled":false}'), { vaft: false, quality: false, hidden: true });
  console.log('PASS page.js: Source quality, vaft and background quality follow the settings');
}).catch(error => { console.error(error); process.exit(1); });

// settings.js with sites.js: one switch per fansite, on by default.
{
  const context = vm.createContext({});
  vm.runInContext(read('sites.js'), context);
  const S = loadSettings(context);
  const defaults = S.resolve();
  assert.equal(S.SITES.length, 15);
  for (const site of S.SITES) {
    assert.equal(defaults[site.key], true);
    assert.equal(S.RULESETS[site.key], site.ruleset);
    assert.equal(S.CSS_OPT_OUT[site.key], site.domain);
  }
  const off = { ...defaults, 'site:tibiopedia.pl': false };
  assert.ok(S.rulesetState(off).disableRulesetIds.includes('site_tibiopedia_pl'));
  assert.ok(S.rulesetState(defaults).enableRulesetIds.includes('site_tibiawiki_com_br'));
  assert.deepEqual(plain(S.cssState(off).off), ['tibiopedia.pl']);
  console.log('PASS settings.js: every fansite has a switch, ruleset and CSS gate');
}
