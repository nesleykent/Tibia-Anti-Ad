// Twitch Clean settings page: the toolbar popup and Safari's extension settings.
// Each switch is an <input type="checkbox" switch> whose data-setting names a
// settings.js key. Loaded in <head> so the switch style is chosen before the
// first paint: Safari draws input[switch] natively, other browsers use the CSS
// switch in popup.css.
document.documentElement.classList.toggle('native-switch', 'switch' in HTMLInputElement.prototype);

(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const S = globalThis.TwitchCleanSettings;
    // Oldest "Show" overrides are dropped beyond this many.
    const MAX_SHOWN = 200;
    const TWITCH = /^https?:\/\/([^/]+\.)?twitch\.tv(\/|$)/i;

    let settings = S.resolve();
    let shown = {};
    let twitchTab = null;
    let reloadPending = false;

    const $ = id => document.getElementById(id);

    const listItem = (title, detail, buttonLabel, buttonName, onClick) => {
        const item = document.createElement('li');
        item.className = 'list-item';
        const text = document.createElement('div');
        text.className = 'list-text';
        const name = document.createElement('span');
        name.className = 'row-title';
        name.textContent = title;
        const info = document.createElement('span');
        info.className = 'detail';
        info.textContent = detail;
        info.title = detail;
        text.append(name, info);
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'button';
        button.textContent = buttonLabel;
        button.setAttribute('aria-label', buttonName);
        button.addEventListener('click', onClick);
        item.append(text, button);
        return item;
    };

    const renderSwitches = () => {
        for (const input of document.querySelectorAll('input[data-setting]')) {
            const key = input.dataset.setting;
            let checked = settings[key];
            let disabled = key !== 'enabled' && !settings.enabled;
            if (key === 'backgroundQuality' && settings.enabled && settings.removeStreamAds) {
                checked = true;
                disabled = true;
            }
            input.checked = checked;
            input.disabled = disabled;
            input.closest('.row')?.classList.toggle('is-disabled', disabled);
        }
        $('d-backgroundQuality').textContent = settings.removeStreamAds
            ? 'Included with Remove stream ads.'
            : 'Stops Twitch lowering the quality in hidden tabs.';
        $('status').textContent = settings.enabled ? 'On' : 'Paused. Every feature is off.';
    };

    const renderReload = () => {
        $('reload').hidden = !reloadPending;
        $('reload-button').hidden = !twitchTab;
        $('reload-note').textContent = twitchTab
            ? 'Video changes apply when Twitch reloads.'
            : 'Video changes apply the next time Twitch loads.';
    };

    const renderShown = () => {
        const list = $('tibia-shown-list');
        list.replaceChildren(...Object.entries(shown).map(([channel, title]) =>
            listItem(channel, title, 'Hide', `Hide ${channel} again`, () => setShown(channel, null))));
        $('tibia-shown').hidden = !list.children.length;
    };

    const renderHidden = response => {
        const section = $('tibia-hidden');
        const list = $('tibia-hidden-list');
        const empty = $('tibia-hidden-empty');
        list.replaceChildren();
        // Shown only on the Tibia category, where the filter hides cards.
        section.hidden = !S.active(settings, 'tibiaFilter') || !response?.onDirectory;
        if (section.hidden) { return; }
        list.append(...response.hidden.map(card =>
            listItem(card.channel, card.reason, 'Show', `Show ${card.channel}`, () => setShown(card.channel, card.title))));
        empty.textContent = 'No streams hidden on this page.';
        empty.hidden = list.children.length > 0;
    };

    // Asks the Tibia filter in the active Twitch tab which cards it hides.
    const refreshHidden = () => {
        if (!twitchTab || !S.active(settings, 'tibiaFilter')) { renderHidden(null); return Promise.resolve(); }
        return api.tabs.sendMessage(twitchTab.id, { type: 'twitch-clean:tibia-hidden' })
            .then(renderHidden, () => renderHidden(null));
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
        return api.storage.local.set({ tibiaShown: shown }).then(() => setTimeout(refreshHidden, 150));
    };

    const onChange = event => {
        const input = event.target.closest?.('input[data-setting]');
        if (!input) { return; }
        const key = input.dataset.setting;
        settings = { ...settings, [key]: input.checked };
        api.storage.local.set({ [key]: input.checked });
        if (key === 'enabled' || key in S.RULESETS) {
            // The background script does the same on the storage change; this applies it now.
            api.declarativeNetRequest.updateEnabledRulesets(S.rulesetState(settings)).catch(() => {});
        }
        if (key === 'enabled' || S.RELOAD_KEYS.includes(key)) { reloadPending = true; }
        renderSwitches();
        renderReload();
        if (key === 'enabled' || key === 'tibiaFilter') { setTimeout(refreshHidden, 150); }
    };

    const reloadTwitch = () => {
        if (!twitchTab) { return; }
        api.tabs.reload(twitchTab.id);
        reloadPending = false;
        renderReload();
    };

    const load = () => Promise.all([S.load(api), api.storage.local.get({ tibiaShown: {} })])
        .then(([loaded, { tibiaShown }]) => {
            settings = loaded;
            shown = tibiaShown && typeof tibiaShown === 'object' ? tibiaShown : {};
            renderSwitches();
            renderShown();
        });

    const start = () => {
        $('version').textContent = `Version ${api.runtime.getManifest().version}`;
        document.addEventListener('change', onChange);
        $('reload-button').addEventListener('click', reloadTwitch);
        api.storage.onChanged.addListener((changes, area) => {
            if (area === 'local') { load(); }
        });
        const tab = api.tabs.query({ active: true, currentWindow: true })
            .then(([active]) => { twitchTab = active && TWITCH.test(active.url || '') ? active : null; })
            .catch(() => { twitchTab = null; });
        Promise.all([load(), tab]).finally(() => {
            renderReload();
            refreshHidden();
            // Reveal after a frame has been styled with the stored values, so the
            // switches appear in place instead of animating.
            requestAnimationFrame(() => requestAnimationFrame(() => document.body.classList.remove('loading')));
        });
    };

    if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', start, { once: true }); }
    else { start(); }
})();
