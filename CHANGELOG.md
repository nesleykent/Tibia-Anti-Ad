# Changelog

Changes are recorded for users. Unreleased entries describe `main`, not a stable release or a browser-store publication.

## Unreleased

### Added

- Full Tibia Anti-Ad Manifesto and project principles connecting viewer choice, content preservation and transparent evidence.
- MIT license for project-authored work, third-party notices, security policy, community conduct and maintainer guidance.
- Structured breakage and false-positive reports, contribution review checklist and release acceptance gates.
- One local/CI check command covering syntax, tests, offline evaluation, documentation links and reproducible generated artifacts.
- Automated Chrome package resource checks and CI artifacts for development builds.

### Changed

- Tibia category filter: weighted, context-aware classification replaces exact keyword rules. Titles and tags are normalized (accents, lookalike Cyrillic/Greek letters, small capitals and fancy Unicode fonts, leetspeak, repeated and spaced-out letters), listed server names also match one spelling mistake away (`rubimot`, `pokealianca`, `rubiniot`), PokeAlliance's Titan servers count as its worlds, and negation, leaving, comparison and "later" words weaken a mention (`não jogo rubinot`, `ex-rubinot`, `Tibia vs RubinOT`). Weak context (server rates, old client versions, "OT", Pokémon words, the channel name) only adds to other evidence. Signals combine with diminishing returns and a stream is hidden only with a clear lead; undecided streams stay visible. Against the audited capture it hides 276 of 281 other-game streams (was 274) and no official stream, and keeps 86 of 92 official streams as Tibia (was 84). Hidden-stream reasons in the settings page name the evidence.
- Settings page: Twitch options are grouped into collapsible Ads and tracking, Video player, Page clutter and Tibia category sections, with the fansites in their own section; each shows how many switches are on. The section for the active tab (Tibia directory, fansite) opens automatically and the sections you open are remembered on this device.
- The Tibia filter and its metadata reader observe the page only on the Tibia directory and cache verdicts, instead of watching every Twitch page.

- Repository layout separates extension source/browser overrides, filter sources/generated lists, fansite research and Python/JavaScript tests. Subscription URLs now use `filters/lists/`; update existing subscriptions to the links in the README.

- Public setup instructions and subscriptions use the canonical `nesleykent/Tibia-Anti-Ad` repository.
- Documentation distinguishes the extension's title/tag filtering from offline thumbnail OCR and explains experimental fansite repairs.
- CI uses pinned actions, a bounded runtime and a Python compatibility matrix.

### Fixed

- The nag hider no longer clears the Tibia filter's marks when it starts, which could briefly show hidden streams again.

Live website preservation, cross-browser enforcement and Twitch ad-break behavior remain unverified. No stable release is declared by this change.
