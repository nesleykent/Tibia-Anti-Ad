// Tibia Anti-Ad: tibiawiki.com.br anti-adblock protection and native scrolling
// (page world, document_start). Ported from research/userscripts/tibiawiki-scrollbar.user.js;
// its network blocking is left out because the extension's ruleset already does it.
// - BlockAdblock: an inline obfuscated script that wipes the page when ads are
//   blocked. It skips the wall while the ghArpOhsKq session flag is positive, and
//   the observer removes the script when it is inserted after this runs.
//   Never hide #banner_ad / #ad-label: they are its bait elements.
// - Removes the site's ::-webkit-scrollbar rules so Safari uses its native scrollbar.
// Reads the settings mirrored by settings-bridge.js ("tibia-anti-ad:settings").
(() => {
    'use strict';

    let settings = {};
    try { settings = JSON.parse(localStorage.getItem('tibia-anti-ad:settings')) || {}; } catch {}
    if (settings.enabled === false || settings['site:tibiawiki.com.br'] === false) { return; }

    try { sessionStorage.setItem('ghArpOhsKq', '1500'); } catch {}

    const isBlockAdblock = node =>
        node.tagName === 'SCRIPT' && !node.src &&
        /Digital Millennium Copyright Act|BlockAdblock|ghArpOhsKq/.test(node.textContent || '');
    new MutationObserver(records => {
        for (const record of records) {
            for (const node of record.addedNodes) {
                if (node.nodeType === 1 && isBlockAdblock(node)) {
                    node.type = 'javascript/blocked';
                    node.textContent = '';
                    node.remove();
                }
            }
        }
    }).observe(document.documentElement, { childList: true, subtree: true });

    const stripScrollbar = () => {
        for (const sheet of document.styleSheets) {
            let rules;
            try { rules = sheet.cssRules; } catch { continue; }
            for (let i = rules.length - 1; i >= 0; i--) {
                if (rules[i].selectorText?.includes('::-webkit-scrollbar')) { sheet.deleteRule(i); }
            }
        }
    };
    document.addEventListener('DOMContentLoaded', stripScrollbar);
    addEventListener('load', stripScrollbar);
    document.addEventListener('load', event => { if (event.target.tagName === 'LINK') { stripScrollbar(); } }, true);
})();
