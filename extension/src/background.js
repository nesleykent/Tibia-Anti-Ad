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

    const syncToolbar = async settings => {
        const state = settings.enabled ? 'active' : 'inactive';
        const tasks = [api.action.setTitle({
            title: `Tibia Anti-Ad \u2014 Blocking ${settings.enabled ? 'enabled' : 'disabled'}`,
        })];
        // Safari uses SF Symbols; Chrome has independent vector-based artwork.
        const safari = api.runtime.getURL('').startsWith('safari-web-extension:');
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
    api.alarms.create('tibia-rules', { periodInMinutes: R.PERIOD_MINUTES });
    api.alarms.onAlarm.addListener(alarm => { if (alarm.name === 'tibia-rules') { updateRules(); } });
    api.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message?.type !== 'tibia-anti-ad:update-rules') { return false; }
        updateRules().then(sendResponse);
        return true;
    });

    api.runtime.onInstalled.addListener(() => { sync(); updateRules(); });
    api.runtime.onStartup.addListener(() => { sync(); updateRules(); });
    api.storage.onChanged.addListener((changes, area) => {
        if (area === 'local' && Object.keys(changes).some(key => key === 'enabled' || key in S.RULESETS)) { sync(); }
    });
    // A nonpersistent background can load without onStartup/onInstalled firing.
    sync();
})();
