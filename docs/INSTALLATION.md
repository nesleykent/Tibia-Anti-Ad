# Installation and rollback

**Installing the Tibia Anti-Ad extension in Chrome?** Follow the [Chrome installation tutorial](INSTALL_CHROME.md). The instructions below cover filter lists for an existing blocker.

The repository is public. Copy a generated subscription URL from the [README](../README.md) into a compatible blocker. If your blocker only supports local import, download the selected list and import it through its supported interface. No GitHub account or access token is needed.

All lists are experimental. Use one generated bundle, not both. Review the site's historical report before enabling it. Cosmetic hiding does not prevent tracking requests.

## Firefox with uBlock Origin

Open the dashboard's Filter lists tab, expand Import, paste the portable subscription URL from the README, apply changes and reload. Use the extended bundle instead only if you want the additional parent selectors. This release has not been tested in Firefox with the extension enforcing the rules.

## Chrome with uBlock Origin Lite

Use the installed version's custom-list import facility if available. Otherwise use its supported custom-filter editor; do not assume feature parity with full uBO. Enable the permissions/mode needed for cosmetic filtering (typically Optimal or Complete). Verify both network requests and layout on the actual installed version. No Chrome extension-enforcement test was performed for this release.

## Safari

For the Tibia Anti-Ad extension and compiled Mac app, use the [Safari installation guide](INSTALL_SAFARI.md). The notes below concern third-party blockers importing filter lists.

Use a blocker that accepts the selected list's syntax. uBO Lite and other Safari blockers differ in custom-filter import, conversion and network enforcement. If your version offers a custom-filter editor, paste supported rules there. A raw subscription URL is not a native Safari content-blocker JSON file.

Record Safari, operating-system and blocker versions. Verify cosmetic hiding and network blocking separately with a harmless, site-specific canary image; remove the temporary rule immediately afterward. Consult the historical reports for examples, but confirm the image still exists first. Do not interpret a hidden banner as evidence that analytics requests stopped.

## Acceptance after installation

Test the homepage and a deep page at desktop and mobile widths, then delayed loading, scrolling and SPA navigation. Check search, calculators, maps, forms, sign-in, comments, keyboard navigation and focus. Check for blank spaces, scroll locks, redirects and autoplay. Inspect actual blocked requests with the blocker's logger or browser network tools, using a clean baseline with cache disabled. Retest with your usual lists enabled to detect interactions.

Tibiopedia and TibiaWiki BR are deliberately excluded from generated bundles: supplied research describes inline anti-adblock code capable of removing content. Do not install their raw lists casually. Their companion scripts require further timing and compatibility review.

## Rollback

Unsubscribe from the Tibia Anti-Ad list or remove the pasted rules, disable any separately installed companion script, and reload the page. Restore the previous filtering mode if changed. If a failure persists with Tibia Anti-Ad disabled, record that in the issue. Never disable all privacy protection as a permanent workaround.
