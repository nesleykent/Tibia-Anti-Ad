# Tibia Anti-Ad

Safari Web Extension source supplied in `twitch-clean.zip`, integrated into Tibia Anti-Ad. The supplied files are preserved byte-for-byte except `manifest.json`, `hide.css`, `page.js` and `rules.json`, which were changed for the Tibia filter and the settings; the [source manifest](../research/twitch/source-manifest.json) records each change and the original hashes. The vaft code inside `page.js` is unchanged.

## Features

- 28 declarative network rules in two rulesets: 17 advertising hosts (`rules.json`) and 11 tracking hosts (`tracking.json`).
- Cosmetic hiding of display ads, directory placements and promotional interfaces.
- Targeted English-language handling of Apple TV, animated-emote and Prime Benefits prompts.
- Source-quality preference on page load and background visibility handling.
- **Tibia filter:** on the Tibia category directory, hides streams of other games (RubinOT and other OTServers, Pokémon servers, idle games). It reads each card's complete title and tags from Twitch's page data (`tibia-props.js`) and hides a card when a server is declared in the title or tags without an official world or "Tibia Global"; a `!server` chat command in the title names the server like plain text. Undecided cards stay visible. The settings page lists the streams hidden on the current page with their reasons and can show any of them. See [the research notes](../research/twitch/otserver-filtering.md).
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

**Correcting the Tibia filter:** on the Tibia category, the settings page lists the streams hidden on the current page with the reason for each. **Show** keeps that broadcast visible until its title changes, so a correction never becomes a permanent channel rule. **Shown by you** lists the corrections; **Hide** removes one. Turning off **Hide other games** shows every stream immediately.

## Install in Chrome (development)

Requires Python 3.11+ to build. From the repository root:

```sh
python3 tools/build_chrome_extension.py
```

Open `chrome://extensions`, enable Developer mode, choose **Load unpacked** and select `dist/tibia-anti-ad-chrome`. Review requested Twitch and fansite permissions, then reload affected pages. Rebuild and choose **Reload** in the extension manager after source updates. Remove it through the same manager to uninstall. This is an experimental development package; packaging checks do not certify live Chrome filtering.

## Fansite controls

The extension includes rules and individual switches for all 15 sites in the [inventory](../docs/WEBSITES.md). Network rules are scoped to each site. Unlike the standalone filter subscriptions, the extension includes TibiaWiki BR and Tibiopedia with experimental page repairs; both are enabled by default. Their content-preservation behavior still needs live browser verification. Disable the relevant site switch and reload if content or tools fail.

## Install in Safari

The supplied manifest targets Safari 26+. This folder contains source, not a signed App Store app.

1. Clone or download [the public repository](https://github.com/nesleykent/Tibia-Anti-Ad).
2. In Safari settings, enable the web-developer features and unsigned extensions where available.
3. Choose **Add Temporary Extension…** and select this directory's **`src`** folder, containing `manifest.json`.
4. Enable Tibia Anti-Ad and allow access to Twitch. Reload the live channel page.
5. Open the settings from the Tibia Anti-Ad toolbar button to choose features.

Temporary and unsigned installations follow Safari's lifecycle restrictions; they can disappear after quitting Safari or after the temporary-installation limit. For persistent development, use Apple's Safari web-extension tooling to wrap `extension/` in an Xcode app, configure local signing and run it. No signed app or Xcode project is included. Do not delete an existing project to resolve a packaging error.

Alternatively, use the [standalone StopTheMadness Pro script](../scripts/twitch/README.md). Choose one vaft injection path; remove the Twitch custom script from StopTheMadness when using this extension. This README does not claim the Safari-specific package is verified on Chrome or Firefox.

## Check and undo

On a Twitch live page, `window.twitchAdSolutionsVersion === 24` indicates that vaft started (with **Remove stream ads** on). `localStorage.getItem('video-quality')` should initially contain `{"default":"chunked"}` (with **Source quality** on). These checks do **not** prove that video advertisements were removed. Confirm playback through a real ad break, including audio, captions, quality, chat and reconnect behavior.

Switch off a feature in the settings, or pause everything with the **Tibia Anti-Ad** switch; video features stop after Twitch reloads. Disable/remove Tibia Anti-Ad in Safari settings and reload Twitch to remove its hooks entirely. Source quality is a saved preference: choose your previous quality in the Twitch player afterward. Account for any other blocker when comparing behavior.

The main script runs before the player in the page context. Cosmetic filters alone cannot perform this replacement. The standalone script does not classify or hide OTServ streams.

To inspect a Tibia-filter decision, check the `data-twitch-clean-tibia` attribute on a card's grid cell. Rules live in `filters/sources/twitch/tibia-evidence.json`; after editing, run `python3 tools/twitch_evidence.py --write-js`.

## References

- [TwitchAdSolutions / vaft](https://github.com/pixeltris/TwitchAdSolutions) and the MIT notice embedded in `page.js`.
- [Apple: running a Safari web extension](https://developer.apple.com/documentation/safariservices/running-your-safari-web-extension).
- [StopTheMadness Pro custom code](https://underpassapp.com/StopTheMadness/Pro/Docs/CustomElements.html).
