// ==UserScript==
// @name         TibiaRing – undo AdSense anchor padding
// @namespace    tibiaring-ubol
// @version      1
// @description  Removes the blank band AdSense's (hidden) anchor ad reserves on <body>. Only needed because Safari uBOL does not enforce the custom network rules, and a uBOL hide rule cannot undo inline padding.
// @match        https://www.tibiaring.com/*
// @match        https://tibiaring.com/*
// @run-at       document-start
// @inject-into  page
// @grant        none
// ==/UserScript==

// AdSense Auto ads writes e.g. style="padding: 0px 0px 120px" (bottom anchor) or
// "padding: 154px 0px 0px" (top anchor) on <body>. The site's own CSS sets no body
// padding (verified), so forcing 0 changes nothing else. An !important stylesheet beats
// AdSense's non-important inline value without needing to watch for mutations.
(() => {
  const s = document.createElement('style');
  s.textContent = 'html,body{padding-top:0!important;padding-bottom:0!important}';
  (document.head || document.documentElement).appendChild(s);
})();
