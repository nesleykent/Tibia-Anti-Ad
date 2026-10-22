// Tibia Anti-Ad settings page: the toolbar popup and Safari's extension settings.
// Each switch is an <input type="checkbox" switch> whose data-setting names a
// settings.js key. Loaded in <head> so the switch style is chosen before the
// first paint: Safari draws input[switch] natively, other browsers use the CSS
// switch in popup.css.
document.documentElement.classList.toggle('native-switch', 'switch' in HTMLInputElement.prototype);

(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const S = globalThis.TibiaAntiAdSettings;
    const TWITCH = /^https?:\/\/([^/]+\.)?twitch\.tv(\/|$)/i;
    const TIBIA_DIRECTORY = /^https?:\/\/www\.twitch\.tv\/directory\/category\/tibia(\/|$|\?)/i;
    // Sections the viewer left open, remembered on this device only.
    const OPEN_KEY = 'tibia-anti-ad:open-sections';

    let settings = S.resolve();
    let shown = {};
    let rules = { fetchedAt: 0, error: null };
    let twitchTab = null;
    let reloadPending = false;

    const $ = id => document.getElementById(id);

    const plural = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`;

    // One switch per fansite, the site in the active tab first.
    const buildSites = activeUrl => {
        let host = '';
        try { host = new URL(activeUrl).hostname; } catch {}
        const covers = site => host === site.domain || host.endsWith('.' + site.domain);
        // The most specific match (forum.portaltibia.com.br over portaltibia.com.br).
        const current = S.SITES.filter(covers).sort((a, b) => b.domain.length - a.domain.length)[0];
        const sites = current ? [current, ...S.SITES.filter(site => site !== current)] : S.SITES;
        $('sites').replaceChildren(...sites.map(site => {
            const id = `site-${site.domain}`;
            const row = document.createElement('div');
            row.className = 'row';
            const label = document.createElement('label');
            label.className = 'row-text';
            label.htmlFor = id;
            const title = document.createElement('span');
            title.className = 'row-title';
            title.textContent = site.domain;
            const detail = document.createElement('span');
            detail.className = 'detail';
            detail.id = `d-${id}`;
            const parts = [site === current ? 'This site' : '', `${plural(site.rules, 'network rule')}, ${plural(site.selectors, 'hidden element')}`];
            detail.textContent = parts.filter(Boolean).join('. ') + (site.protected ? '. Also stops its anti-adblock wall.' : '.');
            label.append(title, detail);
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.setAttribute('switch', '');
            input.setAttribute('role', 'switch');
            input.id = id;
            input.dataset.setting = site.key;
            input.setAttribute('aria-describedby', detail.id);
            row.append(label, input);
            return row;
        }));
    };

    const renderSwitches = () => {
        const state = settings.enabled ? 'active' : 'inactive';
        const safari = api.runtime.getURL('').startsWith('safari-web-extension:');
        $('blocking-status-icon').src = safari
            ? `icons/safari-toolbar/${state}-64.png`
            : `icons/chrome-toolbar/${state}-128.png`;
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
        for (const section of document.querySelectorAll('.section')) {
            const inputs = [...section.querySelectorAll('.children input[data-setting]')];
            const on = inputs.filter(input => input.checked).length;
            section.querySelector('.count').textContent = !settings.enabled ? 'Paused' : `${on} of ${inputs.length} on`;
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

    // A one-line summary; the streams themselves are listed in manage.html.
    const renderSummary = response => {
        const hidden = response?.hidden || [];
        const onDirectory = S.active(settings, 'tibiaFilter') && Boolean(response?.onDirectory);
        const restored = Object.keys(shown).length;
        $('tibia-summary').hidden = !onDirectory && !restored;
        if (onDirectory) {
            const counts = new Map();
            for (const card of hidden) { counts.set(card.game, (counts.get(card.game) || 0) + 1); }
            const top = [...counts].sort((a, b) => b[1] - a[1]);
            $('tibia-summary-title').textContent = hidden.length ? `${plural(hidden.length, 'stream')} hidden on this page` : 'No streams hidden on this page';
            $('tibia-summary-detail').textContent = [
                ...top.slice(0, 2).map(([game, count]) => `${game} ${count}`),
                top.length > 2 ? `${top.length - 2} more` : '',
                restored ? `${restored} shown by you` : '',
            ].filter(Boolean).join(' \u00b7 ');
        } else {
            $('tibia-summary-title').textContent = `${plural(restored, 'stream')} shown by you`;
            $('tibia-summary-detail').textContent = 'Each stays visible until its title changes.';
        }
    };

    // Asks the Tibia filter in the active Twitch tab which cards it hides.
    const refreshHidden = () => {
        if (!twitchTab || !S.active(settings, 'tibiaFilter')) { renderSummary(null); return Promise.resolve(); }
        return api.tabs.sendMessage(twitchTab.id, { type: 'tibia-anti-ad:tibia-hidden' })
            .then(renderSummary, () => renderSummary(null));
    };

    // When the Tibia filter's evidence last came from GitHub (tibia-rules.js).
    const renderRules = () => {
        const time = rules.fetchedAt && new Date(rules.fetchedAt).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
        $('rules-detail').textContent = rules.error ? `Update failed: ${rules.error}.${time ? ` Using rules from ${time}.` : ' Using the built-in rules.'}`
            : time ? `Updated ${time} from GitHub. Checked every 6 hours.` : 'Built-in rules. Updates are checked every 6 hours.';
    };
    const updateRules = () => {
        $('rules-button').disabled = true;
        $('rules-detail').textContent = 'Checking for updates\u2026';
        api.runtime.sendMessage({ type: 'tibia-anti-ad:update-rules' })
            .catch(() => {}).finally(() => { $('rules-button').disabled = false; load(); });
    };

    // Opens the management page in a tab, linked to the Twitch tab it lists.
    const manage = () => {
        const query = twitchTab ? `?tab=${twitchTab.id}` : '';
        api.tabs.create({ url: api.runtime.getURL(`manage.html${query}`) }).then(() => window.close(), () => {});
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

    const readOpen = () => {
        try { return new Set(JSON.parse(localStorage.getItem(OPEN_KEY) || '[]')); }
        catch { return new Set(); }
    };
    const saveOpen = section => {
        const open = readOpen();
        if (section.open) { open.add(section.dataset.section); } else { open.delete(section.dataset.section); }
        try { localStorage.setItem(OPEN_KEY, JSON.stringify([...open])); } catch { /* not remembered */ }
    };
    // Remembered sections, plus the one about the active tab: the Tibia category
    // on its directory, the fansites on a fansite.
    const openSections = activeUrl => {
        const open = readOpen();
        if (TIBIA_DIRECTORY.test(activeUrl || '')) { open.add('tibia'); }
        if (S.SITES.some(site => { try { const host = new URL(activeUrl).hostname; return host === site.domain || host.endsWith('.' + site.domain); } catch { return false; } })) { open.add('sites'); }
        for (const section of document.querySelectorAll('.section')) { section.open = open.has(section.dataset.section); }
    };

    const reloadTwitch = () => {
        if (!twitchTab) { return; }
        api.tabs.reload(twitchTab.id);
        reloadPending = false;
        renderReload();
    };

    const load = () => Promise.all([S.load(api), api.storage.local.get({ tibiaShown: {}, tibiaEvidence: null, tibiaEvidenceError: null })])
        .then(([loaded, { tibiaShown, tibiaEvidence, tibiaEvidenceError }]) => {
            rules = { fetchedAt: tibiaEvidence?.fetchedAt || 0, error: tibiaEvidenceError?.message || null };
            renderRules();
            settings = loaded;
            shown = tibiaShown && typeof tibiaShown === 'object' ? tibiaShown : {};
            renderSwitches();
            refreshHidden();
        });

    const start = () => {
        $('version').textContent = `Version ${api.runtime.getManifest().version}`;
        document.addEventListener('change', onChange);
        $('reload-button').addEventListener('click', reloadTwitch);
        $('manage-button').addEventListener('click', manage);
        $('rules-button').addEventListener('click', updateRules);
        // Only the viewer's own clicks are remembered, not the sections opened for the active tab.
        for (const summary of document.querySelectorAll('.section > summary')) {
            summary.addEventListener('click', () => setTimeout(() => saveOpen(summary.parentElement)));
        }
        api.storage.onChanged.addListener((changes, area) => {
            if (area === 'local') { load(); }
        });
        const tab = api.tabs.query({ active: true, currentWindow: true })
            .then(([active]) => {
                twitchTab = active && TWITCH.test(active.url || '') ? active : null;
                buildSites(active?.url);
                openSections(active?.url);
            })
            .catch(() => { twitchTab = null; buildSites(''); openSections(''); });
        tab.then(load).finally(() => {
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
