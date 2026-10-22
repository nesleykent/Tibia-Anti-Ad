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

    const sync = () => S.load(api)
        .then(settings => api.declarativeNetRequest.updateEnabledRulesets(S.rulesetState(settings)))
        .catch(error => console.warn('[Tibia Anti-Ad] could not update rulesets:', error));

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
})();
