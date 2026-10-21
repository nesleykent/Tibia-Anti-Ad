# tibiaring.com – validation summary (rev 1, 2026-10-21)

## What the site runs
- **Google AdSense** (`ca-pub-2228857895560066`): 3 manual units (left rail 160×600 in `nav#frt > div`, leaderboard `ins#gt`, 300×600 in `.indexshow`) plus **Auto ads** (in-content `.google-auto-placed`, top/bottom anchor, mobile pedestal, vignette interstitial). AdX creatives pull in Criteo, AdKernel, 2mdn and DoubleClick click-trackers.
- **Google Funding Choices** (`fundingchoicesmessages.google.com`): consent and ad-block recovery messaging.
- **Ad-traffic-quality / SODAR** (`ep1/ep2.adtrafficquality.google`), which loads a recaptcha aframe.
- **Analytics:** GA4 via gtag (`G-LCMM2VG6G1`).
- **Social:** Twitter share widgets, Facebook SDK (Like buttons and **comments on character pages**).
- **Google Identity Services:** "Sign in with Google" button only (`auto_prompt:false`, so there is **no One Tap pop-up**).
- **Site cookie bar:** created inline by `/tr/js/tr000.js`. It is an inline-styled `div` on `<body>`, auto-closes after 10 s and sets the `agreeCookies` cookie.
- **Anti-adblock:** none in the site's own code (`tr000.js` was searched for bait/probe/height checks and nothing was found). The only recovery mechanism is Funding Choices, and it is network-blocked.
- **Interaction hijacking:** none found. The `preventDefault` calls belong to the site's own menu, login and form handlers. There is no scroll lock or key/wheel capture. The inline `top.location` frame-buster only triggers when the site is framed.

## Verified (Chrome Beta 157 via CDP, desktop 1280 px and mobile 390 px with an iPhone UA; homepage and `char.php`)
How it was tested: the network rules were simulated with `Network.setBlockedURLs` and the cosmetic rules injected as a stylesheet at document start.
- Visible ad elements dropped from **11 to 0** (homepage) and **18 to 0** (character page). There are **no** leftover fixed/sticky ad layers, no gaps or empty frames (screenshots checked), and the AdSense anchor's `padding` on `<body>` no longer appears.
- Requests to the blocked hosts failed as intended.
- Still working: navigation, the side rails, the `#tr_banner` DUEL promo (first-party content, deliberately kept), the Google sign-in button and Facebook comments.
- The search box is present, but submitting it was **not** conclusively tested (the tab was already on the result page).
- On mobile, `#tr_banner` and the right rail are hidden by the **site's own** responsive CSS. A control run without the list showed the same.
- Cookie bar: reproduced by deleting `agreeCookies`. The plain-CSS selector `body > div[style*="position: fixed"][style*="bottom: 0px"][style*="z-index: 1000"]` matched it.

## Simulated / assumed
- **Safari + uBOL enforcement is untested.** Run the canary first: add `||www.tibiaring.com/tr/image/m/s/demon.gif^`, reload, and check that the demon icon disappears. Remove the canary afterwards.
- The cookie-bar selector relies on WebKit serializing inline styles as `position: fixed; … bottom: 0px; … z-index: 1000` (assumed, same as Chromium). The `:has(> #CookieAlertClose)` backup line covers it if Lite supports `:has`.
- The Funding Choices UI (`.fc-consent-root`, `.fc-ab-root`), the vignette and `#fads` selectors are **unverified**, because that markup never rendered during testing. They are standard markup used as a fallback.
- One unreproduced event: twice, just after passing a Cloudflare challenge, the tab ended up on `portaltibia.com.br`. Clean reloads never repeated it. If you see that redirect, send a screenshot and the URL bar.

## What uBOL can't handle
- **If Safari ignores custom network rules,** GA4, Funding Choices and SODAR will still load. Every ad slot still has a cosmetic rule, but there are side effects: AdSense's anchor adds `padding-top/bottom` to `<body>`, and Funding Choices can set `overflow:hidden` on `<body>`. A hide rule cannot undo either, because uBOL custom filters have no `:style()` or scriptlets. In that case a 3-line userscript would be justified; ask for one.
- The Facebook SDK is left on to keep comments working. To drop it, uncomment the `connect.facebook.net` rule in the list.

## Tier 2
No userscript is shipped: everything observed can be solved with uBOL network rules plus plain CSS.

## Install
1. In Safari, open uBOL settings, go to **Custom filters**, paste `tibiaring.com.txt` and save.
2. Set tibiaring.com to **Optimal** or **Complete** filtering mode, which cosmetic rules require.
3. Run the canary test above, then send screenshots of the homepage and a character page at both widths.

## Revision 2 – Safari feedback (2026-10-21)
- **Safari screenshot (rev 1):** every ad slot is hidden, so the cosmetic rules work in Safari uBOL.
- **"X Post" buttons were still visible.** Added plain-CSS rules for `iframe.twitter-share-button` and `a.twitter-share-button` (checked in Chrome: they match the button markup).
- **Blank band under the footer:** this matches the `padding-bottom: 120px` that AdSense's anchor adds to `<body>`. AdSense only sets it when its script loads, which suggests Safari is **not** enforcing the custom network rules. Not yet confirmed: run the canary.
- **Rails starting far down the page:** not caused by the filters. `tr000.js` moves both rails as you scroll (`#flt>div` / `#frt>div` get `margin-top`; reproduced in Chrome as 965 px after scrolling 1500 px). This is site behaviour and is left alone.
- **If the canary confirms network rules are ignored:** the `<body>` padding (and any `overflow:hidden` set by Funding Choices) cannot be undone by a uBOL hide rule. That is the one case where a minimal tier-2 userscript would be justified.

## Revision 3 – tier-2 userscript (2026-10-21)
- The user confirmed that the blank band under the footer persists in Safari, so AdSense is loading there and the custom network rules are not enforced.
- **Why uBOL can't fix it:** the band is an inline `padding: 0 0 120–154px` that AdSense writes on `<body>` for its anchor ad. uBOL custom filters can only hide elements (no `:style()`, no scriptlets), and hiding `<body>` is not an option.
- **Fix:** `tibiaring.com.user.js` injects `html,body{padding-top:0!important;padding-bottom:0!important}` at document-start. The site's own CSS sets no body padding, so nothing else changes.
- **Validated in Chrome**, with the cosmetic rules only and AdSense allowed to load, as in Safari. Control: computed padding `0 0 154px` (bug reproduced). With the fix: `0px`.
