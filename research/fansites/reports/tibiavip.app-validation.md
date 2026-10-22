# tibiavip.app – validation summary (rev 1, 2026-10-21)

## What the site runs (homepage, desktop)
- Google AdSense auto ads (`adsbygoogle.js`, `data-overlays="bottom"` → anchor ad), 6 `aswift_*` slots auto-placed in `div.google-auto-placed`
- Google Funding Choices (consent / ad-block recovery), cookies `FCCDCF`, `FCNEC`
- GA4 `G-8VK9Y78K0V` via gtag (`_ga*` cookies), stats.g.doubleclick.net
- AdSense SODAR telemetry `ep1/ep2.adtrafficquality.google`
- Cloudflare Web Analytics beacon; Cloudflare Turnstile bot check on deep pages (legit, not blocked)
- No anti-adblock script of its own, no scroll/key hijacking, no custom scrollbars, no fixed overlays besides the site navbar

## Verified (built-in browser, Chromium)
- Cosmetic CSS injected: all 6 ad slots + `google_esf` hidden; page height 5404→1982 px (auto-placed gaps gone); nav, slider, stats tabs, search input intact. Selectors hit only AdSense elements.
- Site first-party JS/CSS (`main.min.js`, `main.css`) checked: no ad-block detection, no interaction hijacking.

## Simulated / assumed
- Network rules: hosts taken from `performance` resource entries; not enforced in Safari yet. **Run the canary**: add `||tibiavip.app/images/banner.jpg^` temporarily, reload – if the "Welcome" banner disappears, custom network rules work in your Safari uBOL; remove it afterwards.
- `www.google.com(.br)/pagead/` path is assumed (common AdSense conversion endpoint).
- Anchor/vignette and Funding Choices markup selectors are standard Google markup, not rendered in the test – labelled unverified.

## Not tested
- Deep pages (/worlds, /characters, /bosses…) and mobile width: Cloudflare Turnstile blocked the test browser (I don't solve CAPTCHAs); Chrome extension wasn't connected. Ads there are almost certainly the same AdSense auto ads (same template), so the same rules apply – please send Safari screenshots of a deep page.

## uBOL can't handle
- Nothing found requiring a userscript. No `.user.js` delivered.

## Install
uBOL → Settings → Custom filters → paste `tibiavip.app.txt` → Apply. Set filtering mode for tibiavip.app to **Optimal** or **Complete**.
