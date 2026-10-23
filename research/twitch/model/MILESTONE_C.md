# Milestone C: browser integration

Frozen model SHA-256: `55b7b0a019dd811895bf8388b3b2604ab8d419e9133482f38405fb9d1b5ccb50` (milestone B, commit `af6056a`). No fitting, label changes, calibration changes, alias changes or threshold tuning in C.

The browser now runs entity/context inference with the shared model, recognition patterns and normalization exported from Python. Revision 4 rejects the old cached format. Hiding uses P(private server) >=99%; the Safari percentage is 1-P(private server). No unknown/abstention state. Each diagnostic exposes references, feature contributions and the actual hidden state; per-broadcast Show overrides remain available.

Parity checks cover all 221 reviewed examples plus Unicode/context controls: exact reference spans, contributions, raw logit and hide decisions; probabilities agree to 15 decimal places across exponent implementations. Offline Chrome verification passed for metadata transport, command/sponsor acceptance, hiding, complement, disabling the filter and 1280/375-pixel layouts.

The personal Safari updater built, signed, verified and installed the app, retaining a rollback archive and verifying one registration per component. Safari was left running. Activation of that installation in Safari and persistence after quitting Safari are not established by signature/registration checks.

The first live capture is performed once with the actual unpacked extension in a fresh isolated Chrome Beta profile, using the same shared source. Its original metadata and results remain under ignored local/. The table contains every actually hidden stream and every shown stream with P(private server)>50%. It is unlabelled until maintainer review, so no false-positive/recall metric is claimed. No tuning on this capture is permitted before presenting it.

Live capture completed on 2026-10-23 at 16:53:32–16:53:51 UTC, Chrome 157.0.8103.6: **30 loaded cards, 26 actually hidden, 1 shown above 50%, 3 shown at the 1% base**. This is coverage of the loaded cards, not proof that the entire category was exhausted. No labels or model updates were derived from the capture. 1 exact title/tag inputs overlap the earlier reviewed material; they remain in the snapshot and are not counted as new independent examples. All 30 live outputs match Python reference spans, contributions, logit and decisions; largest probability difference is 0.

Capture SHA-256: `df4bdd9a28fc1dedbb1f2daa2fed92c8f39f143ab6a6dcfc1a1fe657a7f1594e`. Public-page metadata, full channel links/titles/tags and the requested 27-row table are retained locally; no raw capture or local/private artifact is committed. The unlabelled snapshot is ready for maintainer review.

Repository checks passed: 55 Python tests, JS checks and generated-asset verification. Browser verification and Safari signing/installation are recorded separately above. Stop here: do not tune on this first capture before review.
