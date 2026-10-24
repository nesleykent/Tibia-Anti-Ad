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

## Safari probability labels, 1.4.0, 2026-10-23

- Safari-only resources display `score.tibia` from the same shared classification result at the right of each channel-name row. The full title and tags feed the existing model. Labels stay present with Hide other games on or off; the master switch pauses both filtering and labels. No training data, weights, thresholds or classification semantics changed. Percentages are estimates, not p-values, calibration guarantees or measured accuracy.
- All repository checks passed, including 51 Python tests. Native Safari and temporary ZIP manifests load the view before the shared filter; packaged resource bytes are checked. Chrome neither ships nor loads the view. The real unpacked Chrome extension passed all 61 fixture cases through DOM and React metadata, statistical title/tag changes and the absence of probability labels, with no page errors.
- A disposable native WKWebView injected the real scripts with a mock extension-storage API. Assertions matched every raw displayed probability to the classifier with Hide other games on and off, then checked master pause, downloaded-model changes, title changes and SPA navigation. Rendered layouts at 1440 and 375 CSS pixels were inspected in light and dark appearances; percentages fit beside long names without horizontal overflow. The public Twitch Tibia directory separately rendered 30 probability labels in WebKit with hiding off, including the current title/name/verified-badge DOM structure. The rendered directory was inspected. These are engine and presentation checks, not activation of the installed Safari extension or an accuracy benchmark.
- Reproduce the native test by compiling `scripts/safari/test_probability.swift` with `swiftc -parse-as-library` and running the executable with the checkout root as its first argument. Add `--live` for the public Twitch check. Test captures and personal update logs remain in the ignored local verification folder.
- The personal updater built, signed, verified and installed Safari 1.4.0, retaining the previous app. A separate installed-copy check matched the Safari manifest, presentation and shared resource bytes, confirmed universal binaries and passed deep, strict signature verification. Safari activation of the new code, unsigned-extension-disabled acceptance and restart persistence remain unverified; the browser and signing checks above do not establish them.

## Private-server presence inference, 1.5.0, 2026-10-23

- The reported visible estimates were above the old cutoff: the previous model hid below approximately 11.9% in the displayed complement. The underlying issue was poor statistical estimates and missed detections, rather than a reproduced CSS hiding failure. The previous training target also included three unrelated games. The replacement learns private-server/official document-presence likelihoods from 370 labelled observations, with channel-separated logistic calibration. It has no absent-feature terms, intercept or text-length normalization. No manual names, user screenshots or filter-predicted labels were added to training.
- With the same 370 observations and outer channel folds, the previous model and cutoff hid 147 of 278 private streams and zero of 92 official streams. The new model and its stricter 98% estimated-piracy cutoff hide 196 private streams and zero official streams; 97 observations abstain. Brier loss decreased from 0.0461 to 0.0345 and log loss from 0.2002 to 0.1102. These are development measurements on limited, mostly rule-assisted labels, not independent production accuracy. The model still misses private streams; the stricter cutoff preserves existing ambiguous-text controls.
- All 55 Python tests passed, including the new regression against dilution by irrelevant text, neutral odds, class-independent patterns, inner calibration channel separation, existing official/ambiguous controls and full-capture Python/JavaScript parity. Repository checks and deterministic regeneration passed. The packaged Chrome extension passed 61 DOM/React cases and controlled changes to each input field; Safari-only probability UI remained absent from Chrome. An initial Chrome run used an old local build; it was rebuilt and the actual current package passed.
- Native disposable WebKit tests now inject the real settings bridge and hiding CSS, rather than a fixture substitute. Assertions verify actual layout visibility against verdicts with filtering on/off. Responsive light/dark checks, downloaded-model changes, title changes, navigation and master pause passed. A public Twitch run displayed estimates on 30 cards; filtering actually hid 28, and the lowest remaining displayed estimate was 8.4%, above the new 2% hiding boundary. Filtered and unfiltered rendering was inspected. Live counts are not reviewed truth labels. These tests do not establish activation of the installed Safari extension or restart persistence.
- The README, extension guide and Twitch documentation explicitly describe supervised probabilistic machine learning, the piracy target, its displayed complement, current cutoff, provenance and limitations. Personal diagnostic reports and captures remain in the ignored local verification folder.
- The personal updater built, signed, verified and installed Safari 1.5.0 with the previous app retained. The installed-copy check matched the current manifest, model, classifier and other web resources, confirmed universal binaries and passed deep, strict signature verification. Actual activation in the maintainer's Safari tab, unsigned-extension-disabled acceptance and restart persistence remain separate unverified items.

## Safari navigation and filter disable, 1.5.1, 2026-10-23

- Reproduced stale hidden grid wrappers in disposable WebKit: after Twitch regrouped a hidden card with a neutral card, the old wrapper still hid the neutral card. Per-scan reconciliation now removes obsolete Tibia verdicts and empty-valued hiding marks, including marks outside the current WeakSet. Disabling restores all cards. Nonempty prompt-hiding marks retain their separate meaning. Classification and model parameters did not change.
- A failing native-sync test demonstrated that a focused page had no update path until another focus event or the one-minute alarm. Visible Safari top frames now check native edits every second, skip hidden pages and coalesce in-flight checks. Storage events update the filter and CSS gate. The native blocked count clears immediately when filtering or the master switch is disabled, rejects stale disabled-state reports, and refreshes only while the popover is open.
- Blocked Streams uses an explicit fixed header instead of relying on navigation chrome that Safari's embedded popover did not display. Settings back navigation, search and category controls stay outside the scrolling list. The settings form remains mounted to preserve its scroll position.
- Repository checks passed, including the native-sync JavaScript scenario. The actual packaged Chrome extension passed 61 DOM/React cases plus regrouping, complete restoration on disable, and title/tag model changes. WebKit assertions passed with the actual hiding CSS and settings bridge, including regrouped wrappers and untracked stale marks.
- Compiled the real SwiftUI views and settings model in Swift 6 with a disposable defaults suite and synthetic streams. Native window events opened Blocked Streams, scrolled the list and returned through Settings, preserving the form's scroll position. Disabled counts and retained active-page context passed. Rendered 360-by-560 layouts were inspected in light and dark appearances. This was an isolated host-window test, not a claim of installed Safari popover activation. Captures and logs remain ignored locally.
- A physical-instance registry query reproduced four entries: two UUIDs for each of the two installed components, all at the same version and installed paths. Removing and re-registering those paths left exactly one instance per component. The updater now includes same-version duplicates in discovery and verifies registration after installation. Regression tests cover duplicate repair, preserving a unique instance and rejecting a failed repair. Browser activation remains separate from registry verification.
- All repository checks passed with 58 Python tests. The updated personal installer completed successfully; the installed 1.5.1 app passed resource and universal-binary checks, deep strict signature verification and a fresh all-instance query confirming exactly one web filter and one native toolbar component. The Safari settings window's refreshed rendering and activation of the update in existing Safari tabs were not verified.

## Safari settings convergence, 1.5.2, 2026-10-23

- After a report of no streams hiding even after reloading, local shared preferences showed native filtering enabled and the last reported web settings disabled. Direct inspection of the Safari tab was denied by macOS Apple-event authorization. The observed mismatch does not identify how web storage first diverged.
- Reproduced a recovery failure with the real background and settings bridge: after a native edit was acknowledged, diverging web storage stayed disabled because the native timestamp had not advanced. Native synchronization now also reconciles differing known settings after an acknowledged native edit. An untouched native store does not override web settings. The regression failed before the fix and passed afterward; all repository checks passed. Installed Safari page activation remains a separate browser check.
- Installed the personally signed 1.5.2 update. Installed resources, universal binaries, deep strict signatures and one registration per component passed verification. The last native report still showed web filtering disabled after installation; a Safari restart and a fresh page check were requested. This is not a verified resolution of the reported live blocking failure.

## Safari native platform detection, 1.5.3, 2026-10-23

- The maintainer confirmed the failure persisted after restarting Safari and supplied a capture with filtering enabled, zero blocked streams, and visible streams with estimated official probabilities below 0.1%.
- The background incorrectly inferred native Safari support from the absence of the action API. A Safari context exposing that API skipped every native sync. Extending the real background/bridge regression fixture to expose both APIs reproduced the failure. Platform detection now uses the Safari extension URL, independently of the action namespace; the regression and complete repository checks pass. This fixture establishes the faulty branch and its repair, not direct inspection of the maintainer's Safari runtime.

## Native JSON-null persistence failure, 1.5.4, 2026-10-23

- The maintainer confirmed 1.5.3 still did not hide streams after restarting. Live macOS logs then established repeated native extension failures while storing rule status containing `error = null` in UserDefaults. That exception occurred before the settings reply. Prior JavaScript-only tests mocked away the native persistence boundary.
- SharedStore now persists only the typed rule timestamp and optional string error, omitting JSON null. The real Swift handler was tested with a disposable defaults suite: a null-error sync returns the enabled native filter edit without aborting, while a string error is retained. Swift 6 native navigation checks and all repository checks pass. Logs remain ignored locally.
- The personally signed 1.5.4 update passed installed-resource, universal-binary and deep strict signature checks. Without another Safari restart, fresh shared state showed both native and web filtering enabled and the directory reporting 51 hidden streams, compared with zero before the fix. This is actual installed-browser reporting; direct rendered visibility inspection remained unavailable because macOS denied Safari automation.

## Popup diagnostics and directory modes, 2026-10-23

- Repository checks: all 56 Python tests, JavaScript smoke tests, model evaluation
  and generated-resource checks passed. Swift-capable hosts additionally execute
  the real native report persistence and SettingsModel regression case. That case
  reproduced the abort caused by JSON nulls before the fix, then verified the
  moved-stream count, mode switching and title-scoped overrides after the fix.
- Chrome Beta: real unpacked-extension tests saved and parsed JSON files from both
  the isolated content script and the actual action popup. Full React titles,
  duplicate tags, exact integer viewer counts and viewer updates were verified.
  Popup changes persisted the mode and threshold. Page-session exports retained
  streams whose cards had been removed.
- Browser regression fixtures verified two stable groups, Hide and Show behavior,
  Show overrides, and unchanged card positions above and inside the viewport when
  additional streams loaded. Rendered desktop and phone-size views were inspected.
- Live Twitch in isolated Chrome: 30 cards used flex cells and received CSS order;
  Move to bottom affected 27 while hiding none. Desktop (1280 by 800) and phone
  (375 by 667) screenshots were inspected. Viewer data was located in Twitch's
  `currentViewerCount` property, preserving integers instead of rounded labels.
- Safari 27.0.1: the maintainer saved real diagnostics JSON through the native
  popup, including a 407-stream capture. Both captures parsed successfully and
  entered the evaluation CLI directly. The maintainer also confirmed that the
  moved-stream count and list populated after the native report fix. Restarting
  Safari resolved a stale-script export failure following an app update.
- Safari WebDriver could not establish a session despite remote automation being
  enabled. Safari file saving and the affected-stream list were therefore checked
  with the maintainer; automated scroll stability used Chrome. The final inline
  native slider was separately rendered and visually inspected in a SwiftUI
  preview. Real Safari scrolling remains a manual verification limit.
- Packaging/signing is separate: the local Safari updater builds, personally signs,
  verifies and installs the current source with a retained local backup. No signed
  personal app or captured stream data is published with this change. Signature
  verification does not establish Safari restart persistence or certificate lifetime.

### Directory regrouping regression, 1.6.4

The maintainer supplied Safari screenshots showing below-threshold cards before
preferred cards at an 85% threshold. A browser regression reproduced the stale
order when changing the threshold after scrolling: the visited-prefix rule also
applied to deliberate settings edits. The fix resets ordering for explicit mode,
threshold and Show-override changes, while automatic card updates retain the
existing scroll-stability behavior. The test now checks full regrouping after
threshold edits and then unchanged viewport positions on incremental loading.
A separate native regression verifies that a non-directory Twitch tab cannot
replace the category’s affected-stream report with an empty report.
The live Chrome check changed the threshold after actual wheel scrolling, then
asserted the rendered top/left order: all 3 preferred cards preceded all 27
affected cards at 85%. Desktop and phone-sized screenshots were inspected.
Repository checks and real unpacked-popup/export regressions passed. Safari
1.6.4 was built, signed, verified and installed; WebDriver again timed out when
opening a session, so the final Safari visual confirmation remains manual.

### Identifier-span learning and scheduled publication, 1.7.0

2026-10-23: all 399 supplied metadata inputs were labelled from title/tags only.
The feature-only packet retains supervision without raw local titles, channels,
images or filenames. Of 271 private inputs, 44 previously displayed more than
50% official; the fitted identifier model reduces that count to 0. Every runtime
prediction also agrees with replay from the feature-only packet.

Leave-one-server-identity-out refits exclude all matching historical and supplied
examples, including aliases and candidate identity matches. The final benchmark
caught 362/394 stream/identity pairs across 68 folds, 91.9% recall. All six required
new-name controls passed. These are development acceptance controls, not untouched
validation claims. Aggregate results and supervision digest are recorded in
[the evaluation report](../research/twitch/model/span-evaluation.json).

Repository verification: 68 Python tests, JavaScript checks, active acceptance,
Python/JavaScript inference parity and generated-source consistency passed.
The frozen model reproduced exactly from its feature-only supervision with
NumPy 2.3.5. Workflow YAML parsed. API pagination, strict LLM coverage and span
validation, secret-safe failures, newest-capture separation and concurrent-main
publication rejection passed mocked integration tests. Live Twitch/OpenAI calls
and a scheduled publication await the repository secrets described in
[the pipeline guide](TIBIA_LEARNING.md).

Browser verification, separately: Chrome Beta passed full metadata transport,
probability complement and hiding at desktop/mobile sizes, explicit mode and
threshold regrouping, stable incremental loads, diagnostics history, actual file
download, popup persistence and export with the real unpacked extension.

Build/signature verification, separately: the signed Safari updater completed
successfully, installed 1.7.0 and retained the prior app. This does not establish
Safari activation with unsigned extensions disabled or restart persistence.

## Bare server identifiers, 1.7.1

2026-10-23: a live title containing the bare names Feruots and Retronic reproduced
99% official under revision 5. Revision 6 assigned 10.2% official to the same full
title and tags in the real Chrome Beta unpacked extension. This capture covered
45 unique live inputs, not the entire category. Domain-derived training views

All 399 labelled export controls still pass: 271 private, none above 50% official.
Leave-one-server-identity-out recall is 364/394 pairs across 68 folds (92.4%);
all six mandatory unseen-server controls pass. These remain development controls.
Repository checks passed 71 Python tests, JavaScript acceptance, inference parity
and generated-source consistency. Browser checks separately passed full metadata
transport, probability complement, hiding, regrouping, diagnostics retention and
saved downloads at desktop/mobile sizes.

Build/signature verification, separately: the personal Safari updater installed
and verified 1.7.1, retaining the previous signed app. Its containing app can
request an immediate rules refresh through the existing App Group bridge.

Safari runtime verification, separately: after publication and opening the real
Tibia directory, the native rules report recorded a successful fresh download
without the previous validation error. All 85 metadata inputs matched against
the earlier export had revision-6 probabilities; only 14 also matched revision 5.
The live bare-name regression appeared in the native affected-stream report at
89.79% private (10.21% official). This verifies that the running directory received
the model, without claiming unsigned-extension or restart-persistence acceptance.

## Project/protocol recognition, 1.7.2

2026-10-24: metadata review of a newly saved Safari diagnostic covered 145 inputs,
112 labelled private. One private input previously displayed more than 50%
official; revision 7 reduces that count to 0. One hosting-domain false positive
also returns to the exact 1% private baseline. Two additional historical launch
and protocol regressions now pass.

The trainer no longer calibrates negative identifier cutoffs from private session
rows with missing identifier annotations. Eighteen missing identifier annotations
were completed with corrections and prior groups retained in the feature-only
packet. Historical session labels and targets remain unchanged. Canonical aliases
share a holdout identity. All original 399 controls still pass, including the 271
private inputs and the original 44-to-0 count above 50% official.

The complete server-name holdout caught 367/400 stream/identity pairs across 70
folds (91.8%), with all six mandatory cases passing. The identity annotations and
canonical alias grouping are more complete than in the earlier 68-fold report;
these remain development acceptance results, not untouched validation claims.

Repository checks passed 76 Python tests, JavaScript acceptance, inference parity
and generated-source consistency. The frozen model reproduced exactly from its
supervision. Python/JavaScript parity also passed all 544 raw metadata inputs from
the original and supplemental captures. Browser verification separately passed
full metadata transport, complement/hiding, grouping, session retention and an
actual saved diagnostics download at desktop/mobile sizes in Chrome Beta.

Build/signature verification, separately: the personal updater installed and
verified Safari 1.7.2. Runtime verification, separately: a saved diagnostic from
a real Safari category page reported extension 1.7.2 and model 7; all 54 loaded
inputs matched the final model's predictions. This checks the active classifier,
without claiming whole-category coverage, unsigned-extension acceptance or
restart persistence. Format v4 requires the updated extension source.
