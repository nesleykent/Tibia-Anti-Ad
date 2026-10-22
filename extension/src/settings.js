// Tibia Anti-Ad settings: every option, its default and what it controls.
// Loaded by the settings page (popup.html), the background script and the
// isolated content scripts, so all of them share one definition.
(() => {
    'use strict';

    // The fansites (sites.js, generated from filters/sources/sites). Each one has a switch,
    // on by default, that controls its ruleset and its cosmetic rules. Loaded
    // before this file; without it only the Twitch options exist.
    const SITES = globalThis.TibiaAntiAdSites || [];
    const fromSites = field => Object.fromEntries(SITES.map(site => [site.key, field(site)]));

    // Every option is a boolean in storage.local under the same key.
    const DEFAULTS = Object.freeze({
        enabled: true,
        blockAds: true,
        blockTracking: true,
        removeStreamAds: true,
        sourceQuality: true,
        backgroundQuality: true,
        hideAdBreakBanner: false,
        hideDisplayAds: true,
        hideUpsells: true,
        hidePrompts: true,
        hideSignupPrompts: true,
        hideCookieBanner: true,
        tibiaFilter: true,
        ...fromSites(() => true),
    });

    // Declarative net request rulesets (manifest.json rule_resources ids).
    const RULESETS = Object.freeze({
        blockAds: 'twitch_ads',
        blockTracking: 'twitch_tracking',
        ...fromSites(site => site.ruleset),
    });

    // hide.css groups. Opt-out groups are hidden unless named in the root's
    // data-tibia-anti-ad-off attribute; opt-in groups are hidden only when named
    // in data-tibia-anti-ad-on.
    const CSS_OPT_OUT = Object.freeze({
        hideDisplayAds: 'ads',
        hideUpsells: 'upsells',
        hidePrompts: 'prompts',
        hideSignupPrompts: 'signup',
        hideCookieBanner: 'cookies',
        tibiaFilter: 'tibia',
        ...fromSites(site => site.domain),
    });
    const CSS_OPT_IN = Object.freeze({
        hideAdBreakBanner: 'adbreak',
    });

    // page.js runs in the page before any extension API can answer, so the
    // settings bridge mirrors the resolved settings into the page's localStorage
    // under this key and page.js reads them synchronously.
    const PAGE_KEY = 'tibia-anti-ad:settings';

    // Options that page.js applies once, when the page loads.
    const RELOAD_KEYS = Object.freeze(['removeStreamAds', 'sourceQuality', 'backgroundQuality']);

    // Defaults plus whatever valid booleans are stored.
    const resolve = (stored = {}) => {
        const settings = { ...DEFAULTS };
        for (const key of Object.keys(DEFAULTS)) {
            if (typeof stored?.[key] === 'boolean') { settings[key] = stored[key]; }
        }
        return settings;
    };

    // Whether an option is in force: the master switch overrides everything.
    const active = (settings, key) => settings.enabled && settings[key];

    const cssState = settings => ({
        off: Object.entries(CSS_OPT_OUT).filter(([key]) => !active(settings, key)).map(([, group]) => group),
        on: Object.entries(CSS_OPT_IN).filter(([key]) => active(settings, key)).map(([, group]) => group),
    });

    const rulesetState = settings => {
        const ids = Object.entries(RULESETS);
        return {
            enableRulesetIds: ids.filter(([key]) => active(settings, key)).map(([, id]) => id),
            disableRulesetIds: ids.filter(([key]) => !active(settings, key)).map(([, id]) => id),
        };
    };

    const load = api => api.storage.local.get(DEFAULTS).then(resolve);

    globalThis.TibiaAntiAdSettings = Object.freeze({
        SITES, DEFAULTS, RULESETS, CSS_OPT_OUT, CSS_OPT_IN, PAGE_KEY, RELOAD_KEYS,
        resolve, active, cssState, rulesetState, load,
    });
})();
