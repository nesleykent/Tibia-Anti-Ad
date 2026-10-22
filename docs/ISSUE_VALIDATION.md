# Issue verification — 2026-10-22

Maintainer priority: Safari. Browser observations below were collected in isolated Chrome 157.0.8103.6 profiles on macOS 27.0.1, with the actual unpacked extension. They are supplementary evidence, not Safari certification. No personal browser profile, Safari preference, signing identity or installed app was changed.

## Completed

- Fixed channel leakage in `tools/train_tibia_model.py`: 857 observations represent 742 channels. The old five-fold split placed 87 of the 115 repeated channels on both sides of a training/test boundary. All captures of a channel now share a fold. A regression test reproduced the leak before the fix and passes afterward.
- Added precision confidence intervals and abstention counts, distinguishing development cross-validation from independent validation. At the current model cutoff of 6: 364 predictions of other games, zero official false positives, recall 57.5%, abstention 355/857. Observation-level Wilson interval: 98.96–100%; repeated captures are correlated, so this is not independent-sample validation or a release gate.
- Real Chrome requests were blocked on eight fansite homepages at desktop (1440×900) and narrow (390×900) widths: GuildStats, HakaiMarket, Hunt Analyser, Intibia, TibiaLife, TibiaMonk, TibiaPal and TibiaVIP. Before/after screenshots were inspected. These checks do not certify every tool or keyboard flow.
- Tibiopedia `/news`: selected English and Library layout, synchronized the settings mirror, disabled/cleared the HTTP cache, then collected five alternating desktop pairs and one narrow pair. Text remained present with blocking enabled (9,696 characters versus 9,713 baseline). Five requests were blocked per filtered run. `/monsters/Cockroach` also retained content at both widths.
- GuildStats `/guild/United`: the filtered runs retained content at both widths, blocked three requests, and had no `google-anno` roots. The baseline contained Google's ad-intents roots. This confirms real cleanup rather than assuming an empty ad slot proves network blocking.
- Twitch `/nxxxte`: the filtered session blocked 19 requests across `spade.twitch.tv`, `s.amazon-adsystem.com`, `edge.ads.twitch.tv` and `sb.scorecardresearch.com`. Four samples showed progressing 720p playback and chat present with no player error. No video ad was served during either observation window; pre-roll/mid-roll removal remains unverified. Captions were unavailable in both sessions; sign-in was not exercised.
- Twitch directory: 24 of 30 initial cards were hidden in the filtered session. The real storage/DOM path passed Show, undo Show, and disabling the filter. Card counts do not establish classification accuracy.

## Measurements, not ratings

Tibiopedia news, five desktop pairs:

| Metric | Baseline median (range) | Filtered median (range) |
| --- | --- | --- |
| Requests | 758 (722–787) | 241 (241–241) |
| Transferred bytes | 6,429,450 (5,996,532–6,704,623) | 2,086,822 (2,056,700–2,216,961) |
| Observed long-task blocking, ms | 0 (0–34) | 0 (0–0) |

The median differences were 517 requests and 4,342,628 bytes. Other browser probes overlapped this collection, so it is exploratory; no strict performance rating, speed claim or positive award is issued. Consent was not accepted, accounts were not signed in, and cookies were cleared before each pair. Layout/language selection was repeated on Tibiopedia. Unknown assessment dimensions remain unknown.

## Remaining acceptance and blockers

- **#1:** Safari enforcement and complete functional/accessibility checks remain open. SafariDriver explicitly refused a test session because Allow remote automation is disabled. Authorization to enable it was not obtained; the preference remains unchanged. Several public pages returned HTTP 403 without blocking enabled. TibiaWiki BR displayed a **Cloudflare CAPTCHA**, not an extension failure. Exevo Pan returned a plain 403. No CAPTCHA was solved or bypassed.
- **#1:** HakaiMarket `/monsters/dragon` produced a reproducible blank page at narrow width in the filtered sequence, with `getCharmPointsValue is not defined`. The unfiltered sequence remained visible. This is an unresolved compatibility failure; no claim of full preservation is made. A subsequent public-source request returned HTTP 429, so further requests were stopped. A fresh profile without any extension also retained visible content and reported no script error. Next step: isolate the two blocked requests and the cosmetic rules separately before changing a rule.
- **#2:** exploratory before/after measurements exist; a complete assessment protocol and verified positive examples remain open. No unknown result was converted into a zero or an award.
- **#3:** real network blocking and a short playback check passed; served video-ad transitions, caption/sign-in preservation, stalls and fallback behavior still need verification in Safari.
- **#4:** channel leakage is fixed and reversible controls were exercised. No existing model was retrained or automatic hiding behavior changed in this patch.

## Reproduce and resume without repeating completed work

- Repository checks: `PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py`.
- Model report: `PYTHONDONTWRITEBYTECODE=1 python3 tools/train_tibia_model.py`.
- Optional live tools: `tests/browser/live-sites.cjs` and `tests/browser/live-twitch.cjs` require Playwright and Chrome Beta, or `CHROME_BETA_BINARY` pointing to a compatible Chrome. Use an existing Playwright installation through `NODE_PATH`; no browser package is installed by these scripts.
- Site options: `--deep` selects the documented internal pages; `TIBIA_SITE_PATH=/news` with `tibiopedia.pl` selects its news test. `TIBIA_AUDIT_RUN` names a separate attempt. Results and screenshots remain in ignored `local/verification/`; completed site attempts are reused.
- Twitch option: `--directory-only` checks filtering and reversible controls without repeating playback sampling.
- Sanitized observations and screenshot hashes: [results](../research/validation/2026-10-22/results.json). Local raw diagnostics/captures remain under `local/verification/live-sites*`, `local/verification/live-twitch` and `local/verification/issues`. Build/signature checks are separate from these browser observations.
- Exact next work: resolve the HakaiMarket narrow-layout failure, then perform the remaining Safari acceptance after its test-control prerequisite is authorized. Reuse this ledger and existing captures; do not restart the entire inventory.

Wilson calculation reference: [NIST confidence intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).
