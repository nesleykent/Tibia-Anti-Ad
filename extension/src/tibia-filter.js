// Tibia Anti-Ad: hides streams in the Tibia category that are really another game
// (OTServers such as RubinOT, Pok\u00e9mon servers, idle games).
//
// Each card is classified from its full title and tags (copied from Twitch's own
// data by tibia-props.js) by the learned statistical model in tibia-classify.js.
// The displayed complement is compared with the user's threshold while the filter
// and master switch are on. The percentage view uses its complement.
// On Safari the same result also supplies a probability label with hiding off.
// Both features run only on the Tibia category directory; the master pauses both.
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
    const R = globalThis.TibiaAntiAdRules;
    const probabilityView = globalThis.TibiaAntiAdProbability;
    // The bundled evidence until storage answers with a newer download (tibia-rules.js).
    let classify = globalThis.TwitchCleanTibiaClassify.create(globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE);
    let evidence = globalThis.TWITCH_CLEAN_TIBIA_EVIDENCE;
    let enabled = true;
    let mode = 'hide';
    let threshold = S.DEFAULTS.tibiaThreshold;
    // Page-session records survive Twitch unmounting/recycling cards.
    const evaluated = new Map();
    const ordered = new Map();
    const restoreOrder = () => {
        for (const [cell, original] of ordered) {
            if (original.value) { cell.style.setProperty('order', original.value, original.priority); }
            else { cell.style.removeProperty('order'); }
        }
        ordered.clear();
    };
    const reorder = rows => {
        if (!enabled || mode !== 'bottom') { restoreOrder(); return; }
        const groups = new Map();
        for (const row of rows) {
            const parent = row.cell.parentElement;
            if (!parent || !/^(inline-)?(flex|grid)$/.test(getComputedStyle(parent).display)) { continue; }
            if (!groups.has(parent)) { groups.set(parent, []); }
            groups.get(parent).push(row);
        }
        const current = new Set(rows.map(row => row.cell));
        for (const [cell, original] of ordered) {
            if (!current.has(cell)) {
                if (original.value) { cell.style.setProperty('order', original.value, original.priority); }
                else { cell.style.removeProperty('order'); }
                ordered.delete(cell);
            }
        }
        const scroller = document.querySelector('[data-a-target="root-scroller"]');
        const scrolling = (scroller?.scrollTop || window.scrollY) > 0;
        const bottom = scroller ? Math.min(innerHeight, scroller.getBoundingClientRect().bottom) : innerHeight;
        for (const group of groups.values()) {
            // Freeze the visual prefix through the visible row. New cards join
            // only the unvisited suffix, keeping Twitch order inside both groups.
            const visual = group.filter(row => ordered.has(row.cell)).sort((a, b) => (Number(a.cell.style.order) || 0) - (Number(b.cell.style.order) || 0));
            let through = -1;
            if (scrolling) {
                visual.forEach((row, i) => { if (ordered.has(row.cell) && row.cell.getBoundingClientRect().top < bottom) { through = i; } });
            }
            const prefix = visual.slice(0, through + 1);
            const fixed = new Set(prefix.map(row => row.cell));
            const rest = group.filter(row => !fixed.has(row.cell));
            const sorted = [...prefix, ...rest.filter(row => !row.affected), ...rest.filter(row => row.affected)];
            sorted.forEach((row, i) => {
                const cell = row.cell;
                if (!ordered.has(cell)) { ordered.set(cell, {value: cell.style.getPropertyValue('order'), priority: cell.style.getPropertyPriority('order')}); }
                cell.style.setProperty('order', String(i), 'important');
            });
        }
    };
    let probabilityEnabled = Boolean(probabilityView);
    let shown = {};
    const hiddenByUs = new WeakSet();
    // Verdicts by channel, title and tags: Twitch re-renders the same cards often.
    const verdicts = new Map();
    const classifyCard = info => {
        const key = `${info.channel}\n${info.title}\n${info.tags.join('\n')}`;
        let result = verdicts.get(key);
        if (!result) {
            if (verdicts.size >= 1000) { verdicts.clear(); }
            result = classify(info.title, info.tags);
            verdicts.set(key, result);
        }
        return result;
    };

    const onTibiaDirectory = () => /^\/directory\/category\/tibia(\/|$)/i.test(location.pathname);

    const cardInfo = article => {
        const href = article.querySelector('a[data-a-target="preview-card-channel-link"], a[data-a-target="preview-card-image-link"]')?.getAttribute('href') || '';
        const channel = href.match(/^\/([a-z0-9_]{1,25})\/?$/i)?.[1]?.toLowerCase();
        let meta = null;
        try {
            meta = JSON.parse(article.getAttribute(META) || 'null');
            if (meta && typeof meta.channel === 'string' && (!channel || meta.channel === channel)
                && typeof meta.title === 'string' && meta.title.trim()
                && Array.isArray(meta.tags) && meta.tags.every(tag => typeof tag === 'string')) { return meta; }
        } catch { /* fall back to the visible card */ }
        if (!channel) { return null; }
        const heading = article.querySelector('h4[title], h3[title], h4, h3');
        const title = heading?.getAttribute('title') || heading?.textContent || '';
        const tags = meta?.channel === channel && Array.isArray(meta.tags) && meta.tags.every(tag => typeof tag === 'string') ? meta.tags
            : [...article.querySelectorAll('[data-a-target="tw-tag"], .tw-tag')].map(t => t.textContent.trim()).filter(Boolean);
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
            if (probabilityEnabled) { probabilityView.render(article, result); }
            article.setAttribute('data-tibia-private-result', JSON.stringify(result));
            verdict = enabled ? (result.display_probability < threshold ? 'hidden' : 'shown') : null;
            const overridden = verdict === 'hidden' && shown[info.channel] === info.title;
            if (enabled) { cell.setAttribute(VERDICT, `${verdict}: ${(result.private_probability * 100).toFixed(2)}% private server${overridden ? ' (shown by you)' : ''}`); }
            else { cell.removeAttribute(VERDICT); }
            if (overridden) { verdict = 'shown'; }
            evaluated.set(info.channel, {viewers: null, ...info, ...result, hide: result.display_probability < threshold,
                displayed_percentage: result.display_probability * 100,
                displayed_text: globalThis.TwitchCleanTibiaClassify.formatDisplay(result.display_probability),
                percentage_shown: Boolean(article.querySelector('.tibia-probability-value')),
                contributions: result.contributions.map(c => ({...c, weight: evidence.model.weights[c.feature]})),
                hidden: verdict === 'hidden' && mode === 'hide', affected: verdict === 'hidden'});
        }
        else { probabilityView?.remove(article); }
        if (verdict === 'hidden' && mode === 'hide') {
            if (!hiddenByUs.has(cell)) { requestMore(); }
            cell.setAttribute(MARK, '');
            hiddenByUs.add(cell);
        }
        else if (hiddenByUs.has(cell)) { cell.removeAttribute(MARK); hiddenByUs.delete(cell); }
        return { cell, classified: enabled && Boolean(info), affected: verdict === 'hidden', hidden: verdict === 'hidden' && mode === 'hide' };
    };

    // Twitch can reuse or regroup grid wrappers, and copied marks outlive the
    // WeakSet that created them. Reconcile our empty-valued marks against the
    // cells classified in this scan; preserve nags.js's nonempty marks.
    const reconcile = (classified = new Set(), hidden = new Set()) => {
        for (const cell of document.querySelectorAll(`[${VERDICT}], [${MARK}=""]`)) {
            if (!classified.has(cell)) { cell.removeAttribute(VERDICT); }
            if (!hidden.has(cell) && cell.getAttribute(MARK) === '') {
                cell.removeAttribute(MARK);
                hiddenByUs.delete(cell);
            }
        }
    };

    const scan = () => {
        if (!onTibiaDirectory()) {
            evaluated.clear();
            restoreOrder();
            probabilityView?.clear();
            reconcile();
            scheduleReport();
            return;
        }
        const classified = new Set(), hidden = new Set();
        const rows = [];
        for (const article of document.querySelectorAll('article')) {
            const result = apply(article);
            rows.push(result);
            if (result.classified) { classified.add(result.cell); }
            if (result.hidden) { hidden.add(result.cell); }
        }
        reconcile(classified, hidden);
        reorder(rows);
        scheduleReport();
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
            if (!scroller || !enabled || !onTibiaDirectory()) { return; }
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
        if (wanted) { observer.observe(document.body, { childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ['href', 'title', META] }); }
        else { observer.disconnect(); }
        scan();
    };
    const start = () => {
        scan();
        follow();
        globalThis.navigation?.addEventListener?.('currententrychange', follow);
        setInterval(follow, 1000);
    };
    // Cards this script hides on the current page, for the settings pages.
    const hiddenCards = () => [...document.querySelectorAll('article')].flatMap(article => {
        const info = cardInfo(article);
        if (!enabled || mode === 'show' || !info || !evaluated.get(info.channel)?.affected) { return []; }
        const reason = `${(classifyCard(info).private_probability * 100).toFixed(2)}% private server`;
        return [{ channel: info.channel, title: info.title, reason, game: 'Private servers', ...classifyCard(info) }];
    });
    // Report the hidden cards for the Safari app's popover whenever they change.
    let lastReport = '';
    const report = () => {
        const onDirectory = onTibiaDirectory();
        const hidden = enabled && onDirectory ? hiddenCards() : [];
        const value = JSON.stringify([onDirectory, mode, threshold, hidden]);
        if (value === lastReport) { return; }
        lastReport = value;
        api.runtime.sendMessage({ type: 'tibia-anti-ad:hidden-report', url: location.href, onDirectory, mode, threshold, hidden }).catch(() => {});
    };
    let reportTimer = 0;
    const scheduleReport = () => { clearTimeout(reportTimer); reportTimer = setTimeout(report, 500); };
    const diagnostics = () => {
        scan();
        const data = evidence;
        const present = new Set([...document.querySelectorAll('article')].map(cardInfo).filter(Boolean).map(info => info.channel));
        return {captured_at: new Date().toISOString(), url: location.href,
            extension_version: api.runtime.getManifest().version, model_revision: data.revision,
            model_sha256: data.model_sha256, threshold, threshold_metric: 'display_probability', mode, enabled,
            streams: [...evaluated.values()].map(row => ({...row, present_on_page: present.has(row.channel)}))};
    };
    api.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message?.type === 'tibia-anti-ad:tibia-diagnostics') {
            sendResponse(diagnostics());
            return false;
        }
        if (message?.type === 'tibia-anti-ad:export-diagnostics') {
            try {
                if (!onTibiaDirectory()) { throw new Error('Open the Twitch Tibia category first.'); }
                const data = diagnostics();
                // Download in the page's origin, avoiding Safari's unsupported
                // downloads API and extension-origin blob restrictions.
                const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2) + '\n'], {type: 'application/json'}));
                const link = document.createElement('a');
                link.href = url;
                link.download = `tibia-diagnostics-${data.captured_at.replace(/[:.]/g, '-')}.json`;
                document.body.append(link);
                link.click();
                link.remove();
                setTimeout(() => URL.revokeObjectURL(url), 60000);
                sendResponse({ok: true, count: data.streams.length});
            } catch (error) { sendResponse({ok: false, error: error.message}); }
            return false;
        }
        if (message?.type !== 'tibia-anti-ad:tibia-hidden') { return false; }
        sendResponse({ onDirectory: onTibiaDirectory(), enabled, mode, threshold, hidden: enabled && onTibiaDirectory() ? hiddenCards() : [] });
        return false;
    });

    const load = () => Promise.all([S.load(api), api.storage.local.get({ tibiaShown: {}, [R.KEY]: null })])
        .then(([settings, stored]) => {
            const { tibiaShown } = stored;
            evidence = R.current(stored[R.KEY]);
            classify = globalThis.TwitchCleanTibiaClassify.create(evidence);
            verdicts.clear();
            mode = settings.tibiaMode;
            threshold = settings.tibiaThreshold;
            enabled = settings.enabled && mode !== 'show';
            shown = tibiaShown && typeof tibiaShown === 'object' ? tibiaShown : {};
            // Recalculate retained records too when the model or threshold changes.
            for (const [channel, row] of evaluated) {
                const result = classify(row.title, row.tags);
                const affected = enabled && result.display_probability < threshold && shown[channel] !== row.title;
                evaluated.set(channel, {...row, ...result, hide: result.display_probability < threshold, displayed_percentage: result.display_probability * 100,
                    displayed_text: globalThis.TwitchCleanTibiaClassify.formatDisplay(result.display_probability), affected, hidden: affected && mode === 'hide',
                    contributions: result.contributions.map(c => ({...c, weight: evidence.model.weights[c.feature]}))});
            }
            probabilityEnabled = Boolean(probabilityView) && settings.enabled;
            if (!probabilityEnabled) { probabilityView?.clear(); }
            scan();
        });
    api.storage.onChanged.addListener((changes, area) => {
        if (area === 'local' && (changes.tibiaFilter || changes.tibiaMode || changes.tibiaThreshold || changes.enabled || changes.tibiaShown || changes[R.KEY])) { load(); }
    });
    load();
    if (document.body) { start(); }
    else { document.addEventListener('DOMContentLoaded', start, { once: true }); }
})();
