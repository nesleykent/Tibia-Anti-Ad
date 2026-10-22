# tibia.fandom.com — validation summary (rev 1, 2026-10-21)

## Site stack observed (built-in browser, homepage + /wiki/Ferumbras, desktop ~700px and mobile 375px, rechecked after 7–8 s)
- Fandom Odyssey ad-engine, prebid, identity-engine (`script.wikia.nocookie.net/fandom-ae-assets/`), GPT (network 5441), Amazon APS, Criteo, GumGum, AdSense
- ID sync: Audigent `seg.ad.gt`, Yahoo ConnectID (`ups.analytics.yahoo.com`, localStorage `connectId*`), TradeDesk `match.adsrvr.org`, cookies `_pubcid`, `pbjs_unifiedid`
- Ad-block recovery: Google Funding Choices; ad-engine stores `cache_is_blocking_ads` / `cache_adblock_circumvent_score` (base64 keys) and loads rotating random-word hosts (`wear.hmphpointed.com`, `fun.whollyeven.com`)
- Analytics: `beacon.wikia-services.com`, Silversurfer SDK, Cloudflare Insights, Algolia search-insights
- Units: top_leaderboard (sticky), top/mid/incontent boxad (rail), bottom_leaderboard, featured video (JWPlayer), mobile floor_adhesion + interstitial; OneTrust banner; Google One Tap
- No scroll/key hijacking found: html/body overflow `visible`, no fixed overlays besides site nav. Inline obfuscated `a0s` script only wraps timers/listeners (no DOM wipe) → no tier 2 needed.

## Verified (in-page, Chromium pane)
- Cosmetic CSS injected: all `fandom-ad`, wrappers, labels and featured video report height 0; no gaps at top, rail or bottom on both widths (screenshots taken). Article content, nav, search button intact.

## Simulated / assumed
- Network rules were **not** enforced in the pane (no uBOL there). That blocking `fandom-ae-assets` does not break the page is **assumed** (EasyList has blocked it for years); that it also stops the random-word Admiral-style hosts is inferred from them only appearing after ad-engine loads.
- Safari/uBOL behaviour of custom network rules is **unverified**. Canary: temporarily add
  `||static.wikia.nocookie.net/tibia/images/*/Background*.png` (or any wiki background image URL from DevTools) and check it disappears.
- If network rules don't apply in Safari, every visible unit is still covered cosmetically; the requests themselves would then not be blockable in uBOL.

## uBOL can't handle
- Inline `a0s` timer wrapper and the inline `ads`/`fandomAdsSlotsConfig` config (harmless without the engine).
- Random-word ad hosts can't be pre-listed (covered only indirectly).
- Set filtering mode to **Optimal/Complete** for tibia.fandom.com, or cosmetic rules won't apply.

## rev 2
- Added `||brandmetrics.com^` for the Brand Metrics survey fly-in (source traced to ad-engine `BrandMetricsSurvey` → `cdn.brandmetrics.com/tag/.../fandom.com_au.js`). Cosmetic selectors are unverified guesses: the widget never rendered in the test browser.
