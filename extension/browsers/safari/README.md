# Safari app

The Safari app is a native SwiftUI host app containing one Safari web
extension, so Safari lists Tibia Anti-Ad once. The Xcode project is generated
by [XcodeGen](https://github.com/yonaskolb/XcodeGen) from
[`project.yml`](project.yml). Nothing generated is edited by hand.

| Folder | Target | What it does |
| --- | --- | --- |
| `App/` | Tibia Anti-Ad | The host app's window: whether Safari has the extension on, **Open Safari Settings…**, the GitHub link. |
| `WebExtension/` | Tibia Anti-Ad Extension | The Safari web extension built from `extension/src`: scripts, styles, network rules, the toolbar button and its popup (`popup.html`, `manage.html`), the same as Chrome. |

A native SwiftUI toolbar popover would need a second Safari app extension,
which Safari lists as a separate entry next to the web extension, so the
toolbar popup stays the web extension's `popup.html`.

## Build

- `python3 tools/build_safari_extension.py`: stage resources, generate the
  project, build a universal app and sign it ad-hoc. Requires macOS, Xcode and
  `brew install xcodegen`.
- `python3 tools/build_safari_extension.py --sign-identity "Apple Development"`:
  sign with a local development identity.
- `python3 tools/update_safari_extension.py`: rebuild with the installed app's
  team and replace `/Applications/Tibia Anti-Ad.app`, keeping a backup.
- `python3 tools/package_safari_extension.py`: zip the built app and the
  temporary-extension source with checksums.

Ad-hoc signing provides integrity for development, not a Developer ID or
notarization. This build never creates identities, changes keychains or
changes Safari's security preferences.
