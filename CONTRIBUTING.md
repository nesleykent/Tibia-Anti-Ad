# Contributing

Write project documentation, code comments and issue reports in English. Original website labels may remain in their original language when quoted as evidence.

1. Open a research, false-positive or breakage issue with a specific page and reproducible steps.
2. Record browser/blocker versions, viewport, consent state, active lists and observation time. Redact sensitive data.
3. Prefer narrowly scoped network rules and plain CSS. Preserve content, navigation, forms, tools and accessibility. Never hide a broad parent merely because it contains an ad.
4. Add the smallest rule with evidence and label observed, simulated and assumed results separately. Userscripts require proof that ordinary filtering cannot solve the problem and an explanation of timing/side effects.
5. Rebuild bundles and run tests. Actual browser/blocker enforcement, desktop/mobile screenshots and functional checks are required before marking a site verified.
6. Keep assessments independent of popularity, affiliation or funding. Good practices do not earn ad exemptions.

For Twitch, prioritize precision over recall. Never infer OTServ from language, country or category alone. Do not add permanent channel blacklists from a single broadcast. Include correction and undo behavior in any future filtering UI.

Do not commit cookies, tokens, full personal session captures, copied website bundles or opaque archives. Generated lists are committed because users subscribe to their raw URLs. Keep CI read-only and dependency-light. Initial publication goes directly to `main` at the owner's request; contributors should submit reviewable pull requests.
