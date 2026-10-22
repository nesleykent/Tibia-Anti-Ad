# Install Tibia Anti-Ad in Safari

For **Safari 26 or later on a Mac**. The public downloads below use an ad-hoc development signature and require **Allow unsigned extensions**. For your own Mac, you can instead configure a free **Personal Team / Apple Development** certificate in Xcode. Public distribution signing and personal development signing are different workflows.

## For your own Mac: free Xcode signing

**Maintainer's current installation:** the Mac app in Applications was personally signed on 2026-10-22. It is not an Add Temporary Extension installation. See the [signing status and verification record](SAFARI_STATUS.md) before repeating setup or replacing that app.

You do not need to buy Apple Developer Program membership just to set up a Personal Team for local development. Xcode can create a free **Apple Development** certificate associated with your Apple Account. This is not a Developer ID certificate for public downloads.

1. Open **Xcode → Settings → Accounts** (called **Apple Accounts** in some versions).
2. Add your Apple Account and select your **Personal Team**.
3. Open **Manage Certificates…**, click **+**, and choose **Apple Development**. Complete any account or keychain prompts yourself.
4. Open the generated project at **`dist/safari-project/Tibia Anti-Ad/Tibia Anti-Ad.xcodeproj`** in Xcode. If it does not exist yet, run the optional build command near the end of this guide once to generate it.
5. In the project editor, select **Tibia Anti-Ad** under **Targets**. Open **Signing & Capabilities**, enable **Automatically manage signing**, and choose your **Personal Team**. Repeat for **Tibia Anti-Ad Extension**. Both targets need your development identity.
6. Select the **Tibia Anti-Ad** scheme and **My Mac**, then choose **Product → Run**.
7. Enable the newly signed extension in Safari Settings. Remove the earlier temporary installation to avoid confusing it with this copy.

Use **Xcode's Run command** for this personal signing route. The repository's default command-line build uses ad-hoc signing for public previews and CI; rerunning it does not preserve a Personal Team selection in its regenerated project. To build with an existing valid development certificate from the command line instead:

```sh
python3 tools/build_safari_extension.py --sign-identity 'Apple Development'
```

If you have more than one matching certificate, use the exact certificate name or SHA-1 from `security find-identity -v -p codesigning`. To use the build-and-run script with personal signing, set `TIBIA_SAFARI_SIGN_IDENTITY` to that identity. Both the app and its embedded extension are signed and verified; the certificate and private key stay in your Mac's keychain.

**Certificate listed in Xcode but not valid for signing?** A missing Apple WWDR G3 intermediate certificate can cause this. Follow [Apple's instructions for restoring a missing intermediate certificate](https://help.apple.com/xcode/mac/current/en.lproj/devc4c7101d8.html). Do not change the certificate's trust setting to Always Trust.

After signing, test that Safari accepts the extension with **Allow unsigned extensions turned off**, then quit and reopen Safari to check persistence. Native signature verification alone does not establish that Safari has accepted and retained the extension.

See [Apple's Personal Team signing workflow](https://help.apple.com/xcode/mac/current/en.lproj/dev60b6fbbc7.html) and [certificate management](https://help.apple.com/xcode/mac/current/en.lproj/dev154b28f09.html). The paid Developer ID route is needed for a normally trusted, publicly distributed download, not this local Personal Team setup.

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

**If macOS blocks the app:** use the temporary-extension ZIP above, or build the app locally with Xcode below. Do not disable Gatekeeper or other system protections. A publicly distributed signed and notarized download requires a configured Apple Developer ID certificate; that is still pending. For your own Mac, use the free Personal Team route above.

## Open the extension's controls

Click Tibia Anti-Ad in Safari's toolbar. If it is not visible, check **Safari → Settings → Extensions** and your toolbar configuration.

The top **Tibia Anti-Ad** switch pauses everything. Other switches control individual Twitch features and fansites. Open **Tibia category → Manage Blocked Streams…**, then use **Show** to restore a hidden stream. Video-setting changes may need a page reload.

The preview's packaging and native startup have been checked. Live Twitch ad removal and full fansite behavior still require browser verification.

## Update or remove it

- **Temporary folder:** download and extract the new Safari ZIP, remove the old temporary extension in Safari Settings, then add the new folder.
- **Mac app:** quit the host app, replace it with the new app in the same location, reopen it, then check Safari's extension settings and reload affected pages. Keep Safari and the app closed while replacing files.
- **Personally signed local app:** Claude or Codex can run `PYTHONDONTWRITEBYTECODE=1 python3 tools/update_safari_extension.py` after updating and checking the local source. The tool selects a valid certificate from the installed app's team, signs, verifies and installs the update with a previous-version backup. It leaves Safari open; reload pages or restart Safari if needed. See [automatic local updates](SAFARI_STATUS.md#automatic-local-updates-for-claude-and-codex). Do not replace this installation with the ad-hoc public ZIP.
- **Pause:** turn the extension off in Safari Settings and reload affected pages.
- **Remove:** disable the extension in Safari Settings. Remove its temporary entry or delete the containing app, depending on the method you used, then reload pages.

If Source quality was enabled on Twitch, choose your preferred video quality in the player afterward.

## Optional: build with the Xcode installed on your Mac

Requires full Xcode, its command-line tools, and Python 3.11 or newer. Work from the repository's root folder.

```sh
python3 tools/build_safari_extension.py
```

This generates the Xcode project under **`dist/safari-project/Tibia Anti-Ad/`** and the ready-to-run app at **`dist/safari.noindex/Tibia Anti-Ad.app`**. The generated project can be opened in Xcode. The script builds both Mac architectures, verifies resources and applies an ad-hoc development signature. It does not configure a developer account or change Safari's security settings.

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
