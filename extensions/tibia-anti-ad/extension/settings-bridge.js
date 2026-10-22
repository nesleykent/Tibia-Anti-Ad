// Tibia Anti-Ad: applies the settings to each Twitch page.
//
// - Names the hide.css groups that are switched off (data-tibia-anti-ad-off) or
//   opted into (data-tibia-anti-ad-on) on the root element, live as settings change.
// - Mirrors the resolved settings into the page's localStorage for page.js,
//   which has to decide synchronously before Twitch's player starts.
// The last mirrored copy is applied first, synchronously, so a group you turned
// off does not flash back while storage.local answers.
(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const S = globalThis.TibiaAntiAdSettings;

    const setList = (el, name, values) => {
        if (values.length) { el.setAttribute(name, values.join(' ')); }
        else { el.removeAttribute(name); }
    };

    const applyCss = settings => {
        const root = document.documentElement;
        if (!root) { return; }
        const { off, on } = S.cssState(settings);
        setList(root, 'data-tibia-anti-ad-off', off);
        setList(root, 'data-tibia-anti-ad-on', on);
    };

    const mirror = settings => {
        try { localStorage.setItem(S.PAGE_KEY, JSON.stringify(settings)); }
        catch { /* storage blocked: page.js falls back to the defaults */ }
    };

    let cached = null;
    try { cached = JSON.parse(localStorage.getItem(S.PAGE_KEY) || 'null'); }
    catch { cached = null; }
    if (cached) { applyCss(S.resolve(cached)); }

    const refresh = () => S.load(api).then(settings => {
        applyCss(settings);
        mirror(settings);
    });

    api.storage.onChanged.addListener((changes, area) => {
        if (area === 'local' && Object.keys(changes).some(key => key in S.DEFAULTS)) { refresh(); }
    });
    refresh();
})();
