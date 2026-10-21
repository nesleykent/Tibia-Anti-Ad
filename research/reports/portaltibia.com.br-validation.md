# portaltibia.com.br validation (rev 1, 2026-10-21)

Tested in **Chrome Beta**, launched with a throwaway profile and a DevTools port.

## Site stack (WordPress, CrystalSkull theme + WPBakery)
- **PremiumAds wrapper**, the same network as the forum: GPT, Prebid and Amazon APS. Engine formats: Seedtag, Teads, Taboola, Membrana, k-words, MGID.
- **Navegg DMP** and the partners it syncs to (Adobe everesttech, Salesforce Krux, Oracle BlueKai, Acuity, smartclip, Taboola, Lotame, Smart), plus the forum's ID-sync set.
- **Analytics:** Facebook Pixel and like-box, GA4 (4 property IDs), Jetpack stats (`stats.wp.com`, `pixel.wp.com`), Yandex Metrica, Cloudflare Web Analytics.
- **Disqus** comments, which pull in **VigLink**, an affiliate rewriter for outbound links.
- **Dormant TibiaBR Revive layer pop-up** (`banners.tibiabr.com/www/delivery/al.php`). It is `document.write`'d only on the bare root URL, which now redirects to `/pt/home/`.
- **Visible units:**
  - "Patrocínio" leaderboard on the homepage;
  - "Patrocínio" 300x250 sidebar box on all pages;
  - sticky bottom anchor (80 px);
  - FansitesBR fixed icon bar.
- **No anti-adblock.**

## Forced redirect (interaction hijack)
- **Observed twice with ads allowed and no clicks:** about 23 s after load, the tab navigated to `tibiaring.com/char.php?…`, then to `tibiaring.com`. The navigation initiator was "other", with no script stack.
- **Not from the site itself:** neither PortalTibia's HTML (fetched from a script-free same-origin page) nor its scripts reference tibiaring.
- **Not tibiaring's frame-buster:** a synthetic tibiaring iframe did **not** bust out, because Chrome blocks cross-origin frame-busting without a user gesture.
- **Conclusion:** most likely an ad creative in a same-origin GPT iframe setting `top.location`.
- **Not reproduced** in 3×90 s later runs, so it is a rotating creative.
- **Fix:** the ad-stack network rules. With them, zero ad frames load.

## Verified (CDP `Network.setBlockedURLs` with the list's hosts + list CSS without `:has()`)
| Page | Width | Network + CSS | CSS only |
|---|---|---|---|
| Home | 1280 | no ads, no fixed units, no "Patrocínio" label; 10 requests attempted, all blocked | same |
| Article | 1280 | same; 14 requests attempted, all blocked | same |
| Article | ~500 | same | same |
| Home | ~500 | same | same |

- **Still works:** news grid, carousel, ticker, tabs, YouTube, Disqus, the "Parceiros" partner banners and the CipSoft "Promoted Fansite" badge.
- **No body margin** left by the anchor.

## Leftovers with plain CSS only (`:has()` backups cover them if uBOL applies them)
- **Sponsor widget:** an empty bordered shell, about 42 px. The ad and its heading are hidden, but the `.widget` wrapper has no unique class; its index differs per page.
- **Facebook like-box widget:** the iframe is hidden, but the "Curta a nossa página!" title and its box remain, about 101 px.
- Neither can be selected without a parent selector. `.widget:has(…)` backups are in the list. Whether uBOL in Safari applies `:has()` is unverified.

## Assumed / unverified
- Whether Safari applies uBOL custom network rules: still open; run the guildstats canary test.
- `.pp-sticky-this*`, MGID and Seedtag cosmetics were not rendered in testing.
- The dormant `banners.tibiabr.com` layer was never seen live, so its markup is unknown; it is blocked by host only.
- "Mobile" means ~500 px, the narrowest Chrome window allowed.

## Judgment calls
- **FansitesBR bar:** hidden; delete its 2 lines to keep it.
- **Facebook like-box:** blocked as a social tracker.
- **Disqus:** kept (comments). **VigLink:** blocked (affiliate link hijack).
