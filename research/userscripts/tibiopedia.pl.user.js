// ==UserScript==
// @name         tibiopedia.pl – neutralize Ad-Shield inline loader
// @namespace    adblock.local
// @version      1.0
// @description  Stops the inline Ad-Shield loader from wiping <body> when html-load.com is blocked by uBOL. Blocking itself is done by tibiopedia.pl.txt.
// @match        https://tibiopedia.pl/*
// @run-at       document-start
// @inject-into  page
// @grant        none
// ==/UserScript==

// Why not uBOL: both loaders are inline (no URL to block) and, once html-load.com and its
// mirrors fail, they run setInterval(() => document.body.remove(), 100). A hide rule cannot
// undo a removed body, and uBOL custom filters have no scriptlets.
(() => {
  'use strict';

  // Stable markers: the external loader tag and the inline loader both carry `nowprocket`
  // + data-cfasync="false"; the external one points at html-load.com / data-sdk="l/…".
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

  const mo = new MutationObserver(muts => {
    for (const m of muts)
      for (const n of m.addedNodes)
        if (n.nodeName === 'SCRIPT' && isAdShield(n)) kill(n);
  });
  mo.observe(document.documentElement, { childList: true, subtree: true });
  addEventListener('DOMContentLoaded', () => mo.disconnect(), { once: true });

  // Backup: the onerror loader returns early when window["as_<n><hash>"] for the current,
  // previous or next 10-minute bucket is an object with .s === itself ("loader-check-2-10min").
  const h = str => { let e = 0; for (let i = 0; i < str.length; i++) e = ((e << 5) - e + str.charCodeAt(i)) | 0; return e; };
  const host = location.hostname, r = 6e5, now = Date.now(), o = now - now % r;
  for (const t of [o - r, o, o + r, o + 2 * r]) {
    const k = 'as_' + (t / r % 10) + h(host + 'loader-check-2-10min_' + t);
    const v = {}; v.s = v; window[k] = v;
  }
  // Backup 2: if the observer removes the external tag but the inline loader still runs, it
  // throws "Cannot find html-load.com script" (→ body wipe) unless as_loader_version is set.
  window.as_loader_version = '0';
})();
