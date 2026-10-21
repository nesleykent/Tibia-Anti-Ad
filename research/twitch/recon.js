// Read-only Twitch recon for the uBOL list. Paste into Safari's Web Inspector
// Console (Develop > Show Web Inspector > Console) on a twitch.tv page, press
// Return, then paste the copied JSON back. It collects element structure, the
// hostnames of loaded resources, and cookie/localStorage NAMES (never values).
// It also sends two empty requests to listed ad hosts to see whether Safari
// blocks them (plain rule form and $domain= rule form).
(async () => {
    const copyText = typeof copy === 'function' ? copy : null;
    const LISTED = ['ads.twitch.tv', 'spade.twitch.tv', 'client-event-reporter.twitch.tv', 'trowel.twitch.tv',
        'analytics.m7g.twitch.tv', 'ddacn6pr5v0tl.cloudfront.net', 'amazon-adsystem.com', 'doubleclick.net',
        'flashtalking.com', 'flxpxl.com', 'googlesyndication.com', 'm.media-amazon.com'];
    const TWITCH_CDN = /(^|\.)(twitch\.tv|twitchcdn\.net|jtvnw\.net|ttvnw\.net)$/;
    const hostOf = u => { try { return new URL(u, location.href).hostname; } catch { return ''; } };
    const clip = (s, n) => String(s || '').replace(/\s+/g, ' ').trim().slice(0, n);
    const ATTRS = ['data-a-target', 'data-test-selector', 'data-target', 'data-a-id', 'aria-label', 'role', 'href', 'src', 'style'];
    const desc = el => {
        let s = el.tagName.toLowerCase();
        if (el.id) s += '#' + el.id;
        for (const c of el.classList) s += '.' + c;
        for (const a of ATTRS) {
            const v = el.getAttribute(a);
            if (v === null) continue;
            s += `[${a}="${clip(a === 'href' || a === 'src' ? v.replace(/[?#].*$/, '') : v, 90)}"]`;
        }
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return `${s} {${Math.round(r.width)}x${Math.round(r.height)} ${cs.position}${cs.zIndex !== 'auto' ? ' z' + cs.zIndex : ''}}`;
    };
    const chain = (el, depth = 9) => {
        const out = [];
        for (let e = el; e && e !== document.documentElement && out.length < depth; e = e.parentElement) out.push(desc(e));
        return out;
    };
    const entry = (label, el) => ({ label, text: clip(el.textContent, 100), chain: chain(el), html: clip(el.outerHTML, 700) });
    const byText = (label, re, max = 3) => {
        const out = [];
        const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        for (let n = w.nextNode(); n && out.length < max; n = w.nextNode()) {
            if (re.test(clip(n.nodeValue, 200)) && n.parentElement) out.push(entry(label, n.parentElement));
        }
        return out;
    };

    const report = { v: 2, path: location.pathname, ua: navigator.userAgent, viewport: `${innerWidth}x${innerHeight}` };

    // Is uBOL's custom CSS live? Probe with a throwaway element matching a listed selector.
    const probe = document.createElement('div');
    probe.className = 'follow-prompt';
    probe.style.cssText = 'position:absolute;left:-9999px;top:0';
    document.body.append(probe);
    report.cosmeticRulesActive = getComputedStyle(probe).display === 'none';
    probe.remove();

    // Which hosts actually loaded, and did any listed (blocked) host get through?
    const hosts = {};
    for (const e of performance.getEntriesByType('resource')) {
        const h = hostOf(e.name);
        if (!h) continue;
        hosts[h] ??= {};
        hosts[h][e.initiatorType] = (hosts[h][e.initiatorType] || 0) + 1;
    }
    report.resourceHosts = hosts;
    report.listedHostsThatLoaded = Object.keys(hosts).filter(h => LISTED.some(l => h === l || h.endsWith('.' + l)));
    report.scriptHosts = [...new Set([...document.scripts].map(s => hostOf(s.src)).filter(Boolean))];

    // Direct test of the DNR rules: a blocked request rejects, an allowed one resolves.
    const tryFetch = async url => {
        const ctl = new AbortController();
        const timer = setTimeout(() => ctl.abort(), 6000);
        try { await fetch(url, { mode: 'no-cors', cache: 'no-store', signal: ctl.signal }); return 'loaded'; }
        catch { return 'blocked'; }
        finally { clearTimeout(timer); }
    };
    report.networkProbe = {
        plainRule: await tryFetch('https://edge.ads.twitch.tv/'),
        domainScopedRule: await tryFetch('https://s.amazon-adsystem.com/'),
    };

    // The elements from the screenshots, by visible text (EN and pt-BR).
    report.targets = [
        ...byText('learnMore', /^(learn more|saiba mais)$/i),
        ...byText('primeBenefits', /prime benefits|benef[ií]cios do prime/i),
        ...byText('appleDrop', /sub for 1 month|apple drop|apple tv/i),
        ...byText('animatedEmotesCallout', /animated emotes can be disabled|emotes animados/i),
        ...byText('adBreakBanner', /taking an ad break|intervalo comercial|pausa para an[uú]ncios/i),
        ...byText('adLabel', /^(ad|an[uú]ncio|sponsored|patrocinado|promoted|promovido)$/i),
    ];

    // Ad creatives and frames: iframes, non-Twitch media, banner-shaped images.
    report.iframes = [...document.querySelectorAll('iframe')].slice(0, 12).map(f => ({ host: hostOf(f.src), chain: chain(f, 7) }));
    report.foreignMedia = [...document.querySelectorAll('img[src],video[src],video source[src]')]
        .filter(m => { const h = hostOf(m.src); return h && !TWITCH_CDN.test(h); })
        .slice(0, 12).map(m => entry('foreignMedia', m));
    report.bannerLike = [...document.querySelectorAll('img,video,canvas,iframe')]
        .filter(m => { const r = m.getBoundingClientRect(); return r.width >= 300 && r.height > 0 && r.width / r.height >= 4; })
        .slice(0, 6).map(m => entry('bannerLike', m));

    // Attribute hooks that look ad- or promo-related.
    const AD_RE = /(^|[-_\s])(ad|ads|sda|display-ad|sponsor\w*|promot\w*|upsell\w*|callout\w*|highlight\w*)([-_\s]|$)/i;
    report.adishHooks = [...new Set([...document.querySelectorAll('[class],[data-a-target],[data-test-selector]')]
        .filter(e => AD_RE.test(`${e.className?.baseVal ?? e.className} ${e.getAttribute('data-a-target') || ''} ${e.getAttribute('data-test-selector') || ''}`))
        .slice(0, 40).map(desc))];

    // Large fixed/sticky layers.
    report.fixedLayers = [...document.querySelectorAll('body *')].filter(e => {
        const cs = getComputedStyle(e);
        if (cs.position !== 'fixed' && cs.position !== 'sticky') return false;
        const r = e.getBoundingClientRect();
        return r.width * r.height > 5000;
    }).slice(0, 15).map(desc);

    report.cookieNames = document.cookie.split(';').map(c => c.split('=')[0].trim()).filter(Boolean);
    try { report.localStorageKeys = Object.keys(localStorage).slice(0, 80); } catch { report.localStorageKeys = 'unavailable'; }

    const json = JSON.stringify(report);
    try { copyText(json); console.log(`Copied ${json.length} characters. Paste them back into the chat.`); }
    catch { console.log(json); }
    return report;
})();
