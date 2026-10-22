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

- Repository layout separates extension source/browser overrides, filter sources/generated lists, fansite research and Python/JavaScript tests. Subscription URLs now use `filters/lists/`; update existing subscriptions to the links in the README.

- Public setup instructions and subscriptions use the canonical `nesleykent/Tibia-Anti-Ad` repository.
- Documentation distinguishes the extension's title/tag filtering from offline thumbnail OCR and explains experimental fansite repairs.
- CI uses pinned actions, a bounded runtime and a Python compatibility matrix.

Live website preservation, cross-browser enforcement and Twitch ad-break behavior remain unverified. No stable release is declared by this change.
