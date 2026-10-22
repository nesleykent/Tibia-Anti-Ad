# Safari signing status

Last verified: **2026-10-22**. This record supersedes the earlier statement that no Apple signing identity was available.

## Installation methods

| Method | Signing and installation | Lifetime / verification |
| --- | --- | --- |
| Temporary source ZIP | Added through Safari's **Add Temporary Extension…** | Safari removes it after 24 hours or when Safari quits. |
| Public Release Mac app / default CI build | Ad-hoc signature; app contains the extension | Requires unsigned-extension development mode. Safari resets that permission when it quits; app files remain installed. |
| Maintainer's installed Mac app | Free **Apple Development** certificate; `/Applications/Tibia Anti-Ad.app` | App and embedded extension signatures verified. Registered with macOS. Safari acceptance with unsigned extensions disabled and restart persistence still need verification. |

The maintainer's installed app uses the third method. **Do not call that installation temporary or tell the maintainer to add the ZIP again after every Safari restart.** It was not installed using Add Temporary Extension. This does not establish permanent certificate validity or verified Safari persistence.

## Work completed on the maintainer's Mac

1. Xcode created a free Apple Development identity through the account's Personal Team.
2. The private key was present, but the Apple WWDR G3 intermediate certificate was missing. Downloading the official intermediate from Apple's certificate authority, validating its chain and adding it to the login keychain made the development identity valid. No Always Trust override was used.
3. Built the shared source as a universal Mac app and signed the embedded `.appex` first, then its containing `.app`, with the same development identity and the repository's sandbox entitlements.
4. Installed the result in `/Applications/Tibia Anti-Ad.app`. Deep, strict code-signature verification passed, and `pluginkit` reported the extension at that installed location.

Bundle identifiers: `com.nesleykent.tibiaantiad` (app) and `com.nesleykent.tibiaantiad.Extension` (extension). Personal certificate identifiers and private keys are intentionally excluded from this record.

## Automatic local updates for Claude and Codex

After updating the code in the current checkout and running the repository checks, the agent runs:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/update_safari_extension.py
```

This discovers the installed app's Apple team and a valid Apple Development identity from that team in the local keychain, including a renewed certificate if available. It builds the current source, signs and verifies both bundles, stages the app and updates the existing Applications location. The previous app is retained under `local/safari/previous/Tibia Anti-Ad.app`; failed installed-copy verification restores the previous installation. Concurrent runs are rejected. No personal identity needs to be stored in repository configuration.

The agent should perform this update itself instead of delegating certificate selection, signing or file copying to the maintainer. The tool does not pull source, publish assets, change Safari preferences or close the user's Safari tabs. It opens the installed host app after the update. Reload affected pages; Safari may need to be restarted to load the updated extension. Preservation of enabled state and settings across updates has not yet been verified in Safari.

If no valid identity from the installed team is available, the update stops before replacing the installed app. The account owner may need to renew their certificate in Xcode or approve a macOS keychain prompt; agents must not bypass such prompts or fall back to ad-hoc signing.

## Build only, without changing the installed app

With an existing valid development identity in the local keychain:

```sh
python3 tools/build_safari_extension.py --sign-identity 'Apple Development'
```

Or build and launch with:

```sh
TIBIA_SAFARI_SIGN_IDENTITY='Apple Development' ./scripts/safari/build_and_run.sh
```

If multiple identities match, supply the exact certificate name or SHA-1 shown by `security find-identity -v -p codesigning`. The tool signs both bundles and checks their signatures. It writes to `dist/`; it does not update the installed app in Applications. Verify the new build, quit the host app and Safari before replacing the installed app, then verify the installed copy again. Do not substitute a public ad-hoc download for a personally signed update.

Without an explicit identity, both commands use ad-hoc signing for preview/CI builds. Generated Xcode projects are recreated and do not retain manual signing selections. Certificates stay in the local keychain; never commit or distribute personal signing material or upload the personally signed app as a public Release asset.

## Remaining Safari check

In Safari, turn **Allow unsigned extensions** off, enable the installed Tibia Anti-Ad extension, then quit and reopen Safari. Confirm the extension remains enabled and works on an allowed page. Record the Safari version, date and observed result here when this has actually been checked. Native signature validation and registration alone do not prove this behavior.

## Sources

- [Apple: Personal Team signing](https://help.apple.com/xcode/mac/current/en.lproj/dev60b6fbbc7.html).
- [Apple: missing intermediate certificate](https://help.apple.com/xcode/mac/current/en.lproj/devc4c7101d8.html) and [WWDR certificate purposes](https://developer.apple.com/help/account/certificates/wwdr-intermediate-certificates/).
- [Apple: running a Safari web extension](https://developer.apple.com/documentation/safariservices/running-your-safari-web-extension).
- [Installation guide](INSTALL_SAFARI.md) and [verification record](VERIFICATION.md).
