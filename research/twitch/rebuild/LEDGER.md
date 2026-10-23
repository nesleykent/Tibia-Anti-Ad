# Rebuild ledger

## Milestone A: complete, waiting for annotation review

Done:

- Discarded the rejected f8833f9 rebuild with a normal Git revert, retaining public history. Discarded the uncommitted classifier test experiment. Original input captures and controls remain unchanged; unrelated existing untracked files were not included.
- Re-read original data instead of importing the rejected annotation overlay or model. Checked catalogue/project sources, protocol/launch examples, command ambiguity, spelling controls, Pokemon/idle projects and actual copied-world collisions.
- Prepared 220 pending proposals: 114 captured metadata rows, all 65 original controls, 7 user examples, 18 constructed contrasts and 16 language counterfactuals. Proposed targets: 107 private, 42 not-private, 71 lacking an established target. Every source, reason, target/context distinction and historical-label disagreement is explicit.
- Imported 50 first-page catalogue host/protocol facts automatically. No catalogue candidate or annotation is approved for training.

Results:

- Corrected the rejected report's data error: only 10 of the 487 titles in the 14:00 capture are accessibility prompts; 477 are other titles, with tags unavailable in this capture.
- Confirmed actual alias collisions: Antica/Antica Retro and Refugia/PixelOT. Official world identifiers must not become numerical officialness rewards.
- Distinguished primary private-server launch presentation from incidental advertising, known-private referents from current private sessions, and missing evidence from a false target label.
- The earlier Kalanta-as-OT assertion is explicitly disputed. 28 sampled historical assertions remain unverified rather than silently becoming negative labels.
- All 220 proposals and 50 catalogue facts pass provenance/schema validation, including exact original-source spans and hashes. No classifier training, calibration, model selection or new extension integration occurred in this milestone. Model-fitting repository tests are deferred until the approval gate; no full repository-test pass is claimed for this milestone.

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
