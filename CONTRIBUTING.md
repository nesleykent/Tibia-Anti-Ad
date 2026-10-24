# Contributing

Write project documentation, code comments and issue reports in English. Original website labels may remain in their original language when quoted as evidence.

1. Open a research, false-positive or breakage issue with a specific page and reproducible steps.
2. Record browser/blocker versions, viewport, consent state, active lists and observation time. Redact sensitive data.
3. Prefer narrowly scoped network rules and plain CSS. Preserve content, navigation, forms, tools and accessibility. Never hide a broad parent merely because it contains an ad.
4. Add the smallest rule with evidence and label observed, simulated and assumed results separately. Userscripts require proof that ordinary filtering cannot solve the problem and an explanation of timing/side effects.
5. Run `python3 tools/check_project.py` with Python 3.11+ and Node.js 22+. If it reports rebuilt stale artifacts, review them and rerun. Build Chrome with `python3 tools/build_chrome_extension.py`. Actual browser/blocker enforcement, desktop/mobile screenshots and functional checks are required before marking a site verified.
6. Keep assessments independent of popularity, affiliation or funding. Good practices do not earn ad exemptions.

For Twitch, prioritize precision over recall. Never infer OTServ from language, country or category alone. Do not add permanent channel blacklists from a single broadcast. Preserve the existing correction and undo behavior when changing filtering UI.

Do not commit cookies, tokens, full personal session captures, copied website bundles or opaque archives. Generated lists are committed because users subscribe to their raw URLs. Keep verification reproducible and dependency-light. GitHub Actions is disabled. Initial publication goes directly to `main` at the owner's request; contributors should submit reviewable pull requests.

## Workflow and shared principles

Read the [manifesto](MANIFESTO.md) and [Code of Conduct](CODE_OF_CONDUCT.md). The goal is browsing without advertising, including discreet ads, while preserving the community's useful content. Critique practices with evidence and treat people respectfully.

Fork the repository, make a focused branch and submit a pull request describing the player problem, resulting behavior, evidence and rollback. Add regression tests for behavior changes. Edit filter inputs and evidence sources rather than hand-editing generated files. The check command rebuilds website bundles, extension site rules and classifier evidence. Historical source hashes must not be updated to conceal unintended imported-file changes.

Before requesting review, update the changelog and relevant guides. Declare live behavior unverified when only mocks or offline tests were run. Maintainer review considers correctness, content preservation, privacy, clarity and reproducibility; passing automated checks alone does not certify browser behavior. See [release gates](docs/RELEASING.md).

New original contributions are submitted under the project's [MIT license](LICENSE). Keep third-party notices and disclose imported material and its license. Do not copy code or media with unknown redistribution rights into new contributions. Report vulnerabilities privately using [SECURITY.md](SECURITY.md).
