// Tibia Anti-Ad: AdSense leftovers on guildstats.eu and tibiamonk.com (content script).
// Ported from research/userscripts/guildstats.eu.user.js and tibiamonk.com.user.js.
// The rulesets block AdSense; this cleans up if a unit still appears: it removes the
// ad-intents bar, the vignette/anchor units and the ad-intent chips AdSense writes
// with inline !important styles, drops the body padding the anchor reserves, and
// strips the #google_vignette hash so Back and reload do not re-open the vignette.
(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const S = globalThis.TibiaAntiAdSettings;
    const site = S.SITES.find(s => location.hostname === s.domain || location.hostname.endsWith('.' + s.domain));
    const SELECTOR = 'html > div[id^="google-anno"], html > ins.adsbygoogle, .google-anno-sc';

    const sweep = () => {
        document.querySelectorAll(SELECTOR).forEach(el => el.remove());
        const body = document.body;
        if (body && body.style.padding && !document.querySelector('html > ins.adsbygoogle')) { body.style.removeProperty('padding'); }
    };
    let queued = false;
    const schedule = () => {
        if (queued) { return; }
        queued = true;
        requestAnimationFrame(() => { queued = false; sweep(); });
    };

    S.load(api).then(settings => {
        if (!site || !S.active(settings, site.key)) { return; }
        if (location.hash === '#google_vignette') { history.replaceState(null, '', location.pathname + location.search); }
        new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
        const watchBody = () => {
            sweep();
            new MutationObserver(schedule).observe(document.body, { attributes: true, attributeFilter: ['style'] });
        };
        if (document.body) { watchBody(); }
        else { addEventListener('DOMContentLoaded', watchBody, { once: true }); }
    });
})();
