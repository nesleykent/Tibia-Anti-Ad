# tibiapal.com – validation summary (rev 2, 2026-10-21)

## What the site runs
- Google AdSense (`adsbygoogle.js`, `show_ads_impl`), auto-ads: anchor, vignette (`#google_vignette`), "ad intents" chip `#google-anno-sa`
- Ad Traffic Quality telemetry (`ep1/ep2.adtrafficquality.google`)
- GA4 + UA via gtag (`googletagmanager.com`, `analytics.google.com`, `stats.g.doubleclick.net`)
- Google Funding Choices (consent CMP + ad-blocking recovery), cookies `FCCDCF`/`FCNEC`
- Paid partner promos: TibiaTrade iframe (2 copies), IgłaOTS card, Bestiary Arena iframe, two sidebar affiliate links
- Anti-adblock: site's own `showAdblockPopup()` call is commented out; no bait elements; `onload.js` has no ad/adblock code. Only possible wall = Funding Choices recovery → blocked at network level.
- No scroll lock / key interception / custom scrollbar found in site code.

## Verified (built-in Chromium pane, CSS injected)
- All hosts above observed in `performance` entries on `/` and `/hunting`.
- Cosmetic selectors match real elements, at 1280px and 375px; no empty gaps after hiding (`#mobile-top-ad` was a 375×375 block on mobile, now gone; `#banner` is kept as a layout box (only its TibiaTrade children hidden); verified at 1600px that right sidebar and footer stay in place).
- Own-content cards (Discord, Kick live, YouTube) and tools/nav untouched.

## Simulated / assumed
- Network rules were not enforced in-pane (no extension). Whether uBOL on Safari applies custom network rules is **unverified** – run the canary below.
- `.fc-*` overlay selectors are standard Funding Choices markup, not seen on this site (unverified).
- `ins[data-vignette-loaded]` is Google's documented vignette marker; vignette itself not rendered while testing.

## Canary test for Safari
Temporarily add `||tibiapal.com/images/mainlogo.png^`, reload: if the beaver logo disappears, network rules work. Remove it afterwards.
If they do NOT work: all visible units are still covered cosmetically, but GA/AdSense/FC requests can't be blocked from the custom list.

## uBOL cannot fix
Nothing identified. No userscript needed (no inline anti-adblock, no DOM wipe).

## Install
uBOL → Settings → Custom filters → paste `tibiapal.com.txt` → Save. Set tibiapal.com filtering mode to **Optimal** or **Complete** (cosmetic rules need it).

## Rev 3 – Safari report (ad-intents side sheet)
- The user saw Google "ad intents" in Safari: in-text ⊞ keyword links ("hunting", "Calculator") opening a right-hand ad sheet.
- These only exist when `pagead2.googlesyndication.com` loads, so in Safari the `||pagead2…^` network rule is **not taking effect**. Treat Safari custom network rules as not working until the canary proves otherwise.
- Added unverified catch-all cosmetic rules for the sheet (Advertisement iframes, google-anno containers). The in-text keyword links can't be safely hidden with CSS (they wrap real words), so in Safari they stay visible but lead nowhere once the sheet is hidden.
