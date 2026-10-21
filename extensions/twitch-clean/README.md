# Twitch Clean

Safari Web Extension source supplied in `twitch-clean.zip`, integrated into Anti-Ad Tibia. The supplied files are preserved byte-for-byte except `manifest.json`, which now also loads the Tibia filter; see the [source manifest](../../research/twitch/source-manifest.json).

## Features

- 28 declarative network rules for advertising and telemetry hosts.
- Cosmetic hiding of display ads, directory placements and promotional interfaces.
- Targeted English-language handling of Apple TV, animated-emote and Prime Benefits prompts.
- Source-quality preference on page load and background visibility handling.
- **Tibia filter:** on the Tibia category directory, hides streams of other games (RubinOT and other OTServers, Pokémon servers, idle games). Title/tags naming another server hide a card at once; the extension then reads the right third of each thumbnail with bundled Tesseract OCR (about 2–4 s per stream, two at a time, visible cards first, cached 30 min) to hide OTServer clients the text missed ("Map View" window, Battle Pass) and to restore streams whose `!server` is only a sponsor command next to the official client. Official-marked and unclear streams stay visible.
- The MIT-licensed **vaft** script attempts to replace stitched video advertisements with a clean stream. When no clean stream is available, playback can freeze during the break; an alternate stream can be lower resolution.

The original upstream vaft project was archived in March 2026. Current live-ad effectiveness has not been verified in this integration. The historical [validation report](../../research/twitch/twitch.tv-validation.md) contains earlier test claims; its 186-test suite was not supplied and has not been reproduced here.

## Install in Safari

The supplied manifest targets Safari 26+. This folder contains source, not a signed App Store app.

1. Download/clone this private repository while signed in.
2. In Safari settings, enable the web-developer features and unsigned extensions where available.
3. Choose **Add Temporary Extension…** and select this directory's **`extension`** folder, containing `manifest.json`.
4. Enable Twitch Clean and allow access to Twitch. Reload the live channel page.

Temporary and unsigned installations follow Safari's lifecycle restrictions; they can disappear after quitting Safari or after the temporary-installation limit. For persistent development, use Apple's Safari web-extension tooling to wrap `extension/` in an Xcode app, configure local signing and run it. No signed app or Xcode project is included. Do not delete an existing project to resolve a packaging error.

Alternatively, use the [standalone StopTheMadness Pro script](../../scripts/twitch/README.md). Choose one vaft injection path; remove the Twitch custom script from StopTheMadness when using this extension. This README does not claim the Safari-specific package is verified on Chrome or Firefox.

## Check and undo

On a Twitch live page, `window.twitchAdSolutionsVersion === 24` indicates startup. `localStorage.getItem('video-quality')` should initially contain `{"default":"chunked"}`. These checks do **not** prove that video advertisements were removed. Confirm playback through a real ad break, including audio, captions, quality, chat and reconnect behavior.

Disable/remove Twitch Clean in Safari settings and reload Twitch to remove its hooks. Source quality is a saved preference: choose your previous quality in the Twitch player afterward. Account for any other blocker when comparing behavior.

The main script runs before the player in the page context. Cosmetic filters alone cannot perform this replacement. The standalone script does not classify or hide OTServ streams.

To inspect a Tibia-filter decision, check the `data-twitch-clean-tibia` attribute on a card's grid cell. Rules live in `filters/twitch/tibia-evidence.json`; after editing, run `python3 tools/twitch_evidence.py --write-js`. Tesseract.js 6.0.1 (Apache-2.0, `vendor/tesseract/LICENSE.md`) and its English model are bundled; nothing but the thumbnail is fetched.

## References

- [TwitchAdSolutions / vaft](https://github.com/pixeltris/TwitchAdSolutions) and the MIT notice embedded in `page.js`.
- [Apple: running a Safari web extension](https://developer.apple.com/documentation/safariservices/running-your-safari-web-extension).
- [StopTheMadness Pro custom code](https://underpassapp.com/StopTheMadness/Pro/Docs/CustomElements.html).
