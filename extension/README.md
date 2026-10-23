# Tibia Anti-Ad

Safari Web Extension source supplied in `twitch-clean.zip`, integrated into Tibia Anti-Ad. The supplied files are preserved byte-for-byte except `manifest.json`, `hide.css`, `page.js` and `rules.json`, which were changed for the Tibia filter and the settings; the [source manifest](../research/twitch/source-manifest.json) records each change and the original hashes. The vaft code inside `page.js` is unchanged.

## Features

- 28 declarative network rules in two rulesets: 17 advertising hosts (`rules.json`) and 11 tracking hosts (`tracking.json`).
- Cosmetic hiding of display ads, directory placements and promotional interfaces.
- Targeted English-language handling of Apple TV, animated-emote and Prime Benefits prompts.
- Source-quality preference on page load and background visibility handling.
- **Tibia filter:** on the Tibia category directory, hides streams of other games (RubinOT and other OTServers, Pokémon servers, idle games). It reads each card's complete title and tags from Twitch's page data (`tibia-props.js`) and passes both fields together to a trained statistical text classifier. Its learned model directly decides whether to hide the card; no manual name list, official-world exception or channel rule decides it. Undecided cards stay visible. The settings popover summarizes what it hides; the Blocked Streams page lists each stream by category with its reason and can show any of them. See [the research notes](../research/twitch/otserver-filtering.md).
- **Settings** for every feature, described below.
- The MIT-licensed **vaft** script attempts to replace stitched video advertisements with a clean stream. When no clean stream is available, playback can freeze during the break; an alternate stream can be lower resolution.

The original upstream vaft project was archived in March 2026. Current live-ad effectiveness has not been verified in this integration. The historical [validation report](../research/twitch/twitch.tv-validation.md) contains earlier test claims; its 186-test suite was not supplied and has not been reproduced here.

## Settings

Open the settings from the toolbar button, or in Safari from **Settings > Extensions > Tibia Anti-Ad > Settings**. Every feature has its own switch, all on by default except **Hide ad-break banner**. The **Tibia Anti-Ad** switch at the top pauses everything at once. Settings are stored locally in the extension; nothing is sent anywhere.

| Section | Switch | Effect | Applies |
| --- | --- | --- | --- |
| Network | Block ad servers | Ruleset `twitch_ads` (`rules.json`) | Immediately, for new requests |
| Network | Block tracking | Ruleset `twitch_tracking` (`tracking.json`) | Immediately, for new requests |
| Video | Remove stream ads | vaft (`page.js` part 2) | After reloading Twitch |
| Video | Source quality | Writes the Source preference on page load (`page.js` part 1) | After reloading Twitch |
| Video | Keep quality in background | Stops Twitch lowering quality in hidden tabs (`page.js` part 3). Included in vaft, so the switch is locked on while **Remove stream ads** is on | After reloading Twitch |
| Video | Hide ad-break banner | Hides the ad label and countdown during a break (selectors from the list, not yet checked against live markup) | Immediately |
| Page | Hide display ads, upsells, prompts, sign-up prompts, cookie banner | The matching `hide.css` group | Immediately |
| Tibia category | Hide other games | The Tibia filter | Immediately |

How it works: `settings.js` defines every option and default. `settings-bridge.js` names the switched-off `hide.css` groups on the page's root element and mirrors the settings into the page's `localStorage` for `page.js`, which must decide before Twitch's player starts and cannot wait for extension storage. `background.js` reapplies the ruleset choice after browser start and extension updates. Clearing Twitch's site data removes that mirror, so one page load then runs with the defaults until the bridge writes it again.

**Rule updates:** the Tibia filter's learned model is downloaded from this repository's `main` branch at browser start and every 6 hours; **Filter rules** in the Tibia category section shows the last update and **Update Now** checks immediately. A download is used only if the bundled classifier accepts its format, finite numeric parameters and revision; code, network rules and fansite fixes still update only with the extension.

**Correcting the Tibia filter:** on the Tibia category, the settings popover shows how many streams are hidden. The current binary model groups them under **Other games**. **Manage Blocked Streams…** opens the Blocked Streams page: the hidden streams grouped by category, each with its title and the reason it was hidden, a search field (Command-F) that filters as you type, and a category pop-up menu. **Show** keeps that broadcast visible until its title changes, so a correction never becomes a permanent channel rule. **Shown by You** on the same page lists the corrections; **Hide** removes one. Turning off **Hide other games** shows every stream immediately.

## Install in Chrome (development)

**[Download the ready-to-use Chrome ZIP](https://github.com/nesleykent/Tibia-Anti-Ad/releases/download/v1.0.0-alpha.2/tibia-anti-ad-chrome.zip)**. For simple instructions, follow [Install Tibia Anti-Ad in Chrome](../docs/INSTALL_CHROME.md). It covers downloading, selecting the correct folder, settings, updates and removal.

Requires Python 3.11+ to build. From the repository root:

```sh
python3 tools/build_chrome_extension.py
```

Open `chrome://extensions`, enable Developer mode, choose **Load unpacked** and select `dist/tibia-anti-ad-chrome`. Review requested Twitch and fansite permissions, then reload affected pages. Rebuild and choose **Reload** in the extension manager after source updates. Remove it through the same manager to uninstall. This is an experimental development package; packaging checks do not certify live Chrome filtering.

## Fansite controls

The extension includes rules and individual switches for all 15 sites in the [inventory](../docs/WEBSITES.md). Network rules are scoped to each site. Unlike the standalone filter subscriptions, the extension includes TibiaWiki BR and Tibiopedia with experimental page repairs; both are enabled by default. Their content-preservation behavior still needs live browser verification. Disable the relevant site switch and reload if content or tools fail.

## Permissions

**Why the extension asks for access to every site (`<all_urls>`): appearance only.** Safari greys an extension's toolbar icon on every page the extension has no access to, so with access limited to Twitch and the fansites the icon turned white on all other pages. The maintainer chose a consistently tinted icon, so the extension requests access to all sites. It uses that access for nothing: content scripts, cosmetic rules and network rule sets still match only Twitch and the 15 fansites, and no other page is read or changed. To keep access minimal instead, remove `"<all_urls>"` from `host_permissions` in [`tools/build_extension_sites.py`](../tools/build_extension_sites.py) (the icon then greys outside those sites), or grant the extension only those sites in Safari Settings → Extensions → Edit Websites. Details: [toolbar icons](../docs/ICONS.md#access-to-all-sites-aesthetic-choice).

## Install in Safari

**[Download the Safari extension ZIP](https://github.com/nesleykent/Tibia-Anti-Ad/releases/download/v1.0.0-alpha.2/tibia-anti-ad-safari-extension.zip)** or the **[compiled Mac app](https://github.com/nesleykent/Tibia-Anti-Ad/releases/download/v1.0.0-alpha.2/tibia-anti-ad-safari-macos.zip)**. Follow the [Safari installation guide](../docs/INSTALL_SAFARI.md).

These are development previews for Safari 26+. The Mac app is built for Apple Silicon and Intel and uses an ad-hoc signature; there is no Developer ID certificate or notarization configured. Safari requires **Allow unsigned extensions**, which resets when Safari quits. The folder-based temporary install ends after 24 hours or when Safari quits.

Build locally with `python3 tools/build_safari_extension.py`, or use `scripts/safari/build_and_run.sh` to build and launch. Generated Xcode files stay in `dist/`; shared extension source remains in `extension/src/`.

Choose one vaft injection method: remove the standalone Twitch custom script from StopTheMadness when using this extension's video-ad replacement.

## Check and undo

On a Twitch live page, `window.twitchAdSolutionsVersion === 24` indicates that vaft started (with **Remove stream ads** on). `localStorage.getItem('video-quality')` should initially contain `{"default":"chunked"}` (with **Source quality** on). These checks do **not** prove that video advertisements were removed. Confirm playback through a real ad break, including audio, captions, quality, chat and reconnect behavior.

Switch off a feature in the settings, or pause everything with the **Tibia Anti-Ad** switch; video features stop after Twitch reloads. Disable/remove Tibia Anti-Ad in Safari settings and reload Twitch to remove its hooks entirely. Source quality is a saved preference: choose your previous quality in the Twitch player afterward. Account for any other blocker when comparing behavior.

The main script runs before the player in the page context. Cosmetic filters alone cannot perform this replacement. The standalone script does not classify or hide OTServ streams.

To inspect a Tibia-filter decision, check the `data-twitch-clean-tibia` attribute on a card's grid cell. Learned weights live in `filters/sources/twitch/tibia-evidence.json`; train and evaluate them as described in the [model card](../docs/TWITCH_MODEL.md). They are generated from labelled data, not edited as a wordlist.

Safari additionally shows the estimated probability of **official Tibia** at the right of every channel-name row in the Tibia directory, with **Hide other games** on or off. The estimate comes from the same joint title/tag model used for hiding. It is a model estimate, not a p-value or a measured accuracy rate. Hover for its meaning; very small/large estimates display as `<0.1%` / `>99.9%` rather than rounding to certainty. The master switch pauses these labels. This presentation is packaged only for Safari in `extension/browsers/safari/web/`; the inference and filtering source remains shared.

## References

- [TwitchAdSolutions / vaft](https://github.com/pixeltris/TwitchAdSolutions) and the MIT notice embedded in `page.js`.
- [Apple: running a Safari web extension](https://developer.apple.com/documentation/safariservices/running-your-safari-web-extension).
- [StopTheMadness Pro custom code](https://underpassapp.com/StopTheMadness/Pro/Docs/CustomElements.html).
