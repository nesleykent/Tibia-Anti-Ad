# Rebuild ledger

## Milestone A: reviewed labels recorded; data enrichment remains

Done:

- Discarded the rejected f8833f9 rebuild with a normal Git revert, retaining public history. Discarded the uncommitted classifier test experiment. Original input captures and controls remain unchanged; unrelated existing untracked files were not included.
- Re-read original data instead of importing the rejected annotation overlay or model. Checked catalogue/project sources, protocol/launch examples, command ambiguity, spelling controls, Pokemon/idle projects and actual copied-world collisions.
- Prepared 221 records: 114 captured metadata rows, all 65 original controls, 7 initial user examples, 1 new maintainer-reported stream, 18 constructed contrasts and 16 language counterfactuals. Current targets: 121 private, 43 not-private, 57 lacking an established target. Two individual labels are maintainer-confirmed; 89 explicit-project private records are now bulk-approved and 130 remain pending. Every source, reason, target/context distinction and historical-label disagreement is explicit.
- Imported 50 first-page catalogue host/protocol facts automatically. No catalogue candidate or annotation is approved for training.

Results:

- Corrected the rejected report's data error: only 10 of the 487 titles in the 14:00 capture are accessibility prompts; 477 are other titles, with tags unavailable in this capture.
- Confirmed actual alias collisions: Antica/Antica Retro and Refugia/PixelOT. Official world identifiers must not become numerical officialness rewards.
- Distinguished primary private-server launch presentation from incidental advertising, known-private referents from current private sessions, and missing evidence from a false target label.
- The earlier Kalanta-as-OT assertion is explicitly disputed. 19 sampled historical assertions remain unverified rather than silently becoming negative labels.
- All 221 records and 50 catalogue facts pass provenance/schema validation, including exact original-source spans and hashes. No classifier training, calibration, model selection or new extension integration occurred in this milestone. Model-fitting repository tests are deferred until the approval gate; no full repository-test pass is claimed for this milestone.

Maintainer review update, 2026-10-23:

- `raw1400:16`: corrected from missing target/unresolved context to private/session/affirmative=True, exactly as the maintainer requested. The original captured input and previous proposal are preserved; the maintainer edit in REVIEW.md is incorporated.
- `maintainer-example:0`: exact sponsor-list title supplied by the maintainer, explicitly labelled original-server. The RubinOT mention is secondary promotion; no official-world identifiers are needed to make it a negative private example.
- Reviewed 13 analogous command-based proposals for consistency. Their revisions remain pending, are individually logged with previous labels/rationales, and are not represented as maintainer-confirmed individual session facts.
- Paired the two directly reviewed inputs in one contrast group. No command-count rule, per-channel rule, model training or integration was added.
- Do not rerun the initial local packet preparers: the reviewed JSON and revision histories are now the source of truth. Use the validator to check them.

Files changed:

- Revert of the rejected rebuild's runtime/model/report/test changes back to the pre-rebuild baseline.
- `research/twitch/rebuild/REVIEW.md`: compact 4-column review queue; prior full packet archived in ANNOTATION_BACKGROUND.md.
- `research/twitch/rebuild/review-queue.json`: exact grouping, 89 bulk approvals and one deferred historical no-evidence positive.
- `research/twitch/rebuild/DATA_GAP.md`: real-context counts and proposed additional capture before B.
- `research/twitch/rebuild/annotation-proposals.json`: proposed labels, contexts, exact provenance and approval flags.
- `research/twitch/rebuild/sources.json`: source manifest, hashes, coverage and limitations.
- `research/twitch/rebuild/catalogue-candidates.json`: automatically extracted candidate facts, unapproved.
- `research/twitch/rebuild/validate_review.py`: data/provenance checks only, no model code.
- `docs/TWITCH_MODEL.md`: points to the review gate and marks the restored model description as the baseline.
- Local source responses and preparation scripts remain in ignored `local/classifier-v2/`.

Exact next step:

**Stop at A. Await review only of the compact queue in REVIEW.md and collect the missing real sponsorship negatives before B. Do not run any new training before review.** Apply explicit corrections to this packet, then freeze approved labels and grouped separation before starting milestone B. Do not automatically treat approval of the process as approval of every unresolved target.

Remaining milestones:

- B: select/train the new private-evidence/context model and report held-out results. Stop with an updated ledger.
- C: Python/JS parity, complement percentage and hiding integration, browser checks, signed Safari update, commit/push. Stop with an updated ledger.

The installed Safari app was not changed during the data milestone. Reverting repository source is not installation of a new classifier. All three milestone changes must be committed and pushed directly to main without force-pushing.

Compact review update, 2026-10-23:

- Done: replaced the 219-pending-row review burden with one ordered 4-column table: 122 groups cover 131 requested records (57 missing targets, 43 not-private, 18 command-based private and 13 spelling/format-variant private). Two already-confirmed examples remain marked for reference. Exact duplicates and language-only children are grouped.
- Results: 89 explicit-project private records bulk-approved under the maintainer instruction, preserving all targets/reasons and training gates. audit:7 has no observable private identifier, stays deferred/pending, and is excluded from the bulk approval.
- Data gap: 115 real records, 107 identified channels; 14 promotion records comprise 13 proposed private primary presentations and only 1 confirmed original-session sponsorship negative. No natural negation; the lone natural comparison is against monsters. Insufficient to learn session vs sponsorship reliably.
- Next: review the compact queue, gather independently verified real sponsorship-list negatives and matched session-command positives, then return with the new annotations before any model fitting. Proposed initial enrichment: 50 of each, with negative examples from at least 30 channels over at least 3 days. Reserve a separate natural sample for calibration/testing.
- Files: REVIEW.md, ANNOTATION_BACKGROUND.md, review-queue.json, DATA_GAP.md, annotation-proposals.json, sources.json, validate_review.py, LEDGER.md. No runtime/model/extension changes.

Context acceptance update:

- Recorded the maintainer's exact session-command title and the full confirmed sponsor-list title in `tests/data/tibia-private-context-acceptance.json`. Same `!rubinot`, opposite required probability behavior; no fixed per-term contribution is acceptable.
- Added `check_context_acceptance.py`, an executable output checker for each future runtime. Acceptance bounds: session >=95%, sponsorship <=5%. These are test bounds, not hiding thresholds or measured calibration. Fixtures remain outside training and held-out metrics. No classifier acceptance pass is claimed yet.
- Next B/C verification must run actual inference on these exact title/tag inputs and pass the checker independently for Python and JS. No fit or runtime changes made now.

Round 2 review and channel correction, 2026-10-23:

- Done: applied the private command/variant and not-private block approvals. Recorded 9 new private adjudications from missing targets, 4 new not-private adjudications plus the latest audit:155 correction to not-private. Eldrius (audit:132) corrected to private from the maintainer reply. Source inputs, original labels and every superseded proposal remain intact.
- Results: 131 proposed private session targets, 47 not-private, 43 missing historical session targets. Approvals: 159 bulk, 17 individually confirmed, 33 baseline-confirmed, 12 with historical/scope decisions pending. Missing historical targets do not mean missing supervision: all 43 get no-private-evidence target 0 and required P(private)=1%. audit:7 also gets that baseline supervision rather than a positive loss from its historical asserted private label. All 44 must remain in dataset/split accounting.
- audit:155: maintainer inspected https://www.twitch.tv/adaismad and says it appears to be original Tibia. Latest not-private adjudication supersedes the intermediate private suggestion. A misspelling by itself is not OT evidence.
- Data gap: 115 real examples; session83, promotion15, no-evidence8, unresolved8, comparison1, negation0. Only 2 real confirmed original-session sponsorship-list negatives (baratuca and audit:42). Enrichment before B is still required.
- Scope: Project Zomboid hiding remains unresolved; the reply identifying Eldrius as OT is not silently applied to Project Zomboid. Ten listed ambiguous session targets remain absent, with the mandatory 1% behavior already specified. Do not repeatedly ask for the approved blocks.
- Files: annotation-proposals.json, sources.json, review-queue.json, REVIEW.md, DATA_GAP.md, validate_review.py, check_context_acceptance.py, tests/data/tibia-no-private-evidence-acceptance.json and this ledger. The acceptance checker now covers the 2 context contrasts and 44 baseline cases.
- Validation: provenance, original hashes/spans, approvals, baseline retention contract, fixture/output checker synthetic self-checks, Python syntax and diff hygiene. No new model inference, fit, calibration, extension integration or browser verification. Full repository tests that fit models remain deferred at the pre-training gate; no full-check pass is claimed.
- Exact next step: retain the reviewed packet, complete real sponsorship-negative capture/annotation preparation and settle the remaining Project Zomboid scope. Review new captured annotations before any fitting. At B, use explicit no-private-evidence supervision rather than filtering missing historical targets; verify actual outputs for all 46 acceptance cases and use disjoint held-out data for metrics.

Channel links update:

- Added source-backed Twitch channel URLs directly to the compact consultation table, including adaismad/audit:155. Historical capture titles are distinguished from the channel's present live content. No VOD identity or current live status is invented.
- Machine-readable review groups now retain channel/url and source index for each available capture link. Constructed examples without a real source channel remain marked as tests. Approved rows are consultation-only, not a new approval request.
