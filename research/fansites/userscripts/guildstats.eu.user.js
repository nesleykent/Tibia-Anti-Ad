// ==UserScript==
// @name         guildstats.eu – remove inline-!important AdSense overlays
// @namespace    adblock.local
// @version      1.1
// @description  OPTIONAL. Only needed if uBOL on Safari does not apply the list's network rules: removes AdSense units whose inline `display:… !important` defeats cosmetic hiding.
// @match        https://guildstats.eu/*
// @run-at       document-start
// @inject-into  page
// @grant        none
// ==/UserScript==

// Why not uBOL: AdSense writes display/visibility/position as inline !important on the
// ad-intents bar (#google-anno-sa) and the vignette/anchor <ins> under <html>. Page-level
// CSS cannot beat inline !important, and uBOL custom filters have no :remove()/scriptlets.
(() => {
  'use strict';
  // Also the ad-intents chips AdSense injects INTO site text (div.google-anno-sc role=link,
  // e.g. "Play Tabletop RPGs" inside the header title) – same inline !important styling.
  const SEL = 'html > div[id^="google-anno"], html > ins.adsbygoogle, .google-anno-sc';
  const sweep = () => {
    document.querySelectorAll(SEL).forEach(e => e.remove());
    // Anchor ad reserves space with inline body padding; drop it when no anchor remains.
    const b = document.body;
    if (b && b.style.padding && !document.querySelector('html > ins.adsbygoogle')) b.style.removeProperty('padding');
  };
  let queued = false;
  const schedule = () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; sweep(); }); } };
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  addEventListener('DOMContentLoaded', () => {
    sweep();
    new MutationObserver(schedule).observe(document.body, { attributes: true, attributeFilter: ['style'] });
  }, { once: true });
  // #google_vignette hash hijack: strip it so Back/reload don't re-trigger the vignette.
  if (location.hash === '#google_vignette') history.replaceState(null, '', location.pathname + location.search);
})();
