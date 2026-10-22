// Tibia Anti-Ad: hides streams in the Tibia category that are really another game
// (OTServers such as RubinOT, Pokémon servers, idle games).
//
// Each card is classified from its full title and tags (copied from Twitch's own
// data by tibia-props.js) with the rules in tibia-classify.js: a server declared
// in the title or tags hides the card, unless an official world or "Tibia
// Global" is also present; a "!server" chat command counts like the name. Only "other"
// hides a card. Runs only on the Tibia category directory, and only while the
// "Hide other games" setting (tibiaFilter) and the master switch are on.
//
// Corrections: "Show" in the settings page stores {channel: title} in
// tibiaShown. That broadcast stays visible until its title changes, so the
// override never becomes a permanent channel rule. The settings page asks this
// script for the cards it hides on the current page.
(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const S = globalThis.TibiaAntiAdSettings;
    const MARK = 'data-twitch-clean-hidden';
    const VERDICT = 'data-twitch-clean-tibia';
    const META = 'data-twitch-clean-meta';
    const classify = globalThis.TwitchCleanTibiaClassify.create(globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE);
    let enabled = true;
    let shown = {};
    const hiddenByUs = new WeakSet();
    // Verdicts by channel, title and tags: Twitch re-renders the same cards often.
    const verdicts = new Map();
    const classifyCard = info => {
        const key = `${info.channel}\n${info.title}\n${info.tags.join('\n')}`;
        let result = verdicts.get(key);
        if (!result) {
            if (verdicts.size >= 1000) { verdicts.clear(); }
            result = classify(info.title, info.tags, null, info.channel);
            verdicts.set(key, result);
        }
        return result;
    };

    const onTibiaDirectory = () => /^\/directory\/category\/tibia(\/|$)/i.test(location.pathname);

    const cardInfo = article => {
        try {
            const meta = JSON.parse(article.getAttribute(META) || 'null');
            if (meta && typeof meta.channel === 'string') { return meta; }
        } catch { /* fall back to the visible card */ }
        const href = article.querySelector('a[data-a-target="preview-card-channel-link"], a[data-a-target="preview-card-image-link"]')?.getAttribute('href') || '';
        const channel = href.match(/^\/([a-z0-9_]{1,25})\/?$/i)?.[1]?.toLowerCase();
        if (!channel) { return null; }
        const title = article.querySelector('h4[title], h3[title]')?.getAttribute('title') || '';
        const tags = [...article.querySelectorAll('[data-a-target="tw-tag"], .tw-tag')].map(t => t.textContent.trim()).filter(Boolean);
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
        if (info) {
            const result = classifyCard(info);
            verdict = result.verdict;
            const overridden = verdict === 'other' && shown[info.channel] === info.title;
            cell.setAttribute(VERDICT, `${verdict}: ${result.reason}${overridden ? ' (shown by you)' : ''}`);
            if (overridden) { verdict = 'shown'; }
        }
        if (verdict === 'other') {
            if (!hiddenByUs.has(cell)) { requestMore(); }
            cell.setAttribute(MARK, '');
            hiddenByUs.add(cell);
        }
        else if (hiddenByUs.has(cell)) { cell.removeAttribute(MARK); hiddenByUs.delete(cell); }
    };

    const scan = () => {
        if (!enabled || !onTibiaDirectory()) {
            for (const el of document.querySelectorAll(`[${VERDICT}]`)) {
                el.removeAttribute(VERDICT);
                if (hiddenByUs.has(el)) { el.removeAttribute(MARK); hiddenByUs.delete(el); }
            }
            return;
        }
        for (const article of document.querySelectorAll('article')) { apply(article); }
    };

    // Twitch loads more cards from a scroll handler on its root scroller that
    // checks whether the list end is near. Hiding cards shortens the list without
    // a scroll, so after hiding, dispatch a synthetic scroll event (as Unwanted
    // Twitch does): Twitch loads more only if the end is now near, and the
    // reader's position never changes.
    // The handler may not be attached yet, or a load may be in flight, so retry
    // while the visible list stays shorter than two screens and no new cards came.
    const RETRIES = 8;
    let nudgeTimer = 0;
    let retries = 0;
    let lastCount = 0;
    const requestMore = () => {
        if (nudgeTimer) { return; }
        nudgeTimer = setTimeout(() => {
            nudgeTimer = 0;
            const scroller = document.querySelector('[data-a-target="root-scroller"]');
            if (!scroller || !onTibiaDirectory()) { return; }
            scroller.dispatchEvent(new Event('scroll'));
            const count = document.querySelectorAll('article').length;
            if (count !== lastCount) { lastCount = count; retries = 0; }
            const short = scroller.scrollHeight - scroller.scrollTop < scroller.clientHeight * 2;
            if (short && retries++ < RETRIES) { requestMore(); }
        }, 700);
    };

    // Twitch reuses cards on scroll and client-side navigation: rescan once per
    // batch of mutations, including tibia-props.js updating a card's metadata.
    let queued = false;
    const observer = new MutationObserver(() => {
        if (queued) { return; }
        queued = true;
        queueMicrotask(() => { queued = false; scan(); });
    });
    // Observe the page only on the Tibia directory. Twitch navigates without
    // reloading, so follow the URL (Navigation API where available, else a
    // one-second check) and clear the marks when leaving the directory.
    let observing = false;
    const follow = () => {
        const wanted = onTibiaDirectory();
        if (wanted === observing) { return; }
        observing = wanted;
        if (wanted) { observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['href', 'title', META] }); }
        else { observer.disconnect(); }
        scan();
    };
    const start = () => {
        scan();
        follow();
        globalThis.navigation?.addEventListener?.('currententrychange', follow);
        setInterval(follow, 1000);
    };
    // Cards this script hides on the current page, for the settings page.
    const hiddenCards = () => [...document.querySelectorAll('article')].flatMap(article => {
        const cell = cellOf(article);
        if (!hiddenByUs.has(cell)) { return []; }
        const info = cardInfo(article);
        const reason = (cell.getAttribute(VERDICT) || '').replace(/^other: /, '');
        return info ? [{ channel: info.channel, title: info.title, reason }] : [];
    });
    api.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message?.type !== 'tibia-anti-ad:tibia-hidden') { return false; }
        sendResponse({ onDirectory: onTibiaDirectory(), enabled, hidden: enabled && onTibiaDirectory() ? hiddenCards() : [] });
        return false;
    });

    const load = () => Promise.all([S.load(api), api.storage.local.get({ tibiaShown: {} })])
        .then(([settings, { tibiaShown }]) => {
            enabled = S.active(settings, 'tibiaFilter');
            shown = tibiaShown && typeof tibiaShown === 'object' ? tibiaShown : {};
            scan();
        });
    api.storage.onChanged.addListener((changes, area) => {
        if (area === 'local' && (changes.tibiaFilter || changes.enabled || changes.tibiaShown)) { load(); }
    });
    load();
    if (document.body) { start(); }
    else { document.addEventListener('DOMContentLoaded', start, { once: true }); }
})();
