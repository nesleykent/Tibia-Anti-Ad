# Twitch Clean

Safari Web Extension source supplied in `twitch-clean.zip`, integrated into Anti-Ad Tibia. The extension files are preserved byte-for-byte; see the [source manifest](../../research/twitch/source-manifest.json).

## Features

- 28 declarative network rules for advertising and telemetry hosts.
- Cosmetic hiding of display ads, directory placements and promotional interfaces.
- Targeted English-language handling of Apple TV, animated-emote and Prime Benefits prompts.
- Source-quality preference on page load and background visibility handling.
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

The main script runs before the player in the page context. Cosmetic filters alone cannot perform this replacement. The extension and standalone script do not classify or hide OTServ streams.

## References

- [TwitchAdSolutions / vaft](https://github.com/pixeltris/TwitchAdSolutions) and the MIT notice embedded in `page.js`.
- [Apple: running a Safari web extension](https://developer.apple.com/documentation/safariservices/running-your-safari-web-extension).
- [StopTheMadness Pro custom code](https://underpassapp.com/StopTheMadness/Pro/Docs/CustomElements.html).
