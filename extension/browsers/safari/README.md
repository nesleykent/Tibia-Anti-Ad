# Safari macOS packaging

The Safari app is generated from `extension/src/` with Apple's converter. Do not maintain a duplicate copy of the JavaScript here. The generated Xcode project and build products live in `dist/`.

- `python3 tools/build_safari_extension.py`: generate the project, build a universal macOS app, apply sandbox entitlements and verify the app and embedded extension. Requires macOS and full Xcode.
- `python3 tools/package_safari_extension.py`: package the built app and the temporary-extension source ZIP, with SHA-256 checksum files.
- `scripts/safari/build_and_run.sh --verify`: rebuild, launch and check that the host process stays running.
- `python3 tools/update_safari_extension.py`: update the personally signed app in Applications using an automatically selected valid identity from the installed team; preserve a previous-version backup. See [automatic local updates](../../../docs/SAFARI_STATUS.md#automatic-local-updates-for-claude-and-codex).

The entitlements mirror the converter's sandbox settings: the host uses App Sandbox and outgoing network access; the extension uses App Sandbox. Ad-hoc signing provides integrity for development, not an Apple Developer ID or notarization. It does not remove Safari's unsigned-extension requirement or Gatekeeper's distribution checks.

For a signed public app, configure a Developer ID certificate and notarization or publish through the App Store. This build never creates identities, changes keychains, disables Gatekeeper or changes Safari's security preferences.

For local personal signing, use `python3 tools/build_safari_extension.py --sign-identity 'Apple Development'` with a valid certificate already in your keychain, or choose a free Personal Team on both targets in Xcode. The run script accepts the same identity through `TIBIA_SAFARI_SIGN_IDENTITY`. The default preview build uses ad-hoc signing and regenerates its project; it does not retain personal Xcode settings. See the [personal signing instructions](../../../docs/INSTALL_SAFARI.md#for-your-own-mac-free-xcode-signing).
