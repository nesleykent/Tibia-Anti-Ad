# exevopan.com — validation summary (rev 1, 2026-10-21)

## What the site runs
- Next.js app; third-party hosts loaded: `bestiaryarena.com` (promo iframes), `i.imgur.com` (promo art),
  `static.tibia.com` / `tibiatrade.gg` (content images), `youtube-nocookie.com` (blog embeds).
- **No ad networks, analytics, trackers, ID-sync, cookies or consent banners** found (resource list, scripts,
  `_app` bundle keyword scan for gtag/GTM/umami/plausible/posthog/clarity/hotjar/sentry/vercel/adsbygoogle/survey/newsletter/onetap).
  The only beacon is NextAuth's own `/_log` error logger (first-party, functional; left alone).
- No anti-adblock, scroll locks or key/wheel hijacking found. The `z-index:9999` fixed div is the empty,
  `pointer-events:none` toast container (harmless).
- Promos: Bestiary Arena iframes (mobile top, footer, floating video bottom-right), affiliate links/logos
  (otPokémon, Tibia Blackjack, Rei dos Coins, Edgar Tc; Ravendawn/NoPing in the rotation pool),
  floating "Get Exevo Pro" upsell pill, TibiaTrade carousel.

## Verified (built-in browser, CSS injected, homepage at 375px + blog article at 1024px)
- All external promo links/iframes hidden; nothing left visible except the legitimate YouTube embed.
- Footer sponsor row and banner box collapse fully (no empty boxes); the floating stack is gone.
- 12 auction cards, search input and article content still render.

## Simulated / assumed
- Network rules: not tested in Safari. **Canary**: the Tibia Blackjack footer logo
  (`/public/assets/tibiablackjack.png`). With the cosmetic rule removed, if it fails to load, network rules work.
- `:has()` TibiaTrade rule is optional; uBOL may skip it (assumed).
- Ravendawn/NoPing selectors come from page JSON; I never saw them rendered (unverified).
- Visual screenshot at desktop failed (the pane was hidden), so the DOM checks are the evidence there.

## uBOL can't fix
- Nothing required. No userscript is needed, so there is no `.user.js`.
