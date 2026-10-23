# Rebuild ledger

## Milestone A: complete, waiting for annotation review

Done:

- Discarded the rejected f8833f9 rebuild with a normal Git revert, retaining public history. Discarded the uncommitted classifier test experiment. Original input captures and controls remain unchanged; unrelated existing untracked files were not included.
- Re-read original data instead of importing the rejected annotation overlay or model. Checked catalogue/project sources, protocol/launch examples, command ambiguity, spelling controls, Pokemon/idle projects and actual copied-world collisions.
- Prepared 221 records: 114 captured metadata rows, all 65 original controls, 7 initial user examples, 1 new maintainer-reported stream, 18 constructed contrasts and 16 language counterfactuals. Current targets: 121 private, 43 not-private, 57 lacking an established target. Two individual labels are maintainer-confirmed; 219 remain pending. Every source, reason, target/context distinction and historical-label disagreement is explicit.
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
- `research/twitch/rebuild/REVIEW.md`: complete human-readable review packet and source links.
- `research/twitch/rebuild/annotation-proposals.json`: proposed labels, contexts, exact provenance and approval flags.
- `research/twitch/rebuild/sources.json`: source manifest, hashes, coverage and limitations.
- `research/twitch/rebuild/catalogue-candidates.json`: automatically extracted candidate facts, unapproved.
- `research/twitch/rebuild/validate_review.py`: data/provenance checks only, no model code.
- `docs/TWITCH_MODEL.md`: points to the review gate and marks the restored model description as the baseline.
- Local source responses and preparation scripts remain in ignored `local/classifier-v2/`.

Exact next step:

**Stop. Ask the maintainer to review the proposed labels in REVIEW.md. Do not run any new training before that review.** Apply explicit corrections to this packet, then freeze approved labels and grouped separation before starting milestone B. Do not automatically treat approval of the process as approval of every unresolved target.

Remaining milestones:

- B: select/train the new private-evidence/context model and report held-out results. Stop with an updated ledger.
- C: Python/JS parity, complement percentage and hiding integration, browser checks, signed Safari update, commit/push. Stop with an updated ledger.

The installed Safari app was not changed during the data milestone. Reverting repository source is not installation of a new classifier. All three milestone changes must be committed and pushed directly to main without force-pushing.
