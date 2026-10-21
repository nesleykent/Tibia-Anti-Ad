// Twitch Clean: exposes each directory card's full stream metadata to the Tibia
// filter. A card shows only some tags; Twitch's own React props for the card
// hold the complete title, every freeform tag and the channel login. This runs
// in the page world (where those props live) and copies them into a
// data-twitch-clean-meta attribute that tibia-filter.js reads. Nothing is
// fetched. Runs only on the Tibia category directory.
(() => {
    'use strict';

    const ATTR = 'data-twitch-clean-meta';
    const onTibiaDirectory = () => /^\/directory\/category\/tibia(\/|$)/i.test(location.pathname);

    const metaOf = article => {
        const key = Object.keys(article).find(k => k.startsWith('__reactFiber'));
        for (let fiber = key && article[key], depth = 0; fiber && depth < 40; fiber = fiber.return, depth++) {
            const props = fiber.memoizedProps;
            if (props && typeof props.channelLogin === 'string' && typeof props.title === 'string') {
                const tags = props.tagListProps?.freeformTags?.map(t => t?.name).filter(t => typeof t === 'string') || [];
                return { channel: props.channelLogin.toLowerCase(), title: props.title, tags };
            }
        }
        return null;
    };

    const scan = () => {
        if (!onTibiaDirectory()) { return; }
        for (const article of document.querySelectorAll('article')) {
            const meta = metaOf(article);
            const value = meta ? JSON.stringify(meta) : null;
            // Cards are reused on scroll, so refresh whenever the props change.
            if (value && article.getAttribute(ATTR) !== value) { article.setAttribute(ATTR, value); }
        }
    };

    let queued = false;
    const observer = new MutationObserver(() => {
        if (queued) { return; }
        queued = true;
        queueMicrotask(() => { queued = false; scan(); });
    });
    const start = () => {
        scan();
        observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['href', 'title'] });
    };
    if (document.body) { start(); }
    else { document.addEventListener('DOMContentLoaded', start, { once: true }); }
})();
