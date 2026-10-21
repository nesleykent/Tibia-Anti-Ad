# hunt-analyser.com: validation summary (rev 1, 2026-10-21)

## What the site runs
- Google AdSense (`ca-pub-1239690848987120`): Auto ads plus a left-rail panel (`[data-controller="adsense-rail"]`, two `ins.adsbygoogle` slots). On mobile the filled rail was about 790px tall.
- Google Funding Choices CMP (`fundingchoicesmessages.google.com`, cookies `FCCDCF`/`FCNEC`)
- Google ad-traffic-quality probes (`ep1/ep2.adtrafficquality.google`). These load `google.com/recaptcha/api2/aframe`. The site itself has no reCAPTCHA, which I checked on `/users/new`.
- GA4 `G-2YSSBZ05FL` via GTM, and the Cloudflare Web Analytics beacon
- Functional third parties kept: cdnjs (Font Awesome) and fonts.googleapis.com

## Verified (built-in Chromium pane)
- Third-party hosts on `/home/index`, `/hunt_sessions` and `/creature_analysis` at 1024px, 1400px and 375px widths, rechecked after 6–7 s.
- Site JS: I fetched and searched all 77 import-map modules. There is no anti-adblock, scroll lock or key/wheel hijacking. `adsense_rail_controller` only collapses unfilled slots and the rail. There are no bait elements, so nothing needs a "do not hide" exception.
- Cosmetic CSS injected: the rail and its `<aside>` collapse to 0×0 with no gap at 375px and 1400px. No legitimate element matched the selectors. The creature filter and the session list still render.

## Simulated
- Network blocking was not run in the pane, because uBOL isn't installed there. The host list comes from the observed resource entries.

## Assumed / unverified
- Whether custom network rules apply in Safari uBOL. Use the canary rule at the top of the list to check.
- The Funding Choices consent and ad-block-recovery dialog never rendered here because the consent cookie was already set. The `.fc-*` selectors are Google's standard ones and haven't been seen on this site.

## What uBOL cannot handle
- Nothing found that needs it. No userscript needed (tier 2 not justified).
