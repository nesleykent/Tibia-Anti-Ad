# Twitch server-identity model, 1.6.0

The classifier estimates whether a Tibia-category stream is non-official, including private servers and unrelated games. A supervised logistic regression consumes six explicit identity feature types. A sigmoid calibrator is fitted on separate channels. A separate decision policy can abstain. The JSON artifact is the source of truth for feature definitions, recognized identities, coefficients, thresholds and calibration metadata; Python and JavaScript implement the same operation order and six-decimal output contract.

There is no image input, image fetching, image text extraction, channel feature or channel decision table. Historical captures and their original labels are preserved as evidence, not executed. Existing broadcast-specific Show overrides remain independent of the classifier.

## Research findings and why the previous rebuild failed

The old model had 16,000+ hashed word, bigram and character-fragment coefficients, estimated independently from noisy audit labels. Presence-only scoring prevented absence terms, but did not prevent irrelevant *present* features from acquiring class correlations. `Português` alone received 61% non-official probability; `hunt bosses` alone received 3%, and together 5%. All should be irrelevant to server identity. The failure is shortcut learning, not a missing stopword. Changing the label author to an LLM cannot eliminate correlations or annotation errors; the corpus does not record enough provenance to attribute the earlier LLM's reasoning.

[Gururangan et al., 2018](https://aclanthology.org/N18-2017/) demonstrate that annotation artifacts let text classifiers exploit unintended superficial cues. That is evidence for restricting admissible information here, not evidence that an unrestricted embedding model will fix the labels. Character fragments also multiply correlated evidence and transfer confidence to unrelated words. The new model has no word/subword discovery, so neutral text cannot enter its feature vector regardless of its association with a label. Regression tests enforce identical scores as well as verdicts under language, gameplay and command additions.

The data audit also found:

- The 456-row historical audit was produced with rules and review, not independent observation of each active game. Commands were repeatedly treated as server declarations. One row records explicit user confirmation; this is a training label, never a deployed channel decision.
- The 487-row 14:00 capture contains Twitch accessibility prompts instead of usable titles. It is not training or evaluation data.
- The 114-row 20:15 capture has titles without tags and historical image-assisted verdicts. The 562-row 21:15 capture has richer metadata, but its verdicts came from an earlier filter and were used to tune that filter. Neither is independent truth. Their metadata is used for Python/JS parity and before/after comparison only.
- The 65 historical controls mix truth claims, desired actions, spelling assumptions and image-only expectations. They are regression controls, not training or accuracy data.
- Audit row 448 calls Kalanta an OTServer. The independently fetched official-world roster includes Kalanta. Other overlooked official-world tags and contradictory identities are recorded explicitly.

Every binary-label disagreement and revised historical expected action is listed in [the annotation report](../research/twitch/model/ANNOTATIONS.md). Original files and their provenance remain unchanged. [label-audit.json](../research/twitch/model/label-audit.json) records all 456 reviews, including retained and unresolved labels; [case-audit.json](../research/twitch/model/case-audit.json) records all 65 controls. There are 27 binary-label disagreements and 35 expected-action disagreements. A correct abstention on an unsupported spelling does not assert that the actual game is official.

## Identity ontology and model choices

The ontology is deliberately small and interpretable. Official-world names come from the [TibiaData v4 roster](https://api.tibiadata.com/v4/worlds), retrieved on 2026-10-23, with its response hash recorded in the artifact. CipSoft's own world page could not be fetched, so this is a third-party roster, not a claim of independent CipSoft verification. The roster is frozen for reproducibility and will need maintenance when worlds merge or launch. Historical labels can refer to retired worlds which this roster no longer recognizes.

Other recognized identities are RubinOT, PokeAlliance/PKA, PokeXGames/PXG, DeusOT/DeusOld, Baiak Idle and Medivia. [RubinOT's own site](https://rubinot.com.br/news), [PokeAlliance's site](https://pokealliance.com/), [PXG's own wiki](https://wiki.pokexgames.com/P%C3%A1gina_principal), [DeusOT's site](https://deusot.com/) and [Medivia's site](https://medivia.online/) establish separate games/operators. Baiak Idle's operator site returned 403; its identity rests on the repeated explicit Baiak Idle declarations in the historical audit, so its provenance is weaker. Names outside this ontology, including many real private servers, remain unrecognized. No assumption of official Tibia follows from a missing private-server match.

The design decisions are:

| Decision | Evidence and consequence |
| --- | --- |
| Six identity feature types rather than arbitrary text | The observed language/gameplay shortcut requires a structural information restriction, not another relabelling pass. There are only 213 fitting labels. |
| Separate title and tag features | Captures contain stale, conflicting and promotional tags. Whole-tag equality prevents a tag such as `rubinotfan` from matching a server. |
| Exact bounded names, Unicode decomposition and accent removal | Captures contain stylized text. Exact matching preserves identities without guessing new server names from shared fragments. Misspellings and spaced obfuscation deliberately abstain. |
| Ignore chat commands before feature extraction | Earlier audit evidence itself admits commands can be promotional. `!rubinot`, `!pix` and other commands alone cannot establish active gameplay. |
| Explicit official declarations; exclude bare `Tibia` and `global` | Both appear in private-server metadata. Even `tibiaglobal` conflicts with direct private-server titles in several captures. |
| Common-word worlds such as Dia/Bona/Premia recognized only as whole tags | Ordinary title words can be unrelated to server identity. This sacrifices title coverage. |
| One binary presence value per feature type | Repeated names or many tags must not manufacture extra independent evidence. Matching several terms within one type contributes its coefficient once. |
| Supervised six-variable logistic regression with weak L2 | Compact, convex, explainable and dependency-free. Joint fitting avoids the old independent n-gram likelihood accumulation. L2=0.01 penalizes the sum loss, with no class balancing. Constants were fixed before held-out metrics. |
| Disjoint-group sigmoid calibration | [Guo et al., 2017](https://proceedings.mlr.press/v70/guo17a.html) motivate post-hoc calibration on held-out data. Here a two-parameter sigmoid has L2=0.1 on its slope to remain finite with small, nearly separable samples. It uses empirical prevalence, not artificial equal priors. |
| No identity, conflicting official/other identities, negation/comparison/temporal context: abstain | The data cannot establish which game is active from these cases. [El-Yaniv and Wiener, 2010](https://www.jmlr.org/beta/papers/v11/el-yaniv10a.html) formalize exchanging coverage for lower selective risk. The conservative context detector is limited, not multilingual semantic understanding. |
| Hide at P(other) >= 0.98; official attribution at <= 0.10 | The existing 98% policy expresses a 49:1 false-hide/missed-other cost ratio under a calibrated binary decision model. The user gives the direction, not an exact monetary ratio. These are policy choices fixed before evaluation, not optimized or guaranteed precision. Both abstention and official verdicts remain visible. |

`P(other) = sigmoid(bias + sum(present calibrated coefficients))`. The sigmoid intercept and slope are absorbed into the exported bias and weights. Neutral text contributes exactly zero. Without identity features the displayed estimate is the fitted sampled base rate, about 87.4% other, and **the verdict is always undetermined**. That base rate is not evidence that a particular unidentified stream is non-official. The high sampled prevalence makes that distinction essential. Safari's complement is an estimate under these proxy labels, not a p-value, factual observation or guarantee.

Explanations expose each matched identity, source field, feature type and signed contribution, along with the bias, logit, probabilities and abstention reason. A generic text phrase is never presented as a contributing signal.

## Dataset and separation

All supervision comes from the original 456-row audit plus the explicit annotation overlay. No filter predictions, image-derived verdicts or synthetic controls are training labels. Reviewed composition is 93 official, 260 other and 103 unresolved. Other includes the three unrelated-game rows, correcting the previous target mismatch. Unresolved observations do not become negatives.

A frozen SHA-256 split assigns channel/exact-metadata groups before fitting: 3 buckets for training, 1 calibration, 1 test. Duplicate metadata and repeated channels stay together. The splitter is deterministic, not repeatedly seeded to find a favorable result. [split.json](../research/twitch/model/split.json) records every assignment.

| Partition | Official | Other | Unresolved, excluded from fitting and binary metrics |
| --- | ---: | ---: | ---: |
| Training | 56 | 157 | 55 |
| Calibration | 20 | 53 | 24 |
| Held-out test | 17 | 50 | 24 |

The exported model is fitted on the 213 training observations and calibrated on the 73 calibration observations. **It is not refitted on test or calibration labels after evaluation.** The 67 labelled test observations are not used for coefficient fitting, calibration or threshold selection. These are retrospective same-day holdouts from a previously inspected corpus, not a prospective unseen-day test. Ontology/annotation review used the corpus, so these results do not establish generalization to unseen games or independently verified active gameplay.

## Held-out results

[evaluation.json](../research/twitch/model/evaluation.json) includes test row IDs, individual predictions, the confusion matrix, reliability bins and the uncalibrated comparison.

| Measurement | Held-out result |
| --- | ---: |
| Official streams hidden | **0 / 17** |
| Non-official streams hidden | **42 / 50 (84%)** |
| Precision among hidden labelled streams | 42 / 42 (100% observed) |
| Official verdicts | 15, all labelled official |
| Abstention | 10 / 67 (14.93%): 2 official, 8 other |
| Coverage | 85.07% |
| Error among non-abstained labelled predictions | 0 / 57 |
| Brier score | 0.02446 |
| Log loss | 0.07609 |
| ECE, five fixed equal-width bins | 0.01301 |

The 95% Wilson interval for official false-hiding rate is **0% to 18.43%**. Zero observed errors in 17 official examples is weak evidence of future safety, not a zero-risk guarantee.

Calibration is evaluated on every labelled test row, including abstentions. Occupied reliability bins: 15 predictions below 0.2 average 0.00054 other probability with 0 observed other; 52 predictions at least 0.8 average 0.97815 with 0.96154 observed other. Middle bins are empty, so ECE alone is insufficient. Uncalibrated Brier/log loss/ECE are **0.02378 / 0.07384 / 0.00897**, slightly better than calibrated values. Calibration was fitted separately as required; this small holdout does **not** show calibration improvement, and no test-based calibration selection or refit was performed.

The 24 unresolved test rows are reported separately: 21 undetermined, 1 official, 2 other. The hidden unresolved rows, `audit:279` (stralavento) and `audit:381` (spectralmagin), name multiple non-official games but have no verified active-game label. `audit:218` (lirryk) mentions an official world plus an unrecognized private-server domain and receives an official verdict. This is a known ontology limit; none of these rows contributes to the claimed 0/17 or 42/50 metrics. The all-row test abstention rate is 31/91 (34.07%).

## Highest-weighted signals

All numbers are learned calibrated log-odds contributions, applied once per type. These are semantic feature weights, not independently learned scores for each server.

| Side | Signal | Coefficient | Example matches |
| --- | --- | ---: | --- |
| Official | Official world in title | **-9.52933** | Antica, Kalanta, Ferobra, Quintera |
| Official | Official world as whole tag | -7.73804 | Serdebra, Floribra, Quidera |
| Official | Explicit official declaration in title | -7.00104 | Tibia Global, official Tibia |
| Official | Explicit official declaration as tag | -4.67734 | tibiaglobal, cipsoft |
| Other | Named other server/game in title | **+6.90452** | RubinOT, PokeAlliance, PXG, DeusOT |
| Other | Named other server/game as whole tag | +6.46235 | rubinot, pka, baiakidle |

Português, other languages, hunt, bosses, levels, drops, shiny, chat commands and channel names have no coefficients. Regression tests also cover neutral additions to already classified inputs, repeated signals, tag order, no subword matches, conflicts and the corrected Kalanta case.

## Changed audit streams and verification

[verdict-changes.json](../research/twitch/model/verdict-changes.json) lists **every changed stream**, with public channel, capture row, previous/current verdict, explanation and matched signals. It compares against the bundled revision 3 model at the start of this rebuild, not the old rule/image verdicts: 120 changes in the 456-row audit, 42 in the 114-row capture and 135 in the 562-row capture, 297 total. Across captures, 156 move other to undetermined, 44 undetermined to other, 80 official to undetermined, 15 undetermined to official and 2 official to other. The last two are darianzin (`live-2115:83`, explicit DeusOT) and soyimsa (`live-2115:187`, explicit RubinOT); the live capture has no independent truth labels, so these changes are not counted as accuracy improvements.

Python and JavaScript full verdicts, explanations, probabilities, matched terms and contributions match exactly at the public six-decimal precision over all three captures, 65 controls and Unicode/command edge cases. Unsupported old formats and stale cached revisions fail closed. Older installed extension code cannot interpret the new artifact and must be updated; the rule download URL is unchanged.

Reproduce without new dependencies:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/train_tibia_model.py --write --report local/model-report.json
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py
```

This reproduces the frozen experiment, not a fresh independent evaluation. Record browser behavior separately from repository checks and native signing. Historical untracked originals, local captures, full browser outputs and the concise continuation ledger stay under ignored `local/`.
