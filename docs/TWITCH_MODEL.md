# Twitch private-server model, 1.5.0

Tibia Anti-Ad uses supervised probabilistic machine learning to estimate `P(private-server stream | full title, tags)`. Safari displays `1 - P(private-server stream | full title, tags)` as the Tibia percentage. Learned parameters determine every decision; no hand-maintained server blacklist, official-world override, channel identity or heuristic point total decides a card. Show/Hide corrections still apply only to the current broadcast.

## Inputs and inference

The shared extractor normalizes Unicode and extracts words, adjacent word pairs and character 3/4/5-grams. Numerical runs become a generic number marker. Title and tags share the same feature space, and duplicate patterns count once. Character fragments have one quarter of a word's input weight. Patterns learned in tags can also inform a title. Hash identifiers are a representation choice, not an anonymization guarantee.

The supervised presence model estimates each pattern's document-presence probability in the labelled private-server and official classes, using Jeffreys smoothing (`alpha=0.5`). Its learned coefficient is the log ratio of those probabilities. At inference it adds only coefficients for patterns actually present. It includes no absent-feature terms, no intercept and no input-length normalization. Thus a missing official reference contributes zero, and irrelevant patterns with zero learned weight cannot dilute an existing private-server signal. Unknown or empty text has neutral odds (50%) and remains undetermined.

A positive logistic scale is fitted to predictions from four inner folds separated by channel. Calibration uses balanced log loss and a small regularizer; a zero intercept preserves neutral odds without evidence. The exported coefficients already include this scale. Evaluation holds out a separate outer fold, so calibration never sees its labels. The displayed estimate uses equal class priors; it is not a measured prevalence or a guarantee of accuracy on Twitch. Correlated text patterns, weak labels and distribution shifts remain limitations. [Calibration methodology and limits](https://scikit-learn.org/stable/modules/calibration.html).

Automatic hiding requires at least 98% estimated private-server probability, equivalent to at most 2% in the displayed complement. The stricter decision cutoff preserves the existing official and ambiguous-text visibility controls while the new model improves detection. A low displayed estimate above 2% can therefore remain visible. Show overrides and paused settings also preserve visibility. This cutoff is a decision policy, not a claim of 98% precision. The model classifies official evidence at the symmetric boundary; intermediate results abstain. Score and cutoff remain separate.

`piracy-presence-logit-v1` stores signed learned coefficients with neutral bias. Python and JavaScript implement identical inference without an ML runtime dependency. The earlier `joint-text-logistic-v1` reader remains supported for compatible fixtures; bundled revision 3 rejects cached revision 2 models. Older extensions reject the new model format and keep their last compatible data until updated.

## Training and development evaluation

Training uses 370 labelled observations from the existing audit: 278 private-server streams and 92 official streams. Three unrelated-game observations were removed from the positive class; an unrelated game is not a piracy label. Ambiguous or unverified observations are not turned into negative labels. The audit was produced mostly with rules and review, so its supervision is limited. Predictions from the filter's 562-stream capture, user screenshots and regression fixtures are excluded from training. The source SHA-256 and class definition are recorded with the exported model.

Five-fold development evaluation groups observations by channel. Presence counts and inner calibration are fitted only within each training fold. The same channel split and decision cutoff apply to every input comparison:

| Inputs | Private streams hidden, of 278 | Official streams hidden, of 92 | Undetermined, of 370 |
| --- | --- | --- | --- |
| Title and tags | 196 | 0 | 97 |
| Title only | 234 | 0 | 58 |
| Tags only | 61 | 0 | 304 |

On the same 370 labels and outer channel folds, the previous model with its previous cutoff hid 147 of 278 private-server examples and zero official examples. The new model and its 98% cutoff hide 196 private-server examples and zero of 92 official examples. Brier loss decreased from 0.0461 to 0.0345 and log loss from 0.2002 to 0.1102; these proper scores assess both discrimination and probability quality, not calibration alone. The new observation-level precision interval is 98.08% to 100% (95% Wilson). These are development comparisons, not an independent holdout or a production guarantee. They do not establish that adding tags always improves recall. The model still misses 82 of the 278 labelled private streams at its applied cutoff.

## Reproduce and verify

Training and inference now use the Python standard library. The pinned scikit-learn environment in `tools/model-requirements.txt` is retained for reproducing the historical logistic baseline, not required to train the current presence model.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/train_tibia_model.py --write --report local/model-report.json
PYTHONDONTWRITEBYTECODE=1 python3 tools/twitch_evidence.py --write-js
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py
```

For later bundled changes, increment the evidence revision when older cached models must be superseded. Downloaded data never contains executable code.

Tests check numeric parity on the complete historical captures, both field contributions, neutral-model behavior, generalization of learned character fragments, channel independence, duplicate tags, official visibility controls and cache compatibility. Browser checks additionally change only the title with tags fixed, then change only the tags with the title fixed, and verify actual card visibility. Historical fixture verdicts describe the earlier heuristic; statistical inference may abstain on those other-game examples instead of forcing a name match.

Method references: [scikit-learn text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html), [logistic regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).
