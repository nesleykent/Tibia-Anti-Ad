# forum.portaltibia.com.br validation (rev 1, 2026-10-21)

Tested in **Chrome Beta**, launched with a throwaway profile and a DevTools port, because the forum is behind a Cloudflare challenge. The non-interactive challenge passed on its own; nothing was clicked.

## Site stack (Invision Community + IPSFocus theme)
- **PremiumAds wrapper** (`tags.premiumads.com.br`): GPT plus Prebid. Bidders seen: Rubicon, Criteo, Equativ/Smart, OneTag, TripleLift, Xandr, Seedtag. Engine config adds Teads, Taboola, Membrana, k-words, a vignette interstitial, in-text outstream, a sticky anchor and MGID.
- **MGID** native widgets (`jsc.mgid.com`, plus its cookie-match chain to ~10 SSPs).
- **Trackers and ID-sync:** Navegg DMP, ID5, LiveRamp, Lotame, Eyeota, Outbrain, MediaMath, Yahoo and others.
- **Analytics:** Facebook Pixel, GA4 (two properties), Yandex Metrica, Cloudflare Web Analytics.
- **Visible units:**
  - top leaderboard (970x250 desktop, 468x60 mobile);
  - footer leaderboard;
  - sticky bottom anchor (80 px desktop, 130 px mobile).
- **FansitesBR fixed icon bar** on the left edge.
- **No anti-adblock** in the PremiumAds tag, IPS bundles or inline scripts.
- **No scroll, key or wheel hijack.**
- **Hidden fixed layers, kept:** the IPSFocus layout editor and the reCAPTCHA challenge backdrop.

## Verified (Chrome Beta via CDP, list hosts blocked with `Network.setBlockedURLs`, list CSS injected)
| Page | Width | Network + CSS | CSS only |
|---|---|---|---|
| Home | 1280 | clean, 9 requests attempted, all blocked | clean; 120 px blank at page bottom |
| Topic (article) | 1280 | clean | clean; 120 px blank at page bottom |
| Topic | ~500 | clean | clean |
| Home | ~500 | clean | clean |

- **What survived:** nothing ad-related. The only iframes left are the article's own YouTube embeds.
- **What still works:** posts (123 on home, 8 on the topic), search, chatbox, the mobile footer nav, the sticky site header and the partner-fansite footer.
- **Harness bug, now fixed:** the first CSS injection ran before `<html>` existed and silently did nothing. The table above comes from the corrected harness, which confirms the stylesheet is applied on every run.
- **Fix found during validation:** without the engine, the slot divs have no id, because the `P_FORUM_PORTAL_TIBIA_*` id is added by JS. The rules now target the server-side `div[data-premium]` / `[data-adunit]` plus the trailing `<br>`.
- **Mobile caveat:** Chrome's minimum window width is ~500 px, so "mobile" means the site's ≤500 px responsive layout, not 375 px.

## Assumed / unverified
- **Safari network rules:** whether uBOL on Safari applies custom network rules is still unknown. Run the guildstats canary test.
- **Unrendered units:** MGID, Seedtag and `.pp-sticky-this` selectors are taken from engine code, not seen rendered.
- **Forum area:** the logged-in view was not tested.

## uBOL cannot fix (only if Safari ignores the network rules)
- `body.openAnchor { margin-bottom: 120px }` from PremiumAds' injected CSS: a blank strip at the end of desktop pages. A hide rule can't remove a margin. It is cosmetic only, so I wrote no userscript.

## Judgment call
- The FansitesBR icon bar (`#myiconmenu` plus `www.fansitesbr.com`) is hidden as a floating cross-promo strip. Delete those 2 lines to keep it.
- The partner-fansite banners in the footer are site content and stay.

## Rev 2
- Documented the ad-driven forced redirect to tibiaring.com observed on portaltibia.com.br (same PremiumAds network); see portaltibia.com.br-validation.md. No rule change: the existing ad-stack blocks already prevent it.
