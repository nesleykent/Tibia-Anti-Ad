# tibiopedia.pl validation (rev 1, 2026-10-21)

## Verified (built-in Chromium pane)
- Recon on /news and /monsters/Cockroach, at desktop and 375px width. The site has only the fixed "library" layout (min-width 1000px), so the mobile width shows the same slots. Recorded: the hosts, the slot wrappers (.com_leaderboard, .com_medium_box, .ad_panel_right "Reklama", the ±295px side rails, publift sticky footer) and the Vidoomy floater (z-index 2147483647).
- Ad-Shield: decoded the inline loaders without running them, by stubbing Function. Once html-load.com and its mirrors are blocked, they run `setInterval(()=>document.body.remove(),100)`, show a full-screen report.error-report.com iframe, then a confirm()/redirect.
- Same-origin sandboxed iframe harness with the list's hosts blocked:
  - control without the userscript: body wiped within 1 s;
  - with the userscript: body intact after 25 s;
  - external tag stripped + flag only: wiped; with `as_loader_version`: intact.
- Malvertising: a live ad redirected the top page to securesweep.pro (fake McAfee).

## Simulated / not verified
- Cosmetic rules were written from observed markup but were **not** injected and screenshotted (the usage limit was hit).
- The userscript's MutationObserver does not fire before script execution in the document.write harness. The protection that was proven comes from the `as_*` self-ref flag and `as_loader_version`.
- /news run of the harness was not completed.

## Assumed
- Network rules and the `@@` allow rule work in Safari uBOL custom filters. Run the canary test: `||tibiopedia.pl/images/static/general/social_instagram.jpg^`.
- Mobile nag selector (LAYOUT=='mobile') is unverified.

## uBOL cannot handle
- Ad-Shield's inline body wipe: this needs tibiopedia.pl.user.js. **Without the userscript, the list blanks the site.**
- `body.hasStickyBottomAd #footer{margin-bottom:90px}` (only if fuse.js still runs, so not an issue when it is blocked).
- The Facebook like-box panel stays empty, because connect.facebook.net is blocked on purpose.
