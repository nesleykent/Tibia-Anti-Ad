// Tibia Anti-Ad: Blocked Streams, the page that lists the Tibia category streams
// the filter hides, grouped by category, with search, a category filter and a
// Show button for each. "Show" stores {channel: title} in tibiaShown: that
// broadcast stays visible until its title changes; "Hide" undoes it. The
// settings popover opens this page with ?tab=<id> of the Twitch tab to list.
(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const S = globalThis.TibiaAntiAdSettings;
    // Oldest "Show" overrides are dropped beyond this many.
    const MAX_SHOWN = 200;
    const tabId = Number(new URLSearchParams(location.search).get('tab')) || null;

    let settings = S.resolve();
    let shown = {};
    let hidden = [];
    let reachable = false;

    const $ = id => document.getElementById(id);
    const plural = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`;

    const item = (title, details, buttonLabel, buttonName, onClick) => {
        const li = document.createElement('li');
        li.className = 'row';
        const text = document.createElement('div');
        text.className = 'row-text';
        const name = document.createElement('span');
        name.className = 'row-title';
        name.textContent = title;
        text.append(name);
        for (const [value, className] of details) {
            const line = document.createElement('span');
            line.className = className;
            line.textContent = value;
            line.title = value;
            text.append(line);
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'button';
        button.textContent = buttonLabel;
        button.setAttribute('aria-label', buttonName);
        button.addEventListener('click', onClick);
        li.append(text, button);
        return li;
    };

    // Keeps keyboard focus on the button now in the same place when a row goes
    // away; the lists are rebuilt, so look them up again.
    const keepFocus = (containerId, index) => {
        const buttons = $(containerId).querySelectorAll('button');
        (buttons[Math.min(index, buttons.length - 1)] || $('search')).focus();
    };

    const matches = (card, words) => words.every(word =>
        `${card.channel} ${card.title} ${card.reason} ${card.game}`.toLowerCase().includes(word));

    const renderHidden = () => {
        const words = $('search').value.toLowerCase().split(/\s+/).filter(Boolean);
        const category = $('filter').value;
        const groups = new Map();
        for (const card of hidden) {
            if ((category && card.game !== category) || !matches(card, words)) { continue; }
            if (!groups.has(card.game)) { groups.set(card.game, []); }
            groups.get(card.game).push(card);
        }
        let position = 0;
        const sections = [...groups].sort((a, b) => b[1].length - a[1].length).map(([game, cards], index) => {
            const section = document.createElement('section');
            const id = `h-group-${index}`;
            section.setAttribute('aria-labelledby', id);
            const heading = document.createElement('h2');
            heading.className = 'group-header';
            heading.id = id;
            heading.textContent = game;
            const count = document.createElement('span');
            count.className = 'count';
            count.textContent = ` ${cards.length}`;
            heading.append(count);
            const list = document.createElement('ul');
            list.className = 'group list-group';
            list.setAttribute('aria-labelledby', id);
            list.append(...cards.map(card => {
                const at = position++;
                return item(card.channel, [[card.title, 'detail'], [card.reason, 'detail reason']],
                    'Show', `Show ${card.channel}`, () => setShown(card.channel, card.title).then(() => keepFocus('groups', at)));
            }));
            section.append(heading, list);
            return section;
        });
        $('groups').replaceChildren(...sections);
        const empty = $('empty');
        empty.hidden = sections.length > 0;
        empty.textContent = !reachable ? 'Open the Tibia category on Twitch, then choose Manage Blocked Streams again to see the streams hidden there.'
            : !S.active(settings, 'tibiaFilter') ? 'Other games are shown in Twitch order.'
            : hidden.length ? 'No blocked streams match.' : 'No streams are affected on this page.';
        const showing = sections.reduce((sum, s) => sum + s.querySelectorAll('li').length, 0);
        $('status').textContent = !reachable ? '' : showing === hidden.length
            ? `${plural(hidden.length, 'stream')} ${settings.tibiaMode === 'bottom' ? 'moved to bottom' : 'hidden'} on the Twitch page`
            : `${showing} of ${plural(hidden.length, 'stream')} shown`;
    };

    const renderFilter = () => {
        const select = $('filter');
        const current = select.value;
        const games = [...new Set(hidden.map(card => card.game))].sort();
        select.replaceChildren(new Option('All Categories', ''), ...games.map(game => new Option(game, game)));
        select.value = games.includes(current) ? current : '';
    };

    const renderShown = () => {
        const list = $('shown-list');
        list.replaceChildren(...Object.entries(shown).map(([channel, title], i) =>
            item(channel, [[title, 'detail']], 'Hide', `Hide ${channel} again`, () => setShown(channel, null).then(() => keepFocus('shown-list', i)))));
        $('shown-section').hidden = !list.children.length;
    };

    // Asks the Tibia filter in the Twitch tab which cards it hides.
    const refresh = () => {
        if (!tabId) { reachable = false; hidden = []; renderFilter(); renderHidden(); return Promise.resolve(); }
        return api.tabs.sendMessage(tabId, { type: 'tibia-anti-ad:tibia-hidden' }).then(response => {
            reachable = Boolean(response?.onDirectory);
            hidden = reachable ? response.hidden : [];
        }, () => { reachable = false; hidden = []; }).then(() => { renderFilter(); renderHidden(); });
    };

    // channel -> current title shows that broadcast; title null removes the override.
    const setShown = (channel, title) => {
        const next = { ...shown };
        delete next[channel];
        if (title !== null) { next[channel] = title; }
        const entries = Object.entries(next);
        shown = Object.fromEntries(entries.slice(Math.max(0, entries.length - MAX_SHOWN)));
        renderShown();
        // The filter rescans on the storage change; ask again once it has.
        return api.storage.local.set({ tibiaShown: shown }).then(() => new Promise(resolve => setTimeout(resolve, 150))).then(refresh);
    };

    const load = () => Promise.all([S.load(api), api.storage.local.get({ tibiaShown: {} })])
        .then(([loaded, { tibiaShown }]) => {
            settings = loaded;
            shown = tibiaShown && typeof tibiaShown === 'object' ? tibiaShown : {};
            renderShown();
        });

    const start = () => {
        $('search').addEventListener('input', renderHidden);
        $('filter').addEventListener('change', renderHidden);
        // Command-F (Control-F) goes to the search field, as in other Mac apps.
        document.addEventListener('keydown', event => {
            if (event.key === 'f' && (event.metaKey || event.ctrlKey)) { event.preventDefault(); $('search').focus(); }
        });
        api.storage.onChanged.addListener((changes, area) => {
            if (area === 'local' && (changes.tibiaShown || changes.tibiaFilter || changes.tibiaMode || changes.tibiaThreshold || changes.enabled)) { load().then(refresh); }
        });
        load().then(refresh).finally(() => {
            document.body.classList.remove('loading');
            $('search').focus();
        });
    };

    if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', start, { once: true }); }
    else { start(); }
})();
