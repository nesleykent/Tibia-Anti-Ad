# Release and maintenance guide

Passing repository checks establishes repository integrity, not production readiness. Until the live checks below have evidence, publish only explicitly labeled experimental or prerelease artifacts.

## Review gates

1. Run `python3 tools/check_project.py` on a clean checkout. Review generated changes and upstream notices. Never bypass a failed check by deleting a test or lowering an acceptance threshold.
2. Install the actual built extension and exercise settings, pause/resume, restart persistence, per-site controls, stream explanations, Show/Hide corrections and rollback. Record browser, OS, commit and enabled features.
3. For each affected fansite, test home and deep pages at desktop/mobile widths. Verify actual network enforcement and delayed ads. Check articles, search, navigation, calculators, maps, forms, sign-in, scrolling and keyboard focus against a clean baseline.
4. For Twitch changes, check live ad breaks, audio, captions, playback quality, reconnects and chat. Measure false positives on independently reviewed holdout broadcasts; keep uncertain streams visible. Do not generalize the development samples to production accuracy.
5. Record dated evidence and remaining limits in [VERIFICATION.md](VERIFICATION.md). Redact personal data. Confirm rights for imported assets listed in [third-party notices](../THIRD_PARTY_NOTICES.md).
6. Update [CHANGELOG.md](../CHANGELOG.md), compatibility notes and installation/rollback instructions. Verify the exact commit to publish. GitHub Actions is disabled; publish through the maintainer account with written release notes.

## Version and artifacts

Use semantic versions for extension releases and keep the source manifest version aligned with the release tag. Use prerelease tags such as `v1.0.0-alpha.1` while experimental; the browser manifest itself accepts only its numeric version format. Do not create a stable tag just because the existing manifest says `1.0.0`.

Build the installable ZIP with `python3 tools/package_chrome_extension.py`. It creates `dist/tibia-anti-ad-chrome.zip` with one top-level `tibia-anti-ad-chrome/` folder and a `.zip.sha256` checksum. Publish both as assets on the tagged GitHub prerelease/release, then update direct download links in the README, extension guide and Chrome tutorial. The ZIP must download without GitHub authentication.

Build only the unpacked folder with `python3 tools/build_chrome_extension.py`. This unpacked development build is not signed or store-reviewed. Distribute a reviewed archive with its commit, SHA-256 checksum, license and third-party notices. Build Safari with `python3 tools/build_safari_extension.py` on macOS with Xcode, then `python3 tools/package_safari_extension.py`. Publish both Safari ZIPs and their checksums. The containing app has an ad-hoc development signature only; Developer ID signing and notarization remain unconfigured. Label it as a development preview and link the unsigned-extension instructions. Never publish credentials, local archives or private captures.

## Maintenance and rollback

The repository owner is the current maintainer and reviews contributions. Prioritize security reports, content loss, broken core tools and hidden legitimate broadcasts before adding coverage. Track other work in issues and the [roadmap](ROADMAP.md); no response-time commitment is implied.

Keep `main` usable and reviewable. Contributors submit pull requests. The owner may authorize direct pushes; they must still pass the same checks. Do not force-push published history. For a regression, disable the affected feature or subscription, document the workaround and revert the offending commit with a new commit. Rebuild artifacts and rerun affected browser checks before publishing a correction.
