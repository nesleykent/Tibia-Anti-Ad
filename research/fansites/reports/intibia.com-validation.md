# intibia.com – validation summary (rev 1, 2026-10-21)

## What the site runs
- Google Ad Manager (network 22659178643): `pages-leaderboard-<slug>` (970/728x90), `medium-rectangle-*` (300x250), `modal-skyscraper-left/right-*` (beside dialogs). Plus AdSense/adtrafficquality, cm.g.doubleclick ID sync.
- Funding Choices (`fundingchoicesmessages.google.com`, `ers=3`): consent banner and Google's ad-block recovery message.
- GA4 + GTM (`G-R30M5HD3FC`, `GTM-NJ5PV4J`), Hotjar 2734880, PostHog proxied on first-party `t.intibia.com` (recording, web vitals, dead clicks, **surveys pop-up**).
- First-party sponsor system: `/api/fetch-partner-orders` feeds sidebar "Partners" buttons, mobile fixed bottom "ad bar", footer stripe, partner tiles; `tibiatrade.gg/api/trade/exevopan` feeds "Featured on TibiaTrade" stripe.
- No site-side anti-adblock code found in any bundle; no scroll locks or key/wheel hijacking (html/body overflow is `visible`).

## Verified (built-in Chromium pane, desktop 1366px + mobile 375px)
- All third-party hosts collected via `performance.getEntriesByType('resource')`, homepage and /bestiary-tracker.
- Every cosmetic selector parses as plain CSS and matched only ad/sponsor elements (homepage + bestiary leaderboard); injected CSS leaves 0-height slots, no gaps, no horizontal scroll; nav (11 links) and character search remain visible.
- Sponsor components return `null` without data (read from bundle source), so the API block causes no empty frames.

## Simulated / assumed
- Network rules were not exercised in the pane (no uBOL there). Whether custom network rules apply in Safari uBOL is **unverified**: canary test suggested below.
- Modal skyscraper selectors come from bundle source (`translate-x-[calc(±100%…)]` wrappers); a dialog with ads was not opened.
- `.fc-consent-root`, `.fc-ab-root`, `PostHogSurvey*` are unverified backups (never rendered).
- Blocking `t.intibia.com` is assumed safe: only PostHog assets/events were seen on it.

## uBOL cannot handle / not needed
- Nothing found that requires a userscript, so no `intibia.com.user.js`.

## Safari canary test
Add `||intibia.com/api/fetch-partner-orders` (already in the list), reload with the cosmetic sponsor rules temporarily removed: if the sidebar "Partners" box no longer appears, custom network rules work.

## Install
uBOL → Settings → Custom filters → paste `intibia.com.txt`; set filtering mode for intibia.com to **Optimal** or **Complete** (cosmetic rules need it).
