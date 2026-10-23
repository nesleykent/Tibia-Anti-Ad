# Twitch statistical filter, 1.3.0

The classifier learns from the complete stream title and all available tags together. Its statistical result directly decides `other`, `tibia` or `undetermined`. There are no manually banned names, server-domain rules, official-world overrides or channel features. Undetermined streams remain visible, and the existing Show/Hide corrections remain per broadcast.

## Inputs and model

The shared feature extractor normalizes Unicode and extracts words, adjacent word pairs and character 3/4/5-grams. Numerical runs become a generic number marker. Title and tag patterns share a learned feature space, so a pattern observed in tags can also contribute when it appears in a title. Character fragments carry one quarter of a whole-word feature's input weight, reducing reliance on partial resemblance. Tags are deduplicated and their ordering does not affect the result.

The trainer fits L2-normalized TF-IDF followed by balanced, regularized logistic regression (`C=4`, zero intercept). Only features observed in at least 2 training observations are retained. Each exported entry contains a learned coefficient multiplied by its effective IDF, and that effective IDF for normalization. Features are identified by FNV-1a keys; the model contains no raw titles or channel identifiers. Hashing is a representation choice, not an anonymization guarantee.

The browser and Python reference evaluate the same model without an ML runtime dependency. Positive logits of at least 2 hide a stream; logits of at most -2 classify it as Tibia. Intermediate scores abstain. Empty or entirely unrecognized inputs also abstain. The displayed percentage is the model's logistic estimate, not a calibrated guarantee of real-world correctness. Diagnostics separate the title and tag contributions; patterns present in both fields split their contribution equally without counting twice.

## Training and development evaluation

Training uses the existing audit's 373 labelled observations: 281 other-game streams and 92 official streams. The audit was produced with rules and manual review; it is limited supervision. Predictions from the filter's 562-stream capture are excluded from training. The source SHA-256 is recorded with the exported model. No screenshot examples or regression fixtures were added to training.

Five-fold development evaluation groups observations by channel. All feature selection, IDF fitting and model fitting occur within the training fold. The same channel split and decision cutoff apply to every input comparison:

| Inputs | Other games hidden, of 281 | Official streams hidden, of 92 | Undetermined, of 373 |
| --- | --- | --- | --- |
| Title and tags | 141 | 0 | 203 |
| Title only | 145 | 0 | 188 |
| Tags only | 105 | 2 | 256 |

These measurements demonstrate title use; they do not establish that adding tags always improves recall. At the chosen conservative cutoff, joint input hides 36 more other-game examples than tags alone and avoids its 2 official false positives. It still misses about half of the labelled other-game examples. No independent holdout, calibrated confidence or complete pirate-stream removal is claimed. The joint model's observation-level precision interval is 97.35% to 100% (95% Wilson); the data and design have been used during development, so this is not a production guarantee.

## Reproduce and verify

Training is optional and uses the pinned dependency in `tools/model-requirements.txt`, installed in an ignored local environment. Normal builds, repository checks and browser inference do not need scikit-learn.

```sh
python3 -m venv local/tibia-model-env
local/tibia-model-env/bin/python -m pip install -r tools/model-requirements.txt
PYTHONDONTWRITEBYTECODE=1 local/tibia-model-env/bin/python tools/train_tibia_model.py --write --report local/model-report.json
PYTHONDONTWRITEBYTECODE=1 python3 tools/twitch_evidence.py --write-js
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py
```

The statistical data format requires a matching classifier. Revision 2 rejects older cached rule-assisted data. Older extensions cannot consume this format and retain their last compatible data until the extension is updated. For later bundled changes, increment the evidence revision when older cached models must be superseded. Downloaded data never contains executable code.

Tests check numeric parity on the complete historical captures, both field contributions, neutral-model behavior, generalization of learned character fragments, channel independence, duplicate tags, official visibility controls and cache compatibility. Browser checks additionally change only the title with tags fixed, then change only the tags with the title fixed, and verify actual card visibility. Historical fixture verdicts describe the earlier heuristic; statistical inference may abstain on those other-game examples instead of forcing a name match.

Method references: [scikit-learn text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html), [logistic regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).
