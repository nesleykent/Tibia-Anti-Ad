# Browser compatibility

Syntax compatibility is a target, not a certification of runtime behavior.

| Target | Intended input | This release's evidence |
| --- | --- | --- |
| Firefox / uBlock Origin | Portable or extended bundle | Build checks only; no real extension test |
| Chrome / uBlock Origin Lite | Portable bundle; import depends on installed version | Supplied Chromium CSS injection/network simulations; no extension-enforcement verification |
| Safari / supported blocker | Portable rules accepted by that blocker | Supplied reports include partial Safari feedback and network-rule uncertainty; not certified |

Portable output removes `:has()` selectors. It contains no scriptlets, redirects, CSP modifications, `:style()`, `:remove()` or `:has-text()`. Extended output retains observed or explicitly speculative parent selectors from source files. Both outputs restrict network filtering to the source website; neither supplies a native Safari JSON ruleset or a Chrome extension ruleset.

Some historical source headers claim broader compatibility than their evidence supports. This matrix and the installation guide take precedence for the release. Safari observations cannot be generalized to all Safari/blocker versions. Hiding cookie or recovery interfaces does not choose consent settings, and may leave scroll-lock behavior; report this as breakage.

Official references, consulted 2026-10-21:
- [uBlock Origin static-filter syntax](https://github.com/gorhill/uBlock/wiki/Static-filter-syntax)
- [uBO Lite project and documentation](https://github.com/uBlockOrigin/uBOL-home)
- [Safari user-filter discussion](https://github.com/uBlockOrigin/uBOL-home/discussions/372)
