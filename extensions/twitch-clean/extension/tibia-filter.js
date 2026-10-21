// Twitch Clean: hides streams in the Tibia category that are really another game
// (OTServers such as RubinOT, Pokémon servers, idle games).
//
// Each card is classified from independent evidence (see tibia-classify.js):

// OTServer clients the text missed, or restores a stream whose "!server" was
// only a sponsor command. Only an "other" verdict hides a card.
// Cards on screen are checked first. Runs only on the Tibia category directory.
(() => {
  'use strict';

  const api = globalThis.browser || globalThis.chrome;
  const MARK = 'data-twitch-clean-hidden';
  const VERDICT = 'data-twitch-clean-tibia';
  const classify = globalThis.TwitchCleanTibiaClassify.create(globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE);
  const hiddenByUs = new WeakSet();
  const onTibiaDirectory = () => /^\/directory\/category\/tibia(\/|$)/i.test(location.pathname);
  const cardInfo = article => {
    const href = article.querySelector('a[data-a-target="preview-card-channel-link"], a[data-a-target="preview-card-image-link"]')?.getAttribute('href') || '';
    const channel = href.match(/^\/([a-z0-9_]{1,25})\/?$/i)?.[1]?.toLowerCase();
    if (!channel) {
      return null;
    }
    const title = article.querySelector('h4[title], h3[title]')?.getAttribute('title') || article.querySelector('[data-a-target="preview-card-title-link"]')?.textContent || '';
    const tags = [...article.querySelectorAll('[data-a-target="tw-tag"], button.tw-tag, [class*="tag" i] button')].map(t => t.textContent.trim()).filter(Boolean);
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
  const apply = article => {
    const info = cardInfo(article);
    const cell = cellOf(article);
    let verdict = null;
    if (info && onTibiaDirectory()) {
      const result = classify(info.title, info.tags);
      verdict = result.verdict;
      cell.setAttribute(VERDICT, `${verdict}: ${result.reason}`);
    } else {
      cell.removeAttribute(VERDICT);
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
      if (!seen.has(article)) {
        seen.add(article);
      }
      apply(article);
    }
  };

  // Twitch reuses cards on scroll and client-side navigation: rescan once per
  // batch of mutations.
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
      characterData: true,
      attributes: true,
      attributeFilter: ['href', 'title']
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
