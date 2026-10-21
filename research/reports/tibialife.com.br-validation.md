# tibialife.com.br validation (rev 1, 2026-10-21)

Tested in the built-in browser pane (Chromium) at 1024 px (desktop) and 375 px (mobile), on the homepage and an article page (`/orcsoberfest-14/`). Each page was rechecked after 6 s.

## Site stack (WordPress + Elementor 4.3.5, Roxeen theme)
- **Tracking:** gtag.js `GT-5TGJ8HW` sends to GA4 `G-4J2SDPCGHW`, plus the Google Signals `www.google.com.br/ads/ga-audiences` remarketing beacon. Cookies: `_ga`, `_ga_*`. `localStorage` was empty.
- **Ad networks, ID-sync, consent banner, newsletter or app pop-ups, surveys, chat widgets:** none of these exist. No inline ad, tracking or blocking code, and no iframes.
- **Self-hosted sponsor units:** a "Parceiros" block on the homepage sidebar, holding an ExitLag 336×280 coupon banner (bit.ly) and a danielhatano.com.br banner (860×774 on desktop). An ExitLag affiliate link also sits in the main menu.
- **Anti-adblock:** none (no bait, no probes, no wall).
- **Interaction hijack:** `smooth-scroll.min.js`, which is SmoothScroll for websites v1.5.1. It adds wheel and keydown listeners with `preventDefault` and turns itself on for **desktop Chrome and Safari**. It sits in its own file, so a network rule blocks it.
- **Kept:** the sticky site header, the article reading-progress bar, the Instagram feed (first-party images), gravatar and the comment form.

## Verified
- **Cosmetic rules:** I injected them in-page at 375 px. All 5 targets compute to `display:none`, and the sidebar column now ends at its spacer with no leftover gap (screenshot). At 1024 px the same widget ids exist, so the same rules apply.
- **Article pages:** they carry no sponsor units. The only match is the hidden menu item.
- **Search, navigation and the post sliders:** unaffected, because the rules touch no shared classes.

## Simulated / assumed
- **Network rules:** I verified the host list against `performance` entries. I did not enforce the rules in the pane.
- **Safari custom network rules:** whether they apply is still unproven. Canary test: the list blocks `smooth-scroll.min.js`, so on desktop Safari a mouse wheel scroll should feel native (no eased glide). If it still glides, uBOL on Safari is ignoring custom network rules.
- **Elementor widget ids** (`f472b1d`, `f1eac4f`, `21fb053`): they are stable unless the editor deletes and re-creates the widget. The `a[href]` fallbacks cover the banner image and caption only, not the heading.

## uBOL cannot fix
- **`html { scroll-behavior: smooth }` from the theme CSS.** It only affects anchor jumps and is mixed into the essential `style.css`, so I left it.
- **The GA beacons, if Safari ignores custom network rules.** Nothing can be hidden to stop them.
- **No userscript needed.**

## Install
1. In uBOL, open Settings, then **Custom filters**, and paste `tibialife.com.br.txt`.
2. Set the filtering mode for tibialife.com.br to **Optimal** or **Complete**. Cosmetic rules need it.
