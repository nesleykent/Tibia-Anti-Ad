// Twitch Clean: hides streams in the Tibia category that are really another game
// (OTServers such as RubinOT, Pokémon servers, idle games).
//
// Each card is classified from independent evidence (see tibia-classify.js):
// the game client visible in its thumbnail, read by ocr-background.js, plus the
// title and tags. Title/tags act immediately; the thumbnail check then hides
// OTServer clients the text missed, or restores a stream whose "!server" was
// only a sponsor command. Only an "other" verdict hides a card.
// Cards on screen are checked first. Runs only on the Tibia category directory.
(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const MARK = 'data-twitch-clean-hidden';
    const VERDICT = 'data-twitch-clean-tibia';
    const classify = globalThis.TwitchCleanTibiaClassify.create(globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE);
    const results = new Map(); // channel -> ocr text | null (null = unreadable)
    const pending = new Set();
    const hiddenByUs = new WeakSet();

    const onTibiaDirectory = () => /^\/directory\/category\/tibia(\/|$)/i.test(location.pathname);

    const cardInfo = article => {
        const href = article.querySelector('a[data-a-target="preview-card-channel-link"], a[data-a-target="preview-card-image-link"]')?.getAttribute('href') || '';
        const channel = href.match(/^\/([a-z0-9_]{1,25})\/?$/i)?.[1]?.toLowerCase();
        if (!channel) { return null; }
        const title = article.querySelector('h4[title], h3[title]')?.getAttribute('title')
            || article.querySelector('[data-a-target="preview-card-title-link"]')?.textContent || '';
        const tags = [...article.querySelectorAll('[data-a-target="tw-tag"], button.tw-tag, [class*="tag" i] button')]
            .map(t => t.textContent.trim()).filter(Boolean);
        return { channel, title, tags };
    };

    // The grid cell around a card: the highest ancestor holding only this card.
    const cellOf = article => {
        let node = article;
        while (node.parentElement && node.parentElement.querySelectorAll('article').length === 1) { node = node.parentElement; }
        return node;
    };

    const apply = article => {
        const info = cardInfo(article);
        const cell = cellOf(article);
        let verdict = null;
        if (info && onTibiaDirectory()) {
            // Text decides at once; the thumbnail result refines it when it arrives.
            const result = classify(info.title, info.tags, results.has(info.channel) ? results.get(info.channel) : null);
            verdict = result.verdict;
            cell.setAttribute(VERDICT, `${verdict}: ${result.reason}`);
        } else {
            cell.removeAttribute(VERDICT);
        }
        if (verdict === 'other') { cell.setAttribute(MARK, ''); hiddenByUs.add(cell); }
        else if (hiddenByUs.has(cell)) { cell.removeAttribute(MARK); hiddenByUs.delete(cell); }
    };

    const applyChannel = channel => {
        for (const article of document.querySelectorAll('article')) {
            if (cardInfo(article)?.channel === channel) { apply(article); }
        }
    };

    const request = channel => {
        if (results.has(channel) || pending.has(channel)) { return; }
        pending.add(channel);
        api.runtime.sendMessage({ type: 'tibia-ocr', channel })
            .then(response => results.set(channel, typeof response?.text === 'string' ? response.text : null))
            .catch(() => results.set(channel, null))
            .finally(() => { pending.delete(channel); applyChannel(channel); });
    };

    const seen = new WeakSet();
    const intersection = new IntersectionObserver(entries => {
        for (const entry of entries) {
            const info = cardInfo(entry.target);
            if (!info || !onTibiaDirectory()) { continue; }
            if (entry.isIntersecting) { request(info.channel); }
        }
    }, { rootMargin: '600px 0px' });

    const scan = () => {
        if (!onTibiaDirectory()) {
            for (const el of document.querySelectorAll(`[${VERDICT}]`)) {
                el.removeAttribute(VERDICT);
                if (hiddenByUs.has(el)) { el.removeAttribute(MARK); hiddenByUs.delete(el); }
            }
            return;
        }
        for (const article of document.querySelectorAll('article')) {
            if (!seen.has(article)) { seen.add(article); intersection.observe(article); }
            apply(article);
        }
    };

    // Twitch reuses cards on scroll and client-side navigation: rescan once per
    // batch of mutations.
    let queued = false;
    const observer = new MutationObserver(() => {
        if (queued) { return; }
        queued = true;
        queueMicrotask(() => { queued = false; scan(); });
    });

    const start = () => {
        scan();
        observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['href', 'title'] });
    };
    if (document.body) { start(); }
    else { document.addEventListener('DOMContentLoaded', start, { once: true }); }
})();
