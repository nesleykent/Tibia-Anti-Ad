# Verification record

Date: 2026-10-21. Verification concerns repository setup, artifact construction and the offline prototype. It does not certify live ad-blocking behavior.

- Inventory: 15 supplied per-site filter files; 14 historical reports and 5 companion userscripts. TibiaWiki BR has no standalone report in the supplied files.
- Generated artifacts: 13 sites included; Tibiopedia and TibiaWiki BR excluded because supplied research describes content-destruction risks.
- Automated tests: network/cosmetic site boundaries, source-scope rejection, exclusion policy, portable/extended separation, reproducible output and inventory completeness.
- Classification tests: corroborated declarations, ambiguous mentions, negation, mixed signals, language/category-only evidence, invalid inputs and no automatic hiding.
- Command-line smoke checks: valid input produces JSON; invalid input fails with a readable error and no partial output.
- Local documentation links checked for missing files.
- Original root assets retained unchanged; ZIP archives and local session artifacts excluded from publication.

No website was opened or audited anew for this release. These remain open work in the roadmap. Historical report claims remain attributed to their supplied source, not to this verification run.

## Twitch package integration

The supplied `twitch-clean.zip` is now integrated: extension source and icons, standalone StopTheMadness script, Twitch filter list, updated recon script and historical report. Archive/file SHA-256 values record exact provenance. Node smoke tests check startup, Source quality, visibility and worker/fetch hooks with mocks for both script entry points. Manifest/resource and DNR structural checks are automated. These tests do not reproduce real Safari enforcement or live Twitch ad removal.

## Repository professionalization — 2026-10-21

Scope: maintained documentation, project policies, build packaging and CI. The supplied manifesto is preserved in full in [MANIFESTO.md](../MANIFESTO.md); only Markdown headings and paragraph formatting were added. Existing extension behavior and imported source bytes were preserved.

Local verification:

- `python3 tools/check_project.py`: 32 Python tests, Node startup/settings checks, syntax checks for packaged scripts, maintained local documentation links and deterministic regeneration passed.
- Chrome build: all manifest scripts, rulesets, icons, popup and service-worker imports resolve; rebuilding removes stale output and packages license notices. Tests build into a temporary directory.
- Offline evaluation of the supplied 456-row audit: zero official-Tibia rows classified as `other`; eight unclear rows classified as `other` remain unresolved evidence, not confirmed successes. The audit is development data, not an independent holdout benchmark.
- Website bundles: 13 sites; extension site rules: 15 sites, including experimental repairs for the two excluded from subscriptions. Generated results remain reproducible.
- No live ad-blocking, browser enforcement, visual layout or cross-browser accessibility certification was performed in this maintenance change. Imported-asset redistribution rights remain a release gate.

CI checks Python 3.11 and 3.14 with Node.js 22. Its uploaded Chrome package is a development artifact for the checked commit, not a stable release. Consult [GitHub Actions](https://github.com/nesleykent/Tibia-Anti-Ad/actions/workflows/check.yml) for published run results.

## Directory reorganization — 2026-10-21

- Shared extension source moved to `extension/src/`; Chrome overrides to `extension/browsers/chrome/`.
- Filter inputs moved to `filters/sources/`; generated subscriptions to `filters/lists/`. Current installation links use the new URLs; previous subscription URLs must be replaced.
- Fansite reports/userscripts moved to `research/fansites/`; Python and JavaScript tests are separated under `tests/`.
- SHA-256 checks confirm all 19 moved historical reports/userscripts and all 40 locally archived originals retain their bytes. Local originals are ignored under `local/legacy/`.
- Comparison against the previous commit confirms extension runtime bytes are identical except for updated paths in comments. Effective subscription rules are unchanged.
- The full repository checks and Chrome build pass with the new paths. Documentation indexes and provenance path keys were updated; original provenance digests remain unchanged.

## Friendly-fansite evidence — 2026-10-22

- Received and visually inspected 23 supplied PNG screenshots. The user confirmed ad blockers were disabled; exact capture times, page URLs, browser versions and network evidence were not supplied.
- Original bytes are preserved under `research/fansites/friendly/screenshots/`. The manifest records original names, sizes, dimensions, SHA-256 values and visual observations; the check command verifies the inventory and image metadata against those values.
- Tibia-Statistic’s small Amazon affiliate section is visible and documented. The user explicitly requested that it remain in the friendly selection. No filtering exemption was added.
- Long captures, missing images and rendering artifacts limit visual conclusions. No tracking, performance or live behavior rating was inferred. The existing test/build checks pass.

## Safari packaging — 2026-10-22

- Generated a macOS Xcode project from the shared extension source with Apple’s Safari converter. Corrected the converter-generated host identifier so the embedded extension’s identifier has the required prefix.
- Built both `arm64` and `x86_64` binaries using Xcode 27.1 on macOS 27.0.1, targeting macOS 14 minimum; the manifest still requires Safari 26+. Older Macs and OS versions were not executed in this run.
- The build checks every bundled web resource against the shared source, validates bundle identifiers, checks both architectures and verifies the nested app signatures. Public previews and CI use ad-hoc signatures with the converter's sandbox entitlements. Later on 2026-10-22, a free Apple Development identity became valid after restoring the missing Apple WWDR G3 intermediate certificate. Both bundles were personally signed, installed in `/Applications/Tibia Anti-Ad.app`, and passed deep, strict signature verification; macOS registered the installed extension. This is not an Add Temporary Extension installation. See [current Safari signing status](SAFARI_STATUS.md). No Developer ID or notarization is claimed.
- Native startup is checked through the build-and-run script; this does not certify Safari extension enforcement or live ad removal. Safari’s unsigned-extension preference is not changed automatically.
- Acceptance of the personally signed extension with unsigned extensions disabled, and persistence after Safari restarts, remain unverified. Do not apply the temporary ZIP's lifetime to this installed app or report restart persistence as tested.
- The temporary-extension ZIP has a deterministic top-level folder, source-byte preservation checks, original license notices and a SHA-256 checksum. Native app packaging preserves bundle metadata with Apple’s `ditto`.
- A separate macOS CI job builds, verifies and packages the Safari app without distribution credentials. See GitHub Actions for results on each exact source commit.

## Personal Safari updater — 2026-10-22

- Ran `tools/update_safari_extension.py` against the installed personal app. It discovered a valid identity from the same Apple team, built and signed the app and extension, verified the staged copy and installed result, and retained the previous app under `local/safari/previous/`. Both the installed app and backup passed deep, strict signature verification. `pluginkit` reported the updated extension at its Applications location.
- Automated failure tests verify that a rejected staged candidate preserves both the installed app and existing backup, and that failed installed-copy verification restores the old app. A successful replacement test verifies the new files and retained backup.
- Safari tabs were left open. Updated extension activation, retained Safari settings and restart persistence were not established by this updater test.

## Circular infinity icons and native host — 2026-10-22

- Version 1.2.3 uses the official `infinity.circle` / `infinity.circle.fill` for Safari toolbar and status indicators, and original outlined/filled circle vectors for Chrome and shared branding. No slashed variant is used. The earlier imported shield icons were replaced and their original hashes retained in the provenance record.
- The native WebKit test parsed the real manifest without errors and passed four alternating storage-triggered action image/title transitions, including equal images on returning to each state and distinct images between states. Popup image sources were checked. Native test runtime errors were empty.
- The installed Chrome Beta 157.0.8103.6 passed real action API and popup checks for both states in light/dark appearances in a disposable headless profile. Saved disabled state was restored after restarting the test browser and reloading its unpacked extension. Local screenshots include popup states and rendered icon previews; the browser's native toolbar chrome was not captured.
- The native host now safely validates script messages, uses a weak message-handler proxy, restricts navigation to local resources, reports status/settings errors, and quits after opening Safari Settings only on success. The app build version now follows the extension version rather than remaining fixed at 1.
- The universal app and extension were signed and installed through the personal updater. Installed resources and signatures are checked separately from the browser tests. Live Safari restart persistence remains a separate unverified item.

## Issue verification — 2026-10-22

See the [issue verification ledger](ISSUE_VALIDATION.md) for the channel-split fix, reproducible browser observations, the unresolved HakaiMarket failure and remaining Safari acceptance. These results do not certify all four issues as complete.

## Twitch title filtering, 2026-10-23

- Diagnosis: the full title already reaches both lexical rules and the statistical model. The supplied screenshots exposed missing names (`otponline.com`, `Ibaiak-idle`) and a conflict between a declared server (`[DEUSOT]`) and the generic word "global". Reproduced all three as `undetermined` before the fix. Added the names and stopped treating bare "global" as official evidence alongside an exact, affirmative server declaration. Official worlds and the phrase "Tibia Global" retain their evidence; commands, negation and comparisons do not trigger the new declaration rule. The statistical model and its cutoff were not changed or retrained.
- Repeated browser verification also reproduced old downloaded rules replacing newly bundled evidence. The rules data now has an additive integer revision; bundled revision 1 rejects earlier cached/downloaded data and uses its built-in corrections. Same/newer compatible revisions remain supported. Regression checks cover stale cache/download rejection, malformed revisions, preserved last-good data and recovery after a good download.
- Source for `otponline`: the game's own [rules](https://otponline.com/es/rules) identify it as an independent anime/manga game. `Ibaiak-idle` is the compound spelling visible in the supplied screenshot; it is recognized as a whole name rather than matching arbitrary words ending in "baiak". No channel denylist was added.
- Repository verification: 46 Python tests, JavaScript checks and deterministic regeneration passed. Fourteen new classification cases include the screenshot titles, official controls, mixed/negated mentions and a title-only statistical verdict with just the language tag. Python/JavaScript verdicts and scores agree. Across the 456-row audit and 562-stream capture, no existing verdict changed; the audit still hides none of its 92 official streams. These are development captures, not an independent accuracy benchmark.
- Browser verification, separate from signing: actual unpacked extension in disposable Chrome Beta 157.0.8103.6 profiles. All 61 applicable fixture cases passed twice with stale cached evidence explicitly seeded: DOM title fallback and React metadata with a deliberately truncated DOM title. The test awaits reclassification after the metadata bridge publishes its values. No fixture page errors. Screenshots of both filtered fixture grids were inspected. A live Twitch run confirmed that all 30 stream cards' complete React titles matched their DOM title attributes; 29 also classified as `other` with tags removed. The filtered page hid 29 of 30 cards, and Show, undo Show and disabling the filter passed. Live counts are observations, not reviewed labels or measured accuracy. Non-stream `article` elements are excluded from the title assertion. Live screenshots were inspected.
- Safari build/install verification: version 1.2.4 was built, personally signed, verified and installed through `tools/update_safari_extension.py`, with the previous app archived locally. Installed classifier, evidence, filter and metadata-reader bytes match the checked shared source. This does not establish Safari activation of the updated code, unsigned-extension-disabled acceptance or restart persistence; those remain unverified. The updater left Safari running.
- Test logs, before/after verdict comparisons, browser diagnostics and screenshots are retained locally in the ignored verification folder. Personal signing logs and screenshots are not published.

## Statistical title/tag decision, 1.3.0, 2026-10-23

The preceding 1.2.4 change added lexical cases; it did not replace the rule-dominated decision. Version 1.3.0 removes the manual name/channel tables and heuristic overrides from active classification. A trained logistic text model now directly decides from the complete title and tags together. See the [model card](TWITCH_MODEL.md) for the representation, training provenance, input comparisons and limitations. The exported data contains learned numeric parameters, not a list of manually banned names.

- Training uses 373 labelled audit observations and excludes the filter's own predicted labels. Channel-grouped development cross-validation compares identical folds and cutoff: joint input hides 141 of 281 other-game examples with 0 of 92 official examples hidden; tags alone hides 105 other-game examples and 2 official examples. Joint input abstains on 203 observations. This is development evidence with limited, rule-assisted audit labels, not an independent accuracy guarantee. About half of the labelled other-game examples remain undetected at the conservative cutoff.
- All repository checks passed, including 49 Python tests and JavaScript checks. Python/browser feature identifiers, scores and field contributions agree on the historical captures and controls. Tests show that zero learned weights cannot ban a name, channels do not affect inference, learned character fragments transfer to unseen whole words, and both fields contribute to the joint score. Historical heuristic other-game examples may now abstain; official/neutral visibility controls remain enforced.
- The actual unpacked extension passed 61 fixture cases through both DOM fallback and the React bridge, matching the independent Python port. A controlled statistical model with synthetic text then proved actual card visibility changes when only the title changes with tags fixed, and when only tags change with the title fixed. Text-node-only title changes and empty metadata titles also passed. This tests the input path without any server-name rule. Fixture pages reported no runtime errors; rendered screenshots were inspected.
- A separate live Chrome Beta 157.0.8103.6 run checked complete titles on 30 cards. The new joint model hid 24, while 21 also classified as other games with tags removed. Show, undo Show and disabling the filter passed. These are live observations, not independently reviewed game labels. The rendered directory was inspected.
- The personal Safari updater built, signed, verified and installed version 1.3.0. Installed classifier, model, title reader, filter and rule-update resources match the checked shared source; deep signature validation passed with keychain access. Native installation/signing are separate from the Chrome browser checks. Activation in Safari, unsigned-extension-disabled acceptance and restart persistence remain unverified. No personal signing details or screenshots are published.
