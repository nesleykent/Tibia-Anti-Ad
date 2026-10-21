# Twitch live-video ad script

[`twitch-stopthemadness.js`](twitch-stopthemadness.js) is the supplied standalone alternative to [Twitch Clean](../../extensions/twitch-clean/README.md). It sets Source quality and includes vaft with its MIT notice intact. It tries alternate video streams and strips stitched ad segments; this can reduce resolution or freeze playback during an ad break.

## StopTheMadness Pro

1. Open the website-specific options for `twitch.tv`.
2. Under Custom JavaScript, paste the entire file.
3. Enable **Allow your custom JavaScript to run before DOMContentLoaded**.
4. Reload the Twitch live page. The script must run in the page context before the player starts.

Do not paste JavaScript into uBO Lite's custom-filter field. Filter subscriptions do not install this script. Do not inject a second vaft copy through Twitch Clean or another video-ad blocker.

Check `window.twitchAdSolutionsVersion === 24` and the Source quality setting after reload. Startup is tested locally with mocks; current Safari/live-ad removal is unverified. To undo, remove the custom JavaScript and reload Twitch, then restore your preferred quality in the player.

See [the historical report](../../research/twitch/twitch.tv-validation.md) for original observations and limitations. The source is unchanged from `twitch-clean.zip`; its earlier upstream attribution is preserved, and no independent upstream byte comparison is claimed.

[StopTheMadness Pro documents](https://underpassapp.com/StopTheMadness/Pro/Docs/CustomElements.html) the early-injection option. [TwitchAdSolutions](https://github.com/pixeltris/TwitchAdSolutions) documents vaft's fallback behavior and archived status.
