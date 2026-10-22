// Twitch Clean: hides Twitch nags that have no stable CSS hook.
//
// Each rule needs two signals before it hides anything: the nag's own text and
// a structural anchor that ordinary content never has (the community-highlight
// card class, or the nag's own "Show me" button). Text inside chat messages is
// never considered, and every candidate must be small and contain no chat, so
// a chat line that quotes one of these strings, or the chat pane around it,
// stays visible. Matching uses Twitch's English UI strings. Hidden elements get
// data-twitch-clean-hidden, which hide.css turns into display:none.
(() => {
    'use strict';

    const MARK = 'data-twitch-clean-hidden';
    const MAX_DEPTH = 8;
    const MAX_TEXT = 160;
    // Chat containers: a candidate may never contain these.
    const CHAT_CONTENT = '[data-a-target="chat-line-message"], .chat-line__message, .chat-scrollable-area__message-container, [role="log"]';
    // Chat message bodies: text inside these is never considered. Narrower than
    // CHAT_CONTENT because Twitch can draw callouts inside the chat list itself.
    const CHAT_MESSAGE = '[data-a-target="chat-line-message"], .chat-line__message';

    const textOf = el => (el.textContent || '').replace(/\s+/g, ' ').trim();
    const isSmallNonChat = el => textOf(el).length <= MAX_TEXT
        && !el.closest(CHAT_MESSAGE) && !el.querySelector(CHAT_CONTENT);

    // Smallest ancestor (up to MAX_DEPTH levels, while still small) that also
    // contains a button whose text or aria-label matches `buttonRe`.
    const ancestorWithButton = (el, buttonRe) => {
        for (let node = el, depth = 0; node && node !== document.body && depth < MAX_DEPTH; node = node.parentElement, depth++) {
            if (!isSmallNonChat(node)) { return null; }
            for (const button of node.querySelectorAll('button, [role="button"]')) {
                const label = `${textOf(button)} ${button.getAttribute('aria-label') || ''}`;
                if (buttonRe.test(label)) { return node; }
            }
        }
        return null;
    };

    const RULES = [
        {
            // "Sub for 1 Month of Apple TV+ / Apple Drop" card at the top of chat.
            // FFZ identifies it as community highlight "mw-drop-available"; FFZ and 7TV
            // both target the card class, which polls, hype trains and pinned messages
            // share, so the card must carry both lines of the Apple drop. The title is
            // split across elements ("Sub for " + bold "1 Month of Apple TV+"), so each
            // piece triggers on its own.
            name: 'apple-tv-drop',
            text: /^(Apple Drop|(Sub for )?1 Month of Apple TV\+?)$/i,
            target: el => {
                const card = el.closest('.community-highlight-stack__card');
                if (!card) { return null; }
                const text = textOf(card);
                return /Apple Drop/i.test(text) && /Month of Apple TV/i.test(text) ? card : null;
            },
        },
        {
            // "Animated Emotes can be disabled in Settings" callout above the chat input,
            // anchored on its own "Show me" button.
            name: 'animated-emotes-callout',
            text: /^Animated Emotes can be disabled in Settings/i,
            target: el => ancestorWithButton(el, /^\s*Show me\b/i),
        },
        {
            // "Prime Benefits" dropdown over the player. Only the control itself is hidden.
            name: 'prime-benefits',
            text: /^Prime Benefits$/i,
            target: el => el.closest('button, [role="button"]'),
        },
    ];

    // Calls visit(rule, target) for every rule match among the text nodes under root.
    const forEachMatch = (root, visit) => {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
            const value = node.nodeValue;
            if (!value || value.length > 200 || !node.parentElement) { continue; }
            if (node.parentElement.closest(CHAT_MESSAGE)) { continue; }
            const text = value.replace(/\s+/g, ' ').trim();
            if (!text) { continue; }
            for (const rule of RULES) {
                if (rule.text.test(text)) { visit(rule, rule.target(node.parentElement)); }
            }
        }
    };

    // Marked elements, rechecked on every change: Twitch can reuse a card or
    // callout node for other content (a hype train, a poll), which must reappear.
    const marked = new Map();

    const hide = (rule, target) => {
        if (!target || marked.has(target)) { return; }
        if (!isSmallNonChat(target)) {
            console.debug(`[Twitch Clean] skipped ${rule.name}: candidate too large or inside/containing chat`);
            return;
        }
        target.setAttribute(MARK, rule.name);
        marked.set(target, rule);
        console.debug(`[Twitch Clean] hid ${rule.name}`);
    };

    const stillNag = (el, rule) => {
        if (!el.isConnected || !isSmallNonChat(el)) { return false; }
        let found = false;
        forEachMatch(el, (r, target) => { if (r === rule && target === el) { found = true; } });
        return found;
    };

    // Forgets detached elements (clearing their mark, so a node re-attached later
    // is judged afresh), then rechecks only marked elements whose content changed.
    // Returns the elements it unhid so the caller can scan them for a new nag.
    const revalidate = changed => {
        const unhidden = [];
        for (const [el, rule] of marked) {
            if (!el.isConnected) { el.removeAttribute(MARK); marked.delete(el); continue; }
            if (!changed.has(el) || stillNag(el, rule)) { continue; }
            el.removeAttribute(MARK);
            marked.delete(el);
            unhidden.push(el);
            console.debug(`[Twitch Clean] unhid ${rule.name}: content changed`);
        }
        return unhidden;
    };

    // Work happens directly in the observer callback, which runs once per batch
    // of DOM changes. Nothing is queued for later, so a background tab (where
    // Safari pauses animation frames and throttles timers) holds no extra nodes.
    const observer = new MutationObserver(records => {
        const roots = new Set();
        const changedMarked = new Set();
        for (const record of records) {
            const parent = record.type === 'characterData' ? record.target.parentElement : record.target;
            if (marked.size && parent) {
                const host = parent.closest(`[${MARK}]`);
                if (host) { changedMarked.add(host); }
            }
            if (record.type === 'characterData') {
                if (parent) { roots.add(parent); }
                continue;
            }
            for (const added of record.addedNodes) {
                if (added.nodeType === Node.ELEMENT_NODE) { roots.add(added); }
                else if (added.nodeType === Node.TEXT_NODE && added.parentElement) { roots.add(added.parentElement); }
            }
        }
        if (marked.size) {
            for (const el of revalidate(changedMarked)) { roots.add(el); }
        }
        for (const root of roots) {
            if (root.isConnected) { forEachMatch(root, hide); }
        }
    });

    const start = () => {
        // Marks left by an earlier copy of this script are not tracked; start clean.
        // Empty marks belong to the Tibia filter (tibia-filter.js) and stay.
        for (const el of document.querySelectorAll(`[${MARK}]:not([${MARK}=""])`)) { el.removeAttribute(MARK); }
        forEachMatch(document.body, hide);
        observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    };
    if (document.body) { start(); }
    else { document.addEventListener('DOMContentLoaded', start, { once: true }); }
})();
