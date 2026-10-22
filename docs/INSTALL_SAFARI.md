# Install Tibia Anti-Ad in Safari

For **Safari 26 or later on a Mac**. These are development previews, not an App Store installation. No Apple Developer distribution certificate is configured for this project yet, so Safari requires **Allow unsigned extensions**. That setting resets when you quit Safari.

## Quickest option: download the extension folder

**[Download for Safari (.zip)](https://github.com/nesleykent/Tibia-Anti-Ad/releases/download/v1.0.0-alpha.2/tibia-anti-ad-safari-extension.zip)**

This option does not need Xcode or a GitHub account.

1. Download the ZIP and double-click it in Finder to extract **`tibia-anti-ad-safari`**. Keep the extracted folder in Documents.
2. Open **Safari → Settings → Advanced** and enable **Show features for web developers**.
3. Open the **Developer** tab in Safari Settings.
4. Click **Add Temporary Extension…**. If Safari asks you to allow unsigned extensions, review and confirm its prompt yourself.
5. Select the extracted **`tibia-anti-ad-safari`** folder, which contains `manifest.json`.
6. In **Settings → Extensions**, enable **Tibia Anti-Ad**, allow access to Twitch and the fansites you use, then reload those pages.

Safari removes temporary extensions **after 24 hours or when you quit Safari**. To use it again, repeat Add Temporary Extension. This is the simplest way to try the current preview without installing an app.

## macOS app download

**[Download the Safari Mac app (.zip, development preview)](https://github.com/nesleykent/Tibia-Anti-Ad/releases/download/v1.0.0-alpha.2/tibia-anti-ad-safari-macos.zip)**

The ZIP contains **Tibia Anti-Ad.app**, with the Safari extension embedded. It is compiled for **Apple Silicon and Intel**, with a macOS 14 minimum build target. Its local ad-hoc signature is not an Apple Developer ID signature, and the app is not notarized. Gatekeeper may block a downloaded copy; the app is not presented as a normally trusted public installer.

1. Extract the ZIP and move **Tibia Anti-Ad.app** to **Applications**.
2. Open the app. It provides a button to open Safari's extension settings.
3. In Safari, enable web developer features as described above, then open **Settings → Developer** and select **Allow unsigned extensions**.
4. Open **Settings → Extensions**, select **Tibia Anti-Ad**, enable it, and allow access to the sites you use.
5. Reload Twitch and fansite tabs. Keep the app in Applications while using its extension.

You may need to enable **Allow unsigned extensions** again after restarting Safari. The containing app keeps the extension files installed, but does not remove this development-mode requirement.

**If macOS blocks the app:** use the temporary-extension ZIP above, or build the app locally with Xcode below. Do not disable Gatekeeper or other system protections. A signed and notarized download requires a configured Apple Developer ID certificate; that is still pending.

## Open the extension's controls

Click Tibia Anti-Ad in Safari's toolbar. If it is not visible, check **Safari → Settings → Extensions** and your toolbar configuration.

The top **Tibia Anti-Ad** switch pauses everything. Other switches control individual Twitch features and fansites. **Hidden on this page → Show** restores a hidden stream. Video-setting changes may need a page reload.

The preview's packaging and native startup have been checked. Live Twitch ad removal and full fansite behavior still require browser verification.

## Update or remove it

- **Temporary folder:** download and extract the new Safari ZIP, remove the old temporary extension in Safari Settings, then add the new folder.
- **Mac app:** quit the host app, replace it with the new app in the same location, reopen it, then check Safari's extension settings and reload affected pages. Keep Safari and the app closed while replacing files.
- **Pause:** turn the extension off in Safari Settings and reload affected pages.
- **Remove:** disable the extension in Safari Settings. Remove its temporary entry or delete the containing app, depending on the method you used, then reload pages.

If Source quality was enabled on Twitch, choose your preferred video quality in the player afterward.

## Optional: build with the Xcode installed on your Mac

Requires full Xcode, its command-line tools, and Python 3.11 or newer. Work from the repository's root folder.

```sh
python3 tools/build_safari_extension.py
```

This generates the Xcode project under **`dist/safari-project/Tibia Anti-Ad/`** and the ready-to-run app at **`dist/Tibia Anti-Ad.app`**. The generated project can be opened in Xcode. The script builds both Mac architectures, verifies resources and applies an ad-hoc development signature. It does not configure a developer account or change Safari's security settings.

To build and open the app in one step:

```sh
./scripts/safari/build_and_run.sh
```

To prepare the downloadable ZIP files and their checksums:

```sh
python3 tools/package_safari_extension.py
```

For distribution without the unsigned-extension setting, configure Apple Developer signing and use App Store distribution or Developer ID signing and notarization. Those credentials are not included in the repository.

## References

- [Apple: running a Safari web extension](https://developer.apple.com/documentation/safariservices/running-your-safari-web-extension) — temporary installation, unsigned-extension settings and their lifetime.
- [Apple: distributing a Safari web extension](https://developer.apple.com/documentation/safariservices/distributing-your-safari-web-extension) — development previews and signed distribution.
- [Release details and checksums](https://github.com/nesleykent/Tibia-Anti-Ad/releases/tag/v1.0.0-alpha.2).
