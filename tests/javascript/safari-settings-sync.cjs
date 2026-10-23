// Native popover edits must reach an already focused Twitch page, not wait
// for the popover to close, another focus event, or a one-minute alarm.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = name => fs.readFileSync(path.join(__dirname, '../../extension/src', name), 'utf8');
const flush = async () => { for (let i = 0; i < 8; i++) await new Promise(resolve => setImmediate(resolve)); };

(async () => {
  let stored = {}, nativeSettings = {}, changedAt = 0, nativeCalls = 0;
  const changes = [], messages = [], timers = [], attributes = new Map();
  const window = { addEventListener() {}, setInterval: (callback, delay) => timers.push({ callback, delay }) };
  window.top = window;
  const document = { hidden: false, addEventListener() {}, documentElement: {
    setAttribute: (key, value) => attributes.set(key, value), removeAttribute: key => attributes.delete(key),
  } };
  let handler;
  const api = {
    storage: { local: {
      get: async defaults => defaults ? { ...defaults, ...stored } : { ...stored },
      set: async values => {
        Object.assign(stored, values);
        changes.forEach(listener => listener(Object.fromEntries(Object.entries(values).map(([key, newValue]) => [key, { newValue }])), 'local'));
      },
    }, onChanged: { addListener: listener => changes.push(listener) } },
    runtime: {
      getURL: () => 'safari-web-extension://test/',
      onInstalled: { addListener() {} }, onStartup: { addListener() {} },
      onMessage: { addListener: listener => { handler = listener; } },
      sendNativeMessage: async () => {
        nativeCalls++;
        return { settings: nativeSettings, settingsChangedAt: changedAt };
      },
      sendMessage: message => {
        messages.push(message);
        return new Promise(resolve => handler(message, {}, resolve));
      },
    },
    alarms: { create() {}, onAlarm: { addListener() {} } },
    declarativeNetRequest: { updateEnabledRulesets: async () => {} },
  };
  const context = vm.createContext({ browser: api, window, document, location: { hostname: 'www.twitch.tv' },
    localStorage: { getItem: () => null, setItem() {} }, console,
    TibiaAntiAdRules: { PERIOD_MINUTES: 360, update: async () => ({}) },
  });
  vm.runInContext(read('settings.js'), context);
  vm.runInContext(read('background.js'), context);
  vm.runInContext(read('settings-bridge.js'), context);
  await flush();
  assert.equal(timers.length, 1, 'Safari must check native edits while the page stays focused');
  assert.ok(timers[0].delay <= 1000);
  nativeSettings = { tibiaFilter: false }; changedAt++;
  timers[0].callback(); await flush();
  assert.equal(stored.tibiaFilter, false);
  assert.ok(attributes.get('data-tibia-anti-ad-off').split(' ').includes('tibia'));
  nativeSettings = { tibiaFilter: true }; changedAt++;
  timers[0].callback(); await flush();
  assert.equal(stored.tibiaFilter, true);
  assert.ok(!attributes.get('data-tibia-anti-ad-off')?.split(' ').includes('tibia'));
  const before = nativeCalls;
  document.hidden = true;
  timers[0].callback(); await flush();
  assert.equal(nativeCalls, before, 'background tabs must not poll native settings');
  document.hidden = false;
  const sent = messages.length;
  timers[0].callback(); timers[0].callback(); timers[0].callback();
  await flush();
  assert.equal(messages.length, sent + 1, 'coalesce checks while a native sync is pending');
  console.log('PASS Safari: native popover toggles reach a focused page, restore the CSS group, and skip hidden/in-flight checks');
})().catch(error => { console.error(error); process.exitCode = 1; });
