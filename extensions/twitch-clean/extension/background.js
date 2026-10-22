// Twitch Clean background: keeps the network rulesets in step with the settings.
// Browsers re-enable static rulesets from manifest.json after an update, so the
// stored choice is reapplied on install, on browser start and on every change.
// Safari loads settings.js first through manifest background.scripts; the
// Chrome build runs this file as a service worker and imports it.
if (typeof importScripts === 'function' && !globalThis.TwitchCleanSettings) {
    importScripts('settings.js');
}

(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const S = globalThis.TwitchCleanSettings;

    const sync = () => S.load(api)
        .then(settings => api.declarativeNetRequest.updateEnabledRulesets(S.rulesetState(settings)))
        .catch(error => console.warn('[Twitch Clean] could not update rulesets:', error));

    api.runtime.onInstalled.addListener(sync);
    api.runtime.onStartup.addListener(sync);
    api.storage.onChanged.addListener((changes, area) => {
        if (area === 'local' && Object.keys(changes).some(key => key === 'enabled' || key in S.RULESETS)) { sync(); }
    });
})();
