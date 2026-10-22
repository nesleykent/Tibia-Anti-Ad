# Safari macOS packaging

The Safari app is generated from `extension/src/` with Apple's converter. Do not maintain a duplicate copy of the JavaScript here. The generated Xcode project and build products live in `dist/`.

- `python3 tools/build_safari_extension.py`: generate the project, build a universal macOS app, apply sandbox entitlements and verify the app and embedded extension. Requires macOS and full Xcode.
- `python3 tools/package_safari_extension.py`: package the built app and the temporary-extension source ZIP, with SHA-256 checksum files.
- `scripts/safari/build_and_run.sh --verify`: rebuild, launch and check that the host process stays running.

The entitlements mirror the converter's sandbox settings: the host uses App Sandbox and outgoing network access; the extension uses App Sandbox. Ad-hoc signing provides integrity for development, not an Apple Developer ID or notarization. It does not remove Safari's unsigned-extension requirement or Gatekeeper's distribution checks.

For a signed public app, configure a Developer ID certificate and notarization or publish through the App Store. This build never creates identities, changes keychains, disables Gatekeeper or changes Safari's security preferences.
