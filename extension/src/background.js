// Tibia Anti-Ad background: keeps the network rulesets in step with the settings,
// and the Tibia filter's evidence up to date from GitHub (tibia-rules.js).
// Browsers re-enable static rulesets from manifest.json after an update, so the
// stored choice is reapplied on install, on browser start and on every change.
// Safari loads settings.js first through manifest background.scripts; the
// Chrome build runs this file as a service worker and imports it.
if (typeof importScripts === 'function' && !globalThis.TibiaAntiAdSettings) {
    importScripts('sites.js', 'settings.js', 'tibia-evidence.js', 'tibia-classify.js', 'tibia-rules.js');
}

(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const S = globalThis.TibiaAntiAdSettings;
    const R = globalThis.TibiaAntiAdRules;
    const safari = api.runtime.getURL('').startsWith('safari-web-extension:');

    const syncToolbar = async settings => {
        // The Safari app shows its own native toolbar button instead.
        if (!api.action) { return; }
        const state = settings.enabled ? 'active' : 'inactive';
        const tasks = [api.action.setTitle({
            title: `Tibia Anti-Ad \u2014 Blocking ${settings.enabled ? 'enabled' : 'disabled'}`,
        })];
        // Safari uses SF Symbols; Chrome has independent vector-based artwork.
        const sizes = safari ? [16, 19, 32, 38] : [16, 32, 48, 128];
        const platform = safari ? 'safari' : 'chrome';
        tasks.push(api.action.setIcon({ path: Object.fromEntries(
            sizes.map(size => [size, `icons/${platform}-toolbar/${state}-${size}.png`])
        ) }));
        await Promise.all(tasks);
    };

    // Serialize reads and writes so rapid toggles cannot leave an older icon.
    let pendingSync = Promise.resolve();
    const sync = () => {
        pendingSync = pendingSync.then(async () => {
            const settings = await S.load(api);
            const results = await Promise.allSettled([
                Promise.resolve().then(() => api.declarativeNetRequest.updateEnabledRulesets(S.rulesetState(settings))),
                Promise.resolve().then(() => syncToolbar(settings)),
            ]);
            results.forEach(result => {
                if (result.status === 'rejected') {
                    console.warn('[Tibia Anti-Ad] could not sync blocking state:', result.reason);
                }
            });
        }).catch(error => console.warn('[Tibia Anti-Ad] could not load settings:', error));
        return pendingSync;
    };

    const updateRules = () => R.update(api);

    // Safari: settings edited in the native toolbar popover live in the app's
    // App Group. Exchange them with this extension's storage by native
    // messaging (SafariWebExtensionHandler): send what the scripts use, take
    // edits newer than the last ones applied.
    const native = safari && Boolean(globalThis.browser?.runtime?.sendNativeMessage);
    let pendingNative = Promise.resolve();
    const syncNative = () => {
        if (!native) { return Promise.resolve(); }
        pendingNative = pendingNative.then(async () => {
            const stored = await api.storage.local.get(null);
            const reply = await globalThis.browser.runtime.sendNativeMessage('application.id', {
                type: 'sync', settings: S.resolve(stored), tibiaShown: stored.tibiaShown || {},
                rules: { fetchedAt: stored.tibiaEvidence?.fetchedAt || 0, error: stored.tibiaEvidenceError?.message || null },
            });
            const seen = { settings: 0, shown: 0, rules: 0, ...stored.nativeSeen };
            const changes = {};
            // Native controls remain authoritative after an acknowledged edit:
            // restored web storage can diverge without a new native timestamp.
            const nativeMismatch = reply?.settingsChangedAt > 0 && Object.entries(reply.settings || {})
                .some(([key, value]) => key in S.DEFAULTS && stored[key] !== value);
            if (reply?.settingsChangedAt > seen.settings || nativeMismatch) {
                Object.assign(changes, S.resolve({ ...S.resolve(stored), ...reply.settings }));
                seen.settings = reply.settingsChangedAt;
            }
            if (reply?.tibiaShownChangedAt > seen.shown) {
                changes.tibiaShown = reply.tibiaShown || {};
                seen.shown = reply.tibiaShownChangedAt;
            }
            if (reply?.rulesRequestedAt > seen.rules) {
                seen.rules = reply.rulesRequestedAt;
                updateRules();
            }
            if (Object.keys(changes).length || JSON.stringify(seen) !== JSON.stringify(stored.nativeSeen)) {
                await api.storage.local.set({ ...changes, nativeSeen: seen });
            }
        }).catch(error => console.warn('[Tibia Anti-Ad] could not sync with the app:', error));
        return pendingNative;
    };
    const reportHidden = message => native
        ? globalThis.browser.runtime.sendNativeMessage('application.id', { ...message, type: 'hidden' }).catch(() => {})
        : Promise.resolve();
    if (native) {
        api.alarms.create('tibia-native', { periodInMinutes: 1 });
        api.alarms.onAlarm.addListener(alarm => { if (alarm.name === 'tibia-native') { syncNative(); } });
    }
    api.alarms.create('tibia-rules', { periodInMinutes: R.PERIOD_MINUTES });
    api.alarms.onAlarm.addListener(alarm => { if (alarm.name === 'tibia-rules') { updateRules(); } });
    api.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message?.type === 'tibia-anti-ad:native-sync') { syncNative().then(() => sendResponse(true)); return true; }
        if (message?.type === 'tibia-anti-ad:hidden-report') { reportHidden(message); return false; }
        if (message?.type !== 'tibia-anti-ad:update-rules') { return false; }
        updateRules().then(sendResponse);
        return true;
    });

    api.runtime.onInstalled.addListener(() => { sync(); updateRules(); syncNative(); });
    api.runtime.onStartup.addListener(() => { sync(); updateRules(); syncNative(); });
    api.storage.onChanged.addListener((changes, area) => {
        if (area === 'local' && Object.keys(changes).some(key => key === 'enabled' || key in S.RULESETS)) { sync(); }
        if (area === 'local' && (changes.tibiaEvidence || changes.tibiaEvidenceError)) { syncNative(); }
    });
    // A nonpersistent background can load without onStartup/onInstalled firing.
    sync();
    syncNative();
})();
