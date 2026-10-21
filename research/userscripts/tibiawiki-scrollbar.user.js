// ==UserScript==
// @name         TibiaWiki – native scrolling, anti-adblock & ad-script blocker
// @match        https://www.tibiawiki.com.br/*
// @match        https://tibiawiki.com.br/*
// @run-at       document-start
// @inject-into  page
// @grant        none
// ==/UserScript==
// 1. Removes the site's ::-webkit-scrollbar rules (MediaWiki:Common.css) so Safari uses its
//    native, accelerated overlay scrollbar again.
// 2. Neutralises the BlockAdblock anti-adblock wall (inline obfuscated script that wipes the page).
// 3. Stops ad/tracker scripts and iframes from being inserted. This is the network blocking
//    that uBO Lite custom filters can't do on Safari, and it frees the main thread while scrolling.
(() => {
  // --- BlockAdblock (inline "4.2b" snippet with DMCA notice + JSFuck/packer payload) ---
  const isBlockAdblock = (n) =>
    n.tagName === 'SCRIPT' && !n.src &&
    /Digital Millennium Copyright Act|BlockAdblock|ghArpOhsKq/.test(n.textContent || '');
  // Backup: the script skips the wall when this session flag is positive.
  try { sessionStorage.setItem('ghArpOhsKq', '1500'); } catch {}

  const BLOCK = /(^|\.)(premiumads\.com\.br|doubleclick\.net|googlesyndication\.com|amazon-adsystem\.com|viralize\.tv|banners\.tibiabr\.com|fundingchoicesmessages\.google\.com|googletagmanager\.com|google-analytics\.com|connect\.facebook\.net|navdmp\.com|navegg\.com|adtrafficquality\.google|seedtag\.com|rubiconproject\.com|onetag-sys\.com|smartadserver\.com|pubmatic\.com|criteo\.com|yandex\.ru)$/i;

  const isBlocked = (url) => {
    try { return BLOCK.test(new URL(url, location.href).hostname); } catch { return false; }
  };
  const isAdNode = (n) =>
    n && (n.tagName === 'SCRIPT' || n.tagName === 'IFRAME') && n.src && isBlocked(n.src);

  // Dynamically inserted scripts/iframes (Prebid, GPT, Viralize, pixels).
  for (const m of ['appendChild', 'insertBefore', 'replaceChild']) {
    const orig = Node.prototype[m];
    Node.prototype[m] = function (node, ...rest) {
      if (isAdNode(node)) return node;
      return orig.call(this, node, ...rest);
    };
  }
  for (const m of ['append', 'prepend', 'after', 'before']) {
    const orig = Element.prototype[m];
    Element.prototype[m] = function (...nodes) {
      return orig.apply(this, nodes.filter((n) => !isAdNode(n)));
    };
  }

  // Parser-inserted scripts (incl. the document.write'd Revive al.php pop-up).
  const origWrite = document.write;
  document.write = function (...args) {
    const html = args.join('');
    const m = html.match(/src=['"]([^'"]+)['"]/i);
    if (m && isBlocked(m[1])) return;
    return origWrite.apply(this, args);
  };
  new MutationObserver((muts) => {
    for (const mu of muts) for (const n of mu.addedNodes) {
      if (n.nodeType !== 1) continue;
      if (isBlockAdblock(n)) { n.type = 'javascript/blocked'; n.textContent = ''; n.remove(); }
      else if (isAdNode(n)) n.remove();
    }
  }).observe(document.documentElement, { childList: true, subtree: true });

  // Tracking beacons.
  const origBeacon = navigator.sendBeacon?.bind(navigator);
  if (origBeacon) navigator.sendBeacon = (url, data) => (isBlocked(url) ? true : origBeacon(url, data));

  // Native scrollbar.
  const stripScrollbar = () => {
    for (const sheet of document.styleSheets) {
      let rules;
      try { rules = sheet.cssRules; } catch { continue; }
      for (let i = rules.length - 1; i >= 0; i--) {
        if (rules[i].selectorText?.includes('::-webkit-scrollbar')) sheet.deleteRule(i);
      }
    }
  };
  document.addEventListener('DOMContentLoaded', stripScrollbar);
  window.addEventListener('load', stripScrollbar);
  document.addEventListener('load', (e) => { if (e.target.tagName === 'LINK') stripScrollbar(); }, true);
})();
