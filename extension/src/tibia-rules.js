// Tibia Anti-Ad: keeps the Tibia filter's learned statistical model current
// without a reinstall. The background script downloads
// filters/sources/twitch/tibia-evidence.json from the repository's main branch
// at browser start and every six hours; a copy is kept only when the bundled
// classifier accepts its model format and finite numeric parameters.
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
            // An older cached/downloaded ruleset must not undo an app update.
            const revision = data.revision ?? 0;
            if (!Number.isSafeInteger(revision) || revision < (globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE.revision || 0)) { return false; }
            if (!data.model?.weights || !Object.keys(data.model.weights).length) { return false; }
            const classify = globalThis.TwitchCleanTibiaClassify.create(data);
            const empty = classify('', []);
            return empty.private_probability === 0.01 && empty.display_probability === 0.99 && empty.hide === false;
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
