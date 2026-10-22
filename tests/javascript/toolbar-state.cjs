// Exercise the real background script with Safari/Chrome API contracts.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../../extension/src/background.js'), 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));

async function scenario(safari) {
    let stored = { enabled: false };
    let failRules = false;
    let failIcon = false;
    const events = {};
    const icons = [], titles = [], warnings = [];
    const api = {
        runtime: {
            getURL: () => safari ? 'safari-web-extension://test/' : 'chrome-extension://test/',
            onInstalled: { addListener: fn => { events.install = fn; } },
            onStartup: { addListener: fn => { events.start = fn; } },
            onMessage: { addListener() {} },
        },
        storage: { onChanged: { addListener: fn => { events.change = fn; } } },
        alarms: { create() {}, onAlarm: { addListener() {} } },
        declarativeNetRequest: { async updateEnabledRulesets() { if (failRules) { throw Error('rules failed'); } } },
        action: {
            async setIcon(value) { if (failIcon) { throw Error('icon failed'); } icons.push(value); },
            async setTitle(value) { titles.push(value.title); },
        },
    };
    const context = vm.createContext({
        browser: api,
        TibiaAntiAdSettings: { load: async () => ({ ...stored }), RULESETS: {}, rulesetState: () => ({}) },
        TibiaAntiAdRules: { PERIOD_MINUTES: 60, update: async () => ({}) },
        console: { warn: (...args) => warnings.push(args) },
    });
    vm.runInContext(source, context);
    await flush();
    assert.equal(titles.at(-1), 'Tibia Anti-Ad — Blocking disabled', 'restore stored state on background load');
    if (safari) {
        assert.ok(icons.at(-1).path['16'].includes('inactive-16.png'));
    } else {
        assert.ok(icons.at(-1).path['16'].includes('chrome-toolbar/inactive-16.png'));
    }
    stored = { enabled: true };
    events.change({ enabled: { newValue: true } }, 'local');
    await flush();
    assert.equal(titles.at(-1), 'Tibia Anti-Ad — Blocking enabled');
    if (safari) { assert.ok(icons.at(-1).path['38'].includes('active-38.png')); }
    else { assert.ok(icons.at(-1).path['128'].includes('chrome-toolbar/active-128.png')); }
    const count = titles.length;
    events.change({ enabled: {} }, 'sync');
    await flush();
    assert.equal(titles.length, count, 'ignore another storage area');
    stored = { enabled: false };
    events.start();
    events.install();
    await flush();
    assert.equal(titles.at(-1), 'Tibia Anti-Ad — Blocking disabled');
    failRules = true;
    stored = { enabled: true };
    events.change({ enabled: {} }, 'local');
    await flush();
    assert.equal(titles.at(-1), 'Tibia Anti-Ad — Blocking enabled', 'ruleset failure must not skip toolbar sync');
    assert.ok(warnings.length);
    failIcon = true;
    events.change({ enabled: {} }, 'local');
    await flush();
    failIcon = false;
    stored = { enabled: false };
    events.change({ enabled: {} }, 'local');
    await flush();
    assert.equal(titles.at(-1), 'Tibia Anti-Ad — Blocking disabled', 'recover after an API failure');
    console.log(`PASS ${safari ? 'Safari' : 'Chrome'}: toolbar startup, toggles, lifecycle, errors and recovery`);
}
scenario(true).then(() => scenario(false)).catch(error => { console.error(error); process.exitCode = 1; });
