# Tibia Anti-Ad project specification

## Objective and principles
Identify, block and neutralize advertising, tracking and navigation interference in services used by the Tibia community. The [manifesto](../MANIFESTO.md) establishes the project’s player-first mission; the goal includes advertising regardless of how intrusive it is. The player experience takes priority over monetization. Recognizing good practices never grants advertising immunity.

## Capabilities and delivery order
| Module | Responsibility | Depends on |
| --- | --- | --- |
| website-research | Evidence and functional baselines for fansites, wikis, calculators, maps, databases, market tools and community portals | — |
| filters | Site-scoped network and cosmetic rules; optional narrowly scoped repairs | website-research |
| assessments | Four separate evidence-backed dimensions and positive examples | website-research |
| twitch | Platform ad research and conservative Tibia/OTServ/undetermined classification | — |

Initial repository scope: preserve supplied research, publish experimental filter inputs and reproducible bundles, establish assessment methodology, provide a conservative offline text-classification prototype and track unimplemented live capabilities. Creating this project is not equivalent to completing its research program.

## Structure and commands
- `filters/sources/sites/`: experimental per-site inputs, scoped by the build before installation.
- `filters/lists/anti-ad-tibia*.txt`: generated experimental subscriptions.
- `research/`: supplied reports and scripts, not newly verified evidence.
- `docs/`: installation, methodology, compatibility, Twitch policy and roadmap.
- `extension/`: supplied Safari extension source.
- `scripts/twitch/`: standalone live-video ad script and setup.
- `tools/`: Python 3.11+ standard-library utilities; no external runtime dependencies.
- Build: `python3 tools/build_filters.py`
- Full checks: `python3 tools/check_project.py` (Python 3.11+ and Node.js 22+)
- Classify: `python3 tools/classify_streams.py path/to/streams.json`

Use small functions, explicit output fields and deterministic UTF-8 output. Example: `{"classification": "undetermined", "hide": false}`. No implicit language-based inference or remote requests.

## Acceptance checklist
- English public-facing repository, README and contribution workflow.
- Original local file bytes are preserved under `local/legacy/`; ZIPs and local artifacts are not published.
- Inputs and historical verification claims retain provenance and limitations.
- Every generated network rule is restricted to its source site.
- Known content-destruction risks are excluded from generated bundles.
- Portable bundle omits procedural/parent selectors; advanced bundle is separate.
- Installation distinguishes Safari, Chrome and Firefox and includes rollback.
- Assessments require dated evidence for intrusiveness, tracking, performance and usability; unknown measurements remain unknown.
- Twitch precision takes priority: ambiguous, conflicting and language-only cases stay visible; live integration remains tracked work.
- Tests verify scope, exclusions, deterministic build and conservative classifications.
- Commit and push directly to GitHub `main`, then verify the remote commit.

## Boundaries and verification
Always preserve navigation, content, tools and accessibility. Never publish fabricated ratings, screenshots, performance measurements or live-browser compatibility claims. Never whitelist ads as a reward. No secrets, session dumps or unreviewed archives. External dependencies and browser installation require separate justification. Run unit and artifact checks before publication. Browser-level acceptance requires actual extension enforcement on desktop/mobile home and deep pages; supplied CSS-injection reports do not satisfy that acceptance.

## Repository quality acceptance

- Preserve the full supplied manifesto and link its principles to contributor and release criteria.
- Use the canonical public repository URL; document experimental status without promising production readiness.
- Provide licensing, imported-material attribution, security reporting, conduct and contributor review guidance.
- Check maintained local documentation links, JavaScript syntax, Python/Node behavior, offline evaluation, Chrome package resources and deterministic generated output through the repository verification command.
- GitHub Actions is disabled. Publish verified packages with license notices through the maintainer account.
- Verify the published main commit and its check results. Record remaining live browser and asset-rights gates before declaring a stable release.
