// Safari-only presentation of the complement of the shared model's private-server probability.
// tibia-filter.js supplies the same result used for hiding, even when hiding is off.
(() => {
    'use strict';
    const ROW = 'data-tibia-probability-row';
    const BADGE = 'data-tibia-official-probability';
    const formatter = new Intl.NumberFormat(undefined, { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 });

    const remove = article => {
        for (const badge of article.querySelectorAll(`[${BADGE}]`)) { badge.remove(); }
        for (const row of article.querySelectorAll(`[${ROW}]`)) { row.removeAttribute(ROW); }
    };
    const clear = () => {
        for (const badge of document.querySelectorAll(`[${BADGE}]`)) { badge.remove(); }
        for (const row of document.querySelectorAll(`[${ROW}]`)) { row.removeAttribute(ROW); }
    };
    const render = (article, result) => {
        const link = article.querySelector('a[data-a-target="preview-card-channel-link"]');
        const name = link?.querySelector('p[data-a-target="preview-card-channel-link"], p');
        // Twitch's channel link wraps the title and a separate channel-name row.
        // Older layouts have a channel-only link next to the stream title.
        const row = name?.parentElement || (link && !link.querySelector('h4, h3') ? link.parentElement : null);
        if (!row || !result) { remove(article); return; }
        let badge = article.querySelector(`[${BADGE}]`);
        if (badge && badge.parentElement !== row) { remove(article); badge = null; }
        if (!row.hasAttribute(ROW)) { row.setAttribute(ROW, ''); }
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'tibia-official-probability';
            badge.setAttribute(BADGE, '');
            const label = document.createElement('span');
            label.className = 'tibia-probability-accessible-label';
            label.textContent = '1 \u2212 P(private server): ';
            const value = document.createElement('span');
            value.className = 'tibia-probability-value';
            badge.append(label, value);
            row.append(badge);
        }
        const probability = result.display_probability;
        const text = Number.isFinite(probability) ? probability < 0.0005 ? `<${formatter.format(0.001)}`
            : probability >= 0.9995 ? `>${formatter.format(0.999)}` : formatter.format(probability) : 'n/a';
        const value = badge.querySelector('.tibia-probability-value');
        if (value.textContent !== text) { value.textContent = text; }
        const raw = String(probability);
        if (badge.getAttribute(BADGE) !== raw) { badge.setAttribute(BADGE, raw); }
        const title = `1 \u2212 P(private server): ${text} (complement of model estimate)`;
        if (badge.title !== title) { badge.title = title; }
    };
    globalThis.TibiaAntiAdProbability = Object.freeze({ render, remove, clear });
})();
