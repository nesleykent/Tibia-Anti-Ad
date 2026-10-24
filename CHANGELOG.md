# Changelog

## 1.7.5 - 2026-10-24

- Correct three metadata-identifiable private streams that still displayed 99% official in revision 9. Revision 10 recognizes their independent server tag, branded server name and private-world declaration, displaying 4.0%, 2.3% and 2.3% official respectively.
- Preserve all previous labels and server identities. The original 399-input acceptance still has 271 private inputs and none above 50% official. Server-name holdout remains 376/400 pairs (94.0%), with all 6 mandatory controls passing.
- Remove GitHub Actions workflows, the workflow badge and remote artifact restoration. GitHub Actions is disabled for the repository. No replacement scheduler is introduced.
- Publish releases through the maintainer account with written change descriptions and verified Chrome/Safari ZIPs and checksums. Correct the authorship and notes of 1.7.4 while retaining identical download bytes.

## 1.7.4 - 2026-10-24

- Rebuilt Tibia-directory classification around learned identifier spans from complete titles and tags. The model uses character and structural features of domains, server commands and project names, without a runtime server-name list.
- Added recognition for spacing and Unicode variants, Pokemon and idle projects, project names beside legacy protocols, and bare brands derived from annotated domains. Revision 9 includes the reported Padventures title and tag correction.
- Preserved sponsor-list, negation and mixed-session handling. Language, generic gameplay and channel identity are excluded from classification. Titles/tags without private-server evidence remain at 99% displayed Tibia probability.
- Added Show, Move to bottom and Hide modes, a persisted probability threshold, stable Twitch ordering and per-stream Show overrides. Explicit setting changes regroup all loaded cards.
- Added diagnostics export with complete metadata, probabilities, model evidence, version and rule revision. Safari exports through the page instead of the unsupported extension download API.
- Fixed Safari native settings synchronization, rule-status persistence, affected-stream reports and duplicate extension registration during personal updates.
- Added native Safari controls and outlined/filled circular infinity status icons. Chrome uses matching original vector icons.
- Installation links now select the latest published packages.

## 1.2.3 - 2026-10-22

- Added the earlier context-aware Tibia filter and downloaded filter-rule updates.
- Added searchable affected-stream management with Show overrides.
- Added the native SwiftUI Safari host window and corrected its first settings launch.
- Fixed Safari parsing by keeping extension JavaScript ASCII-compatible.

## 1.0.0-alpha.2 - 2026-10-22

- Published Chrome and Safari development-preview downloads with installation guides and checksums.

## 1.0.0-alpha.1 - 2026-10-22

- Published the initial Chrome development preview.
