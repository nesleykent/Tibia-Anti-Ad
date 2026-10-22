# guildstats.eu validation (rev 1, 2026-10-21)

## Site stack
- AdSense ca-pub-3086877587442670: 2 manual slots per page plus Auto Ads (in-page, anchor and vignette).
- Ad Traffic Quality ep1/ep2.
- Funding Choices (FCCDCF/FCNEC cookies).
- GA4 G-TX01L3PQ6S.
- Cloudflare Web Analytics.
- No Prebid/ID-sync, no inline obfuscated anti-adblock. The only anti-adblock is the passive `images/bad.png` background ("Please turn off your AdBlock") behind each slot wrapper.

## Verified (built-in Chromium pane)
- Recon done on `/` and `/bosses/The+Lily+of+Night` at desktop width, and on `/guild/United` at 375 px.
- With the cosmetic CSS injected:
  - desktop boss page: 0 visible ad or nag elements, no gap at the top;
  - mobile guild page: content, header, search and nav are intact.
- The top wrapper (`margin-top:-100px;height:100px`) collapses with zero net shift.
- No scroll-lock, key or wheel hijack by the site. `scroll-behavior: smooth` is site CSS and harmless.
- AdSense vignette intercepts navigation (URL gets `#google_vignette`). This is covered by the AdSense host rules.

## Simulated
- Network blocking was emulated by clearing AdSense's inline `body` padding (342 px top on mobile, 154 px bottom on desktop, reserved for the anchor ad).

## Assumed / not verified
- **Network rules apply in Safari uBOL custom filters.** Canary: `||guildstats.eu/images/bad.png^` is in the list. With cosmetic filtering off, the "Please turn off your AdBlock" banner should vanish behind empty slots.
- **Vignette `ins` carries inline `display:block !important`.** Author CSS can't override it; I confirmed this in the pane. uBOL injects user-origin CSS in Chrome, which should win. Safari is unverified, so rely on the network block.
- Funding Choices cosmetic selectors (`.fc-ab-root` etc.) were not rendered in the test, so they are unverified.
- Forum (`/forum/*`) was not inspected: it sits behind a Cloudflare challenge that was not bypassed. The list leaves `challenges.cloudflare.com` alone.

## uBOL cannot fix (only if network rules don't apply in Safari)
- AdSense's inline `body` padding and the vignette's inline `!important` display. Both disappear once `pagead2.googlesyndication.com` is blocked.

Rev 1 had no userscript; rev 2 adds an optional one (see below).

## Rev 2 (user report: "still ads")
- Reproduced worst case in pane (AdSense loading, list CSS injected as author CSS): the only survivor was
  `html > div#google-anno-sa` (+ `-glow`), AdSense's "ad intents" bottom bar ("Join Associations", "Tibia game guide").
  Every property on it and on all its children is inline `!important` → page CSS cannot hide it (verified).
- Added `html > div[id^="google-anno"]` + `.google-anno-skip`. Works only if uBOL injects user-origin CSS (Chrome: yes; Safari: unverified).
- Optional `guildstats.eu.user.js`: removes the bar and the vignette/anchor `ins` under <html>, drops AdSense's body padding,
  strips `#google_vignette`. Verified live: bar present before (1) → 0 for 20 s after, main content intact.
- Still unknown: whether Safari applies the list's network rules (canary `bad.png`). If it does, none of this appears at all.

## Rev 3
- Found on tibiamonk.com (same AdSense account type): ad-intents chips `div.google-anno-sc` injected inside site text, inline `!important`.
  Added `##.google-anno-sc`; userscript v1.1 removes them (subtree observer, rAF-throttled). Not yet observed on guildstats itself.
