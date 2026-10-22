// Tibia Anti-Ad: keeps the Tibia filter's evidence (server names, worlds, weights,
// sites) current without a reinstall. The background script downloads
// filters/sources/twitch/tibia-evidence.json from the repository's main branch
// at browser start and every six hours; a copy is kept only when the bundled
// classifier can run it and it still tells a server from an official world.
// Only this data is downloaded, never code; the bundled copy
// (tibia-evidence.js) is used until a valid update arrives.
(() => {
    'use strict';

    const URL = 'https://raw.githubusercontent.com/nesleykent/Tibia-Anti-Ad/main/filters/sources/twitch/tibia-evidence.json';
    const KEY = 'tibiaEvidence';
    const ERROR_KEY = 'tibiaEvidenceError';
    const PERIOD_MINUTES = 360;

    const valid = data => {
        try {
            const classify = globalThis.TwitchCleanTibiaClassify.create(data);
            return classify('RubinOT war', []).verdict === 'other' && classify('Antica hunt', []).verdict === 'tibia';
        } catch {
            return false;
        }
    };

    // The evidence to use: a valid downloaded copy, else the bundled one.
    const current = stored => stored && valid(stored.data) ? stored.data : globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE;

    const update = api => fetch(URL, { cache: 'no-cache' })
        .then(response => {
            if (!response.ok) { throw new Error(`GitHub answered ${response.status}`); }
            return response.json();
        })
        .then(data => {
            if (!valid(data)) { throw new Error('the downloaded rules are not valid'); }
            const fetchedAt = Date.now();
            return api.storage.local.set({ [KEY]: { data, fetchedAt } })
                .then(() => api.storage.local.remove(ERROR_KEY))
                .then(() => ({ ok: true, fetchedAt }));
        })
        .catch(error => {
            const message = String(error?.message || error);
            return api.storage.local.set({ [ERROR_KEY]: { message, at: Date.now() } }).then(() => ({ ok: false, error: message }));
        });

    globalThis.TibiaAntiAdRules = Object.freeze({ URL, KEY, ERROR_KEY, PERIOD_MINUTES, valid, current, update });
})();
