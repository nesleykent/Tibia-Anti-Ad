# twitch.tv uBOL list: validation summary (revision 1, 2026-10-21)

## Status

This session could not load Twitch at all. The environment's network policy refuses every Twitch host (`www.twitch.tv`, `m.twitch.tv`, `gql.twitch.tv`, `static.twitchcdn.net`, `assets.twitch.tv`, `spade.twitch.tv`), and the server-side fetcher could not resolve them either. No in-page recon happened: no resource list, scripts, cookies, localStorage, bundle search, or screenshots of the real site. Every rule therefore comes from current, maintained third-party evidence, cited per rule in `twitch.tv.txt`:

- uBlock filters (uAssets HEAD 2026-10-21)
- EasyList and EasyPrivacy
- AdGuard Base, Tracking and Annoyances lists
- hagezi DNS lists
- FrankerFaceZ (2026-10-20) and BetterTTV (2026-10-15), which are patched continuously against live Twitch
- TwitchDropsMiner (2026-10-09)
- TwitchAdSolutions (archived 2026-03)

The uBOL behavior described below comes from uBOL's own source (gorhill/uBlock `platform/mv3`, commit 1e6f82b, 2026-10-20) and WebKit's DNR translator (`_WKWebExtensionDeclarativeNetRequestRule.mm`, main).

## What Twitch runs (from that evidence)

- **Video ads** are stitched server-side into the HLS playlists (`usher.ttvnw.net`, `*.ttvnw.net/v1/playlist`). They are marked with `stitched` / `twitch-maf-ad` / `twitch-ad-quartile` DATERANGE tags, and the ad segments come from the same video CDN as the stream.
- **During midrolls** Twitch may start a "picture-by-picture" player that keeps the stream visible in a small window while the ad plays.
- **Display ads** use Amazon Publisher Services (`apstag.js` and aax bids on `amazon-adsystem.com`). Stream Display Ads (lower-third and L-shaped frames) play `<video>` creatives from `m.media-amazon.com`.
- **Twitch's own ad server edge** is `edge.ads.twitch.tv`. Historically Twitch also used Google Ad Manager/IMA and Flashtalking.
- **Telemetry:** Spade events, plus `client-event-reporter`, `trowel` and `analytics.m7g` reporters. The Spade endpoint is read at runtime from `spade_url` in the channel HTML or `/config/settings.<hash>.js`, so `spade.twitch.tv` may not be the only host in use. Some telemetry also travels through `gql.twitch.tv` (the `sendSpadeEvents` mutation).
- **Drops** progress now follows video segment fetches, not Spade. TwitchDropsMiner switched to playlist HEAD requests on 2026-10-09. Blocking Spade should therefore not stop Drops (assumption based on that change).
- **Anti-adblock:** a player overlay linking to `/how-to-allow-ads-browser` and Turbo.
- **Upsells:** Turbo "Go Ad-Free" nav icon, Prime Gaming crown and promo bar, Amazon Luna link, Subtember banner.
- **Logged-out nags:** sticky sign-up footer, chat sign-up gate, follow prompt. There is also a consent banner on desktop and `m.twitch.tv`.

## Verified (by reading and running uBOL/WebKit source, not in Safari)

- **Network lines are dropped by Custom filters on Safari.** The Safari build sets `supportsOffscreenDocument = false` ("no workaround"), so the filter compiler never runs and the filter sandbox is hidden (`display:none`). The Custom filters "Import" box keeps only `host##selector` lines. Running the importer's own code on this list dropped all 26 network lines and kept all 18 cosmetic ones. This explains the earlier tibiawiki network rule that "seemed not to apply".
- **Network rules work through Develop > Custom DNR rules, which is available on Safari.** Pasting uBO syntax there runs `parseFilters()` and stores dynamic DNR rules. The full paste, YAML conversion, save and Safari-shim path turns this list into **3 DNR rules** with no errors, and nothing in them that Safari's shim drops or WebKit's validator rejects. WebKit expands them to about 26 content-blocker rules.
  - The rules only apply while Developer mode stays on.
  - They are added in one call, so one Safari-invalid rule would void them all. This list avoids every type WebKit lacks (for example `csp_report`, `object`).
- **`$domain=twitch.tv` conversion path:** `initiatorDomains` → Safari shim `domains` → WebKit `if-domain *twitch.tv`. This is verified in source; whether it actually fires is for the canary to show.
- **`:has()` and `:is()` stay plain CSS.** The importer runs with `nativeCssHas: true`, so they are injected through `insertCSS`, not the procedural engine. All 18 selectors were stored as plain.
- **All selectors for a host become one `a,b,c{display:none!important}` rule.** One unparseable selector voids the entire list.
- **Sub-frames are not reliably covered on Safari.** uBOL skips sub-frame `insertCSS` on Safari (WebKit bug 262491), so embedded Twitch players on other sites get no cosmetic rules.

## Simulated (Chromium 1194 headless, 1280 px and 375 px)

These tests check selector logic and CSS integrity only. They say nothing about whether Twitch's live DOM matches.

- The exact stylesheet uBOL would inject parses as 1 rule with 18 selectors. With one deliberately bad selector added, the rule count drops to 0.
- On a fixture built from the cited markup, all 18 targets hide at both widths. These neighbors stay visible:
  - the mature-content gate and the "Commercial break in progress" screen
  - the ad label and countdown, and the volume button
  - Browse, notifications and the avatar
  - Prime's Claim button
  - the stream-info sibling of the SDA video, the chat body and a normal directory card

## Assumed (needs your Safari check)

- **Live DOM:** every cosmetic selector matches today's Twitch DOM. The most current sources are BTTV (Turbo icon path) and FFZ (Prime, Luna, Subtember). The weakest are `.follow-prompt` and `.promoted-card-stat__promotion`.
- **Anti-adblock overlay:** the stream keeps playing under it, so hiding it is enough. uBO and AdGuard both hide it, which suggests it does.
- **Network rules in practice:** they actually fire in your Safari version. The canary below settles this.
- **Language:** the two `aria-label` rules match the English UI only.

## What uBOL cannot fix (and why)

- **Stitched video ads (pre-, mid- and post-rolls).** They arrive inside the same playlist and segments as the stream. Removing them needs response rewriting (uBO's `replace=`, Firefox only) or a scriptlet (`twitch-videoad`/vaft). Both are unavailable: uBOL custom filters on Safari have no scriptlets or user scripts, and no response modification. Blocking `usher`/`ttvnw` would kill the stream itself.
- **Player squeeze during Stream Display Ads.** EasyList restores the player with `height:100%` via a style rule. Plain hide rules can't do that, so a shrunken player with empty space can remain while an SDA runs.
- **Telemetry through `gql.twitch.tv`.** DNR cannot match request bodies, and blocking the host breaks the site. If Twitch moved `spade_url` to a new host, that host is not covered until someone identifies it in Web Inspector.
- **`m.twitch.tv` "open in app" banner.** EasyList fixes it with a sessionStorage scriptlet. AdGuard's CSS rule is too broad to be safe, because it can hide the page body. If Twitch uses Apple's Smart App Banner meta tag, Safari draws that banner as browser chrome, which no content blocker can hide.
- **Homepage autoplay, chat upsell "nudges" (gift bundles, Partner Plus, clip nudges) and toast notifications.**
  - Autoplay needs a script.
  - The nudges are React chat items with no stable DOM hook in any source.
  - Hiding the toast container would also remove legitimate notices such as Drops and errors.
- **Forcing maximum video quality.** The player keeps its choice in localStorage `video-quality` (`{"default":"chunked"}` = Source) [vaft], and drops quality while `document.hidden` is true, which FFZ counters by redefining `document.hidden` [FFZ]. Both need a script; DNR can't help either, because variant playlist URLs are opaque tokens that don't name the quality. Workaround outside the list: pick Source once in the player's Quality menu; Twitch saves it in that key and reuses it. The background-tab drop remains.
- **Cookie consent.** It can be hidden but not answered. EasyList's `tachyon-accepted-cookie-notice` cookie needs a scriptlet.

## Field report on revision 1 (Safari, macOS, logged out)

Five items still showed. None of them is covered by any public filter list or by a DOM hook in FFZ or BTTV:

- **Category page display banner** ("ESQUENTA DE OFERTAS"): carries an AdChoices-style marker.
- **Black "Learn More" tile in the directory grid:** an ad slot whose creative did not render.
- **"Prime Benefits" dropdown over the player.**
- **Apple TV "Sub for 1 Month" card at the top of chat:** FFZ identifies it as community highlight `mw-drop-available`, which shares its container with hype trains and polls.
- **"Animated Emotes can be disabled" chat callout:** FFZ identifies it as callout `TurnOffAnimatedEmotes`.

FFZ hides the last two through React internals, which plain CSS cannot do. 7TV confirms the `community-highlight-stack` class prefix, but hiding that whole stack would also remove hype trains, polls and predictions.

A Settings screenshot confirms the default filtering mode is Complete and Developer mode is on, so the mode and Develop-pane prerequisites are met. Whether the list itself is loaded (3 DNR rules, 18 twitch.tv selectors) is still unconfirmed.

A second report showed full-size in-player video ads (Volkswagen, Samsung) under the "is taking an ad break" banner. This is the stitched-ad limitation listed below; no uBOL rule can remove it. Twitch's player fetches playlists and segments from a worker, so those requests appear only in Web Inspector's Network tab, not in `twitch-recon.js` output. Rules for all five wait on DOM data from `twitch-recon.js` run in Safari. That output also reports whether the network rules are live (`listedHostsThatLoaded`) and whether the cosmetic rules are live (`cosmeticRulesActive`).

## Revision 2: first Safari data (Safari 27.0.1, `/directory/category/tibia`, logged out)

`twitch-recon.js` output from the maintainer's Safari established the following.

**Verified in Safari:**
- **Cosmetic rules are live.** The probe element was hidden, the "Leave feedback for this Ad" button measured 0x0, and the `upsell-bottom-banner` image measured 0x0, consistent with the sticky-footer rule.
- **The directory ad markup is real and was captured:**
  - Banner: `div#directory-banner[data-a-target="directory-banner-ad-slot"][aria-label="Advertisement"]`, holding a 728x90 iframe titled "Display Ad" from `d3qpnbd0lnus53.cloudfront.net/vast/sf-5.html`.
  - "Learn More" tile: `div#directory-rectangle`, an id used on two nested elements, holding an `m.media-amazon.com` .mp4.
  - Revision 2 hides all three hooks.
- **Hosts observed and now listed:** `sb.scorecardresearch.com`, `api.ono.us-east-1.prod.mt.paets.advertising.amazon.dev`, `d3qpnbd0lnus53.cloudfront.net`. Also seen: `s.amazon-adsystem.com` (iu3/iui3 ID sync), `aes.us-east.3px.axp.amazon-adsystem.com`, `m.media-amazon.com` video, `edge.ads.twitch.tv`.
- **Network rules were not in effect.** Hosts covered by both rule forms loaded, including `edge.ads.twitch.tv`, which the plain global rule covers. The likely cause is that the rules are not saved in Develop > Custom DNR rules; not yet confirmed. `twitch-recon.js` v2 adds a direct probe (two `no-cors` requests) that reports `blocked` or `loaded` per rule form; a Chromium test with one host aborted and one served returned `blocked`/`loaded` correctly.

**Simulated (Chromium, fixture rebuilt from the captured markup):**
- 21 selectors, 1 rule. A bad selector still voids all of them.
- Both ad slots hide, and the category header, tabs and stream cards stay.
- The grid reflows with no gap: 0 px between the card before and after the hidden tile at 375 px; the next card moves up into the same row at 1280 px.

**Still pending:** the Apple TV card, the "Animated Emotes" callout and "Prime Benefits" need the same output from a channel page.

**Reported:** after the revision 2 steps (3 cosmetic lines added, network block saved in Develop > Custom DNR rules), the maintainer reported "it worked". The probe's per-form results were not shared.

## Outside uBOL: StopTheMadness Pro (stitched ads and quality)

The maintainer already runs StopTheMadness Pro. Its documented features include blocking the Page Visibility API and website-specific JavaScript, which can run "as soon as possible" when "Allow your custom JavaScript to run before DOMContentLoaded" is enabled. Whether that JavaScript runs in the page's own context (needed for the ad part) is not documented for Pro. The non-Pro docs describe an injected `<script>` element, which would run in the page context.

`twitch-stopthemadness.js` contains:
- **Part 1, Source quality:** sets localStorage `video-quality` to `{"default":"chunked"}` before the player starts.
- **Part 2, vaft:** the unmodified TwitchAdSolutions script (MIT), commit c51ef2fe, the final one before archiving.
  - It hooks `window.Worker` and fetch to swap or strip stitched ad segments.
  - It forces `document.hidden=false` and `visibilityState=visible`, which also stops the background-tab quality drop.

Audit of the vaft source:
- Network calls go only to Twitch.
- `eval` runs Twitch's own worker code inside the wrapper.
- The Authorization header is sent only to `gql.twitch.tv`.

Smoke test (Chromium, injected at document start on a stand-in twitch.tv page): no page errors, `video-quality` set, `twitchAdSolutionsVersion` 24, Worker hooked, page reported visible. This does not show that vaft still beats Twitch's current ads; that needs Safari.

## Safari checks, in order

1. **Canary.** Paste line A from the CANARY block alone into Develop > Custom DNR rules, Save, and open `twitch.tv/directory`. If the box art disappears, plain network rules work. Delete A and repeat with B. If B fails while A works, remove `$domain=twitch.tv` from sections 1b and 1c.
2. **Rule counts.** After pasting the full list, Develop should show "Number of registered rules: 3". Custom filters should list `twitch.tv` with 18 selectors.
3. **Screenshots to send back:**
   - a channel page during an ad break, desktop and narrow window
   - the homepage
   - `/directory`
   - any surviving pop-up, with Web Inspector open on the element and 3 to 4 ancestors

## Safari extension: Twitch Clean (`twitch-clean/`)

The same rules packaged as a Safari Web Extension (MV3). It also adds page-context Source quality plus vaft and a script for three text-anchored nags.

- **`rules.json`:** 28 static DNR rules, one per host (`urlFilter "||host^"`), generated from this list.
  - The `domains: ["twitch.tv"]` scoping is the form uBOL's Safari build uses.
  - A WebKit-translation emulator shows 0 mismatches across 20 cases, covering look-alike hosts, ports and essential hosts.
- **`hide.css`:** one rule per selector, injected as a user-origin stylesheet (`css_origin: user`, supported in WebKit).
- **`page.js`:** runs in the MAIN world at `document_start`; WebKit supports both. Part 1 sets Source quality, part 2 is vaft.
- **`nags.js`:** hides a nag only when its text and a structural anchor both match; text inside chat messages is never considered.

**Verification, in two rounds** (independent auditors, then skeptics who tried to refute each finding):
- WebKit source audit: no blockers.
- Chromium functional suite: 186/186 on the final build, with no manifest errors.
- nags regression tests all pass:
  - card and callout reuse, a callout drawn inside the chat list, reattached nodes, chat quotes;
  - no node retention with animation frames paused;
  - about 30 ms of extra script time per 5 s under heavy chat.
- The README's install steps were checked against Apple's docs.

**Still unverified in Safari:** real-world behavior of vaft against Twitch's current ads, where Twitch actually renders the three nags, and the exact permission UI for an extension that has no popup.
