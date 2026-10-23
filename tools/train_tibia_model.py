"""Learn piracy-presence likelihoods and cross-fitted logistic calibration.

Only labelled private-server/official observations supervise the model. Absent
features contribute nothing; unknown text has neutral odds. Calibration folds
are separated by channel, inside each development evaluation training fold.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

from twitch_evidence import AUDIT, AUDIT_OTHER, AUDIT_TIBIA, EVIDENCE
from tibia_text import features

# High-confidence automatic hiding; intermediate estimates remain visible.
THRESHOLD = math.log(0.98 / 0.02)
ALPHA = 0.5
CALIBRATION_FOLDS = 4


def observations():
    result = []
    for row in json.loads(AUDIT.read_text())["classificacao"]:
        label = 1 if row["categoria"] in AUDIT_OTHER else 0 if row["categoria"] in AUDIT_TIBIA else None
        if label is not None:
            result.append({"channel": row["canal"], "title": row["titulo_original"],
                           "tags": [t.strip() for t in row["tags_originais"].split("|") if t.strip()], "label": label})
    return result


def dataset(mode="both"):
    return {row["channel"]: (features(row["title"] if mode != "tags" else "",
                                     row["tags"] if mode != "title" else []), row["label"])
            for row in observations()}


def train(rows):
    """Smoothed class-conditional document presence, with no absence terms.

    Jeffreys smoothing regularizes rare patterns. Each word/phrase/fragment is
    counted once per observation, independently of text length or repetition.
    The zero log prior represents an equal-prior binary comparison.
    """
    counts = [collections.Counter(), collections.Counter()]
    totals = [0, 0]
    factors = {}
    for values, label in rows:
        totals[label] += 1
        counts[label].update(values.keys())
        factors.update(values)
    if not all(totals):
        raise ValueError("Both labelled classes are required")
    weights = {}
    for key in sorted(factors):
        present = [(counts[label][key] + ALPHA) / (totals[label] + 2 * ALPHA) for label in (0, 1)]
        weight = math.log(present[1] / present[0]) * factors[key]
        weights[key] = [round(weight, 8), 1]
    return {"format": "piracy-presence-logit-v1", "bias": 0, "threshold": THRESHOLD, "weights": weights}


def score(model, feats):
    known = sorted(set(feats) & model["weights"].keys())
    return math.fsum(model["weights"][key][0] for key in known)


def partitions(rows, folds):
    # Prefixes distinguish captures, not independent channels.
    channel = lambda key: key.removeprefix("live:").casefold()
    assignment = {name: i % folds for i, name in enumerate(sorted({channel(key) for key in rows}))}
    for fold in range(folds):
        yield ({key: value for key, value in rows.items() if assignment[channel(key)] != fold},
               {key: value for key, value in rows.items() if assignment[channel(key)] == fold})


def calibration_slope(results):
    """Fit a positive, zero-intercept logistic scale to held-out predictions.

    Balanced loss corresponds to the model's equal class priors. A small L2
    penalty around scale 1 gives finite estimates even on separable folds.
    The derivative is monotone, so bisection finds its constrained minimum.
    """
    totals = collections.Counter(label for _, label in results)
    if not totals[0] or not totals[1]:
        raise ValueError("Calibration requires both classes")
    def gradient(slope):
        total = 0
        for logit, label in results:
            probability = 1 / (1 + math.exp(-max(-40, min(40, slope * logit))))
            total += logit * (probability - label) / (2 * totals[label])
        return total + 0.001 * (slope - 1)
    if gradient(0) >= 0:
        return 0.0
    low, high = 0.0, 1.0
    while gradient(high) < 0:
        high *= 2
    for _ in range(70):
        middle = (low + high) / 2
        if gradient(middle) < 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def fit(rows):
    calibration = []
    for training, test in partitions(rows, CALIBRATION_FOLDS):
        fitted = train(list(training.values()))
        calibration.extend((score(fitted, values), label) for values, label in test.values())
    slope = calibration_slope(calibration)
    model = train(list(rows.values()))
    for value in model["weights"].values():
        value[0] = round(value[0] * slope, 8)
    model["calibration"] = {"method": "channel-cross-fitted-zero-intercept-logistic", "folds": CALIBRATION_FOLDS,
                            "slope": round(slope, 8), "class_prior": "equal"}
    return model


def wilson_interval(successes, total):
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0, center - radius), min(1, center + radius)


def metrics(results, threshold=THRESHOLD):
    tp = sum(value >= threshold and label == 1 for value, label in results)
    fp = sum(value >= threshold and label == 0 for value, label in results)
    positives = sum(label for _, label in results)
    brier, loss = 0, 0
    for value, label in results:
        probability = 1 / (1 + math.exp(-max(-40, min(40, value))))
        brier += (probability - label) ** 2
        loss += max(value, 0) - label * value + math.log1p(math.exp(-abs(value)))
    return {"observations": len(results), "other": positives, "true_positive": tp, "false_positive": fp,
            "precision": tp / (tp + fp) if tp + fp else None, "recall": tp / positives if positives else None,
            "precision_wilson_95": wilson_interval(tp, tp + fp),
            "abstained": sum(-threshold < value < threshold for value, _ in results),
            "brier": brier / len(results), "log_loss": loss / len(results)}


def cross_validate(rows, folds=5, calibrated=True):
    results = []
    for training, test in partitions(rows, folds):
        model = fit(training) if calibrated else train(list(training.values()))
        results.extend((score(model, values), label) for values, label in test.values())
    for cut in (1, 2, THRESHOLD):
        measured = metrics(results, cut)
        print(f"log-odds >= {cut}: {measured['true_positive']} private streams hidden, "
              f"{measured['false_positive']} official hidden, {measured['abstained']} abstained/{len(results)}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = {"source": "audited labelled capture", "source_sha256": hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
              "threshold": THRESHOLD, "evaluation": "development channel-grouped outer cross-validation with inner calibration; not an independent holdout", "ablations": {}}
    for mode in ("both", "title", "tags"):
        rows = dataset(mode)
        print(f"{mode}: {len(rows)} labelled observations, {sum(y for _, y in rows.values())} private servers")
        report["ablations"][mode] = metrics(cross_validate(rows))
    if args.write:
        rows = dataset()
        data = {"revision": 3, "_comment": "Supervised piracy-presence inference from full titles and tags; absent official references are not piracy evidence.",
                "training": {"observations": len(rows), "source_sha256": report["source_sha256"],
                    "filter_predictions_used": False, "target": "private-server stream versus official Tibia",
                    "excluded_labels": ["unrelated games", "unverified or ambiguous games"],
                    "features": "shared words, word pairs and character 3/4/5-grams; FNV-1a identifiers",
                    "smoothing_alpha": ALPHA, "min_observations": 1, "char_feature_weight": 0.25,
                    "normalization": "presence only; no text-length normalization or absent-feature terms"},
                "model": fit(rows)}
        EVIDENCE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {len(data['model']['weights'])} learned presence weights")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
