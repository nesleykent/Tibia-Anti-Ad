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
