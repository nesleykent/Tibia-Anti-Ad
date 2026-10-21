// Twitch Clean: hides streams in the Tibia category that are really another game
// (OTServers such as RubinOT, Pokémon servers, idle games).
//
// Each card is classified from its full title and tags (copied from Twitch's own
// data by tibia-props.js) with the rules in tibia-classify.js: a server declared
// in the title or tags hides the card, unless an official world or "Tibia
// Global" is also present; a mere "!server" command does not. Only cards the

// where an OTServer-only client ("Map View", Battle Pass) also hides them.
// Only "other" hides a card. Runs only on the Tibia category directory.
(() => {
  'use strict';

  const api = globalThis.browser || globalThis.chrome;
  const MARK = 'data-twitch-clean-hidden';
  const VERDICT = 'data-twitch-clean-tibia';
  const META = 'data-twitch-clean-meta';
  const classify = globalThis.TwitchCleanTibiaClassify.create(globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE);
  const hiddenByUs = new WeakSet();
  const onTibiaDirectory = () => /^\/directory\/category\/tibia(\/|$)/i.test(location.pathname);
  const cardInfo = article => {
    try {
      const meta = JSON.parse(article.getAttribute(META) || 'null');
      if (meta && typeof meta.channel === 'string') {
        return meta;
      }
    } catch {/* fall back to the visible card */}
    const href = article.querySelector('a[data-a-target="preview-card-channel-link"], a[data-a-target="preview-card-image-link"]')?.getAttribute('href') || '';
    const channel = href.match(/^\/([a-z0-9_]{1,25})\/?$/i)?.[1]?.toLowerCase();
    if (!channel) {
      return null;
    }
    const title = article.querySelector('h4[title], h3[title]')?.getAttribute('title') || '';
    const tags = [...article.querySelectorAll('[data-a-target="tw-tag"], .tw-tag')].map(t => t.textContent.trim()).filter(Boolean);
    return {
      channel,
      title,
      tags
    };
  };

  // The grid cell around a card: the highest ancestor holding only this card.
  const cellOf = article => {
    let node = article;
    while (node.parentElement && node.parentElement.querySelectorAll('article').length === 1) {
      node = node.parentElement;
    }
    return node;
  };
  const requestScreen = channel => {
    if (screens.has(channel) || pending.has(channel)) {
      return;
    }
    pending.add(channel);
    api.runtime.sendMessage({
      type: "",
      channel
    }).then(response => screens.set(channel, typeof response?.text === 'string' ? response.text : null)).catch(() => screens.set(channel, null)).finally(() => {
      pending.delete(channel);
      scan();
    });
  };
  const apply = article => {
    const info = cardInfo(article);
    const cell = cellOf(article);
    let verdict = null;
    if (info) {
      const result = classify(info.title, info.tags);
      verdict = result.verdict;
      cell.setAttribute(VERDICT, `${verdict}: ${result.reason}`);
      if (verdict === 'undetermined' && !screens.has(info.channel)) {
        requestScreen(info.channel);
      }
    }
    if (verdict === 'other') {
      cell.setAttribute(MARK, '');
      hiddenByUs.add(cell);
    } else if (hiddenByUs.has(cell)) {
      cell.removeAttribute(MARK);
      hiddenByUs.delete(cell);
    }
  };
  const scan = () => {
    if (!onTibiaDirectory()) {
      for (const el of document.querySelectorAll(`[${VERDICT}]`)) {
        el.removeAttribute(VERDICT);
        if (hiddenByUs.has(el)) {
          el.removeAttribute(MARK);
          hiddenByUs.delete(el);
        }
      }
      return;
    }
    for (const article of document.querySelectorAll('article')) {
      apply(article);
    }
  };

  // Twitch reuses cards on scroll and client-side navigation: rescan once per
  // batch of mutations, including tibia-props.js updating a card's metadata.
  let queued = false;
  const observer = new MutationObserver(() => {
    if (queued) {
      return;
    }
    queued = true;
    queueMicrotask(() => {
      queued = false;
      scan();
    });
  });
  const start = () => {
    scan();
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['href', 'title', META]
    });
  };
  if (document.body) {
    start();
  } else {
    document.addEventListener('DOMContentLoaded', start, {
      once: true
    });
  }
})();
