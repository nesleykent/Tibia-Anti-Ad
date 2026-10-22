// Tibia Anti-Ad: tibiopedia.pl anti-adblock protection (page world, document_start).
// Ported from research/fansites/userscripts/tibiopedia.pl.user.js. Once the extension blocks
// html-load.com and its mirrors, the site's inline Ad-Shield loaders run
// setInterval(() => document.body.remove(), 100). The report in
// research/fansites/reports/tibiopedia.pl-validation.md shows the as_* self-reference flags
// and as_loader_version keep the body intact; the observer is a backup.
// Reads the settings mirrored by settings-bridge.js ("tibia-anti-ad:settings").
(() => {
    'use strict';

    let settings = {};
    try { settings = JSON.parse(localStorage.getItem('tibia-anti-ad:settings')) || {}; } catch {}
    if (settings.enabled === false || settings['site:tibiopedia.pl'] === false) { return; }

    // The external loader tag and the inline loader carry `nowprocket` and
    // data-cfasync="false"; the external one points at html-load.com / data-sdk="l/...".
    const isAdShield = s =>
        s.hasAttribute('nowprocket') ||
        /html-load\.com|content-loader\.com/.test(s.src || '') ||
        /^l\//.test(s.getAttribute('data-sdk') || '');

    const kill = s => {
        s.type = 'javascript/blocked';
        s.removeAttribute('onload');
        s.removeAttribute('onerror');
        s.removeAttribute('src');
        s.textContent = '';
        s.remove();
    };

    const observer = new MutationObserver(records => {
        for (const record of records) {
            for (const node of record.addedNodes) {
                if (node.nodeName === 'SCRIPT' && isAdShield(node)) { kill(node); }
            }
        }
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
    addEventListener('DOMContentLoaded', () => observer.disconnect(), { once: true });

    // The onerror loader returns early when window["as_<n><hash>"] for the current,
    // previous or next 10-minute bucket is an object whose .s is itself.
    const hash = text => { let h = 0; for (let i = 0; i < text.length; i++) { h = ((h << 5) - h + text.charCodeAt(i)) | 0; } return h; };
    const bucket = 6e5, now = Date.now(), start = now - now % bucket;
    for (const t of [start - bucket, start, start + bucket, start + 2 * bucket]) {
        const flag = {};
        flag.s = flag;
        window['as_' + (t / bucket % 10) + hash(location.hostname + 'loader-check-2-10min_' + t)] = flag;
    }
    // Without the external tag the inline loader throws "Cannot find html-load.com
    // script" (and wipes the body) unless as_loader_version is set.
    window.as_loader_version = '0';
})();
