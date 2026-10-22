# Infinity status icons

The final design uses **infinity inside a circle**, with an outline when disabled and a filled circle when enabled. There is no slash. The master `enabled` setting controls both the toolbar and popup blocking indicator; individual site or feature switches do not change this global indicator.

| Surface | Disabled | Enabled |
| --- | --- | --- |
| Safari toolbar and popup | Apple's `infinity.circle` | Apple's `infinity.circle.fill` |
| Safari host window | Circular outline when Safari reports the extension disabled or its status unknown | Filled circular symbol when Safari reports the extension enabled |
| Chrome toolbar and popup | Original outlined infinity-in-circle vector | Original filled infinity-in-circle vector |

The host window reports Safari's extension-enabled status. The popup and toolbar report the extension's master blocking setting. These are separate states: a Safari-enabled extension can have blocking paused.

## Compatibility and rendering

Both exact SF Symbol names were resolved successfully using `NSImage(systemSymbolName:accessibilityDescription:)` on macOS 27.0.1. Apple's local CoreGlyphs `name_availability.plist` assigns both names to release `2020.1`, whose macOS minimum is **11.0**. This is below the project's macOS 14 build target. The extension still requires Safari 26 or later.

Safari toolbar assets are monochrome transparent PNGs at **16, 19, 32 and 38 px**, following [Apple's Safari extension icon requirements](https://developer.apple.com/documentation/safariservices/creating-a-safari-web-extension). Additional 64/128/256 px renders support popup and host status indicators. Safari tints toolbar templates; popup and host images invert in dark appearance. Regenerate with `swift scripts/safari/export_toolbar_icons.swift` on macOS. No private-use Unicode glyph or SF font installation is required at runtime.

The Chrome SVGs in `extension/browsers/chrome/artwork/` are original artwork. PNGs at **16, 32, 48 and 128 px** use dark strokes with light edges for contrast in light and dark themes. Chrome does not load Apple's assets. Regenerate with `node tools/render_chrome_toolbar.cjs` with the optional `sharp` package available; checked-in PNGs keep normal builds dependency-free. Shared branding PNGs also come from this original artwork, so SF Symbols are not used as app icons or logos. See [Apple's SF Symbols HIG](https://developer.apple.com/design/human-interface-guidelines/sf-symbols) and [Chrome's action API](https://developer.chrome.com/docs/extensions/reference/api/action).

The background uses `action.setIcon()` and `action.setTitle()` on background load, install/update, browser startup and relevant local storage changes. Updates are serialized; ruleset errors do not prevent toolbar synchronization, and API errors are caught. Text titles explicitly state whether blocking is enabled. Popup images track the same setting and are decorative alongside the accessible text status.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py` checks PNG dimensions/transparency, resource packaging, both browser variants and lifecycle/error behavior through the real background script with mocked APIs.
- `scripts/safari/test_toolbar.swift` loads the real extension into Apple's public WebKit extension controller in a temporary, nonpersistent context. It checks parse/runtime errors, storage-triggered action titles, distinct stable action images, and popup image sources across repeated toggles. Compile it into a test app bundle before running the visible UI snapshot check. The root folder may be passed as its first argument. It requires macOS 15.4+; this diagnostic requirement does not change the shipped app's minimum OS.
- `tests/browser/chrome-toolbar.cjs` uses Playwright and the installed **Chrome Beta**, a disposable profile and the official DevTools `Extensions.loadUnpacked` command. It verifies successful real `chrome.action.setIcon` calls, action titles, popup switches and saved state after restarting/reloading the unpacked test extension. It captures both states in both appearances and renders the actual PNGs against light/dark backgrounds. Configure `CHROME_BETA_BINARY` if necessary and make Playwright available on `NODE_PATH`.
- Captures are local, under `local/verification/toolbar/`. The Chrome test is headless and does not capture the browser's own toolbar chrome. The WebKit test is not a claim that Safari's enabled-extension state persists after quitting Safari; that separate check remains documented in [Safari status](SAFARI_STATUS.md).

For the maintainer's installed Safari app, run `PYTHONDONTWRITEBYTECODE=1 python3 tools/update_safari_extension.py` after checks. It updates the signed app in Applications and retains a backup. Changes to an extension already loaded by Safari may need a Safari reload/restart to become visible. Do not replace the signed app with the public ad-hoc preview.
