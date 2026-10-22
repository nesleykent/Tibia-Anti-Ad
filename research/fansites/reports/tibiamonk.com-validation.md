# tibiamonk.com validation (rev 1, 2026-10-21)

## Site stack
- Next.js app.
- AdSense ca-pub-8195897520053223:
  - manual `autorelaxed` slots inside `<section aria-label="Advertisement">` (1 on /en, 5 on /en/hunts/monk);
  - Auto Ads: in-page, anchor (top 318 px + body padding 343 px on mobile, bottom on desktop), vignette, ad-intents bar `#google-anno-sa`, in-text chips `.google-anno-sc`.
- Ad Traffic Quality, csi.gstatic.com, Funding Choices, Cloudflare Web Analytics.
- Legit third parties, not blocked: dev.tibiadata.com (API), static.tibia.com, fonts, reCAPTCHA on sign-in.
- No anti-adblock: all Next.js chunks were scanned for adblock/survey/newsletter/onetap/toast/nudge/notification; only React internals matched.
- No scroll, key or wheel hijack. The `.scrollbar-tibiamonk` custom scrollbar is site CSS on the sidebar only and harmless; it can't be undone in uBOL (not needed).

## Verified (built-in Chromium pane)
- Recon on /en (desktop) and on /en/hunts/monk + /en/calculators/experience (375 px).
- With the list's CSS injected on /hunts/monk (mobile): all `section[aria-label="Advertisement"]`, `ins`, auto-placed units and the anchor are hidden. Header, nav, hunt list (58 items) are intact.
- **Survivors of CSS alone:** `#google-anno-sa` bar and the "Play Tabletop RPGs" chip inside the header title. Every property is inline `!important`, so author CSS loses.
- **Userscript logic** (run post-load on /calculators/experience): 6 elements present → 0, and still 0 for 16 s. The body padding is removed, the header text is unchanged, and the calculator input still updates results.

## Simulated / assumed
- Network blocking: not possible in the pane. Assumed to make all AdSense units, chips, bar and padding never appear.
- uBOL Safari: whether custom network rules apply, and whether its CSS is user-origin (which would beat inline `!important`), are both unverified. guildstats.eu's canary test (`bad.png`) answers the first question for both sites.
- Funding Choices cosmetic selectors were not rendered, so they are unverified.

## uBOL cannot fix (only if Safari ignores the network rules)
- AdSense inline-`!important` units (ad-intents bar, in-text chips, vignette, anchor body padding) → optional `tibiamonk.com.user.js`.
