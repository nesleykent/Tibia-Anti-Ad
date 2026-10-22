# hakaimarket.com – validation summary (rev 1, 2026-10-21)

## What the site runs
- React/Vite SPA (MUI), no ad networks, no Prebid/GPT/AdSense, no ID-sync, no consent banner, no anti-adblock.
- Telemetry: Vercel Web Analytics (`/_vercel/insights/script.js` + `/view` beacon). Firebase is bundled for **auth only** (`apis.google.com`, `*.firebaseapp.com`); no Firebase Analytics / GA initialised.
- Monetisation = partner/affiliate promos: Tibia Blackjack Halloween pop-up (1.2 s delay, once per session), header "FREE 25 TC" referral button, otPokémon banner slot, and a footer strip that holds only partners (tibiatrade.gg listing feed, Tibia Blackjack, EdgarTC, Bestiary Arena/Twitch).

## Verified (in the built-in Chromium pane, CSS injected)
- Pop-up backdrop + dialog both matched (2 elements) and hidden; centre of the page is clickable (`landing-grid` is the top element).
- Header: only the legitimate controls remain (login, server, theme, language, changelog, donate, Discord, Instagram).
- Footer + "PARTNERS" toggle hidden; the footer contains nothing else.
- SPA navigation works (/ → /market, /monsters/dragon). /market currently shows the site's own "Under Maintenance" notice, regardless of the filters.
- Desktop (1024 px) and mobile (375 px) recon done. No scroll locks or wheel/key hijacks on the homepage or monster pages. The wheel listeners belong to the map/hunt zoom (legitimate), and body-overflow is only in the Bosses modal (legitimate).

## Simulated / assumed
- The network rules (`_vercel/insights`, `tibiatrade.gg$3p`) were **not** enforced in this pane. Whether uBOL applies custom network rules in Safari is still unproven, so run a canary test: add `||hakaimarket.com/assets/halloween/12.gif^`, reload, and see whether the pumpkin icon in the pop-up/changelog disappears.
- The `[style*="z-index: 9998"]` selectors assume Safari serialises React inline styles the same way Chromium does (`z-index: 9998;`). This is very likely but not tested in Safari.
- `.changelog-card-featured` is an editorial call: it currently holds the partner event. Drop that line if you want featured news back.
- A "discordWelcome" modal exists in the i18n strings, but no rendering code was found, so it has no rule.

## uBOL can't fix / not needed
- Nothing. No userscript is needed (tier 2 not justified).
- If Safari ignores custom network rules, Vercel's pageview beacon keeps firing (first-party path, invisible); the promos stay hidden by cosmetic rules.
