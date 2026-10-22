"""Train the Tibia filter's statistical model: naive Bayes over title words and tags.

Labelled data: the audited capture (official Tibia vs other games) and the
reviewed 562-stream live capture (its "tibia"/"other" verdicts). Features are
squeezed, normalized title words ("t:rubinot") and tags ("g:deusot"); each
feature seen in at least MIN_COUNT channels gets a smoothed log-likelihood
ratio, clipped to +-CLIP. Evaluation is 5-fold cross-validation grouped by
channel, so a channel never appears in both training and test folds.

    python3 tools/train_tibia_model.py            # report cross-validation
    python3 tools/train_tibia_model.py --write    # store the model in tibia-evidence.json
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from twitch_evidence import AUDIT, AUDIT_OTHER, AUDIT_TIBIA, EVIDENCE, features  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "research/twitch/data/2026-10-21/live-2115"
MIN_COUNT, CLIP, ALPHA = 2, 4.0, 1.0


def dataset():
    rows = {}
    for row in json.loads(AUDIT.read_text())["classificacao"]:
        label = 1 if row["categoria"] in AUDIT_OTHER else 0 if row["categoria"] in AUDIT_TIBIA else None
        if label is not None:
            rows[row["canal"]] = (features(row["titulo_original"], [t.strip() for t in row["tags_originais"].split("|") if t.strip()]), label)
    verdicts = {v["channel"]: v["verdict"] for v in json.loads((LIVE / "verdicts.json").read_text())}
    for s in json.loads((LIVE / "streams.json").read_text()):
        verdict = verdicts.get(s["channel"])
        if verdict in ("other", "tibia") and f"live:{s['channel']}" not in rows:
            rows[f"live:{s['channel']}"] = (features(s["title"], s["tags"]), 1 if verdict == "other" else 0)
    return rows


def train(rows):
    pos = sum(label for _, label in rows)
    neg = len(rows) - pos
    counts = {}
    for feats, label in rows:
        for f in feats:
            c = counts.setdefault(f, [0, 0])
            c[label] += 1
    weights = {}
    for f, (n, p) in counts.items():
        if n + p >= MIN_COUNT:
            w = math.log((p + ALPHA) / (pos + 2 * ALPHA)) - math.log((n + ALPHA) / (neg + 2 * ALPHA))
            weights[f] = round(max(-CLIP, min(CLIP, w)), 3)
    # Balanced prior: other games dominate the captures, and their share must not
    # push neutral titles towards hiding; only the words and tags decide.
    return {"bias": 0, "features": dict(sorted(weights.items()))}


def score(model, feats):
    return model["bias"] + sum(model["features"].get(f, 0) for f in feats)


def wilson_interval(successes, total):
    """Two-sided 95% Wilson score interval; no estimate without observations."""
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0, center - radius), min(1, center + radius)


def cross_validate(rows, folds=5):
    keys = sorted(rows)
    # Prefixes distinguish captures, not independent channels. Keep every
    # observation of the same channel on one side of the train/test boundary.
    def channel(key):
        return key.removeprefix("live:").casefold()

    groups = {name: i % folds for i, name in enumerate(sorted({channel(key) for key in keys}))}
    results = []
    for k in range(folds):
        test = [key for key in keys if groups[channel(key)] == k]
        model = train([rows[key] for key in keys if groups[channel(key)] != k])
        results += [(score(model, rows[key][0]), rows[key][1]) for key in test]
    for cut in (4, 6, 8):
        tp = sum(1 for s, y in results if s >= cut and y)
        fp = sum(1 for s, y in results if s >= cut and not y)
        pos = sum(y for _, y in results)
        interval = wilson_interval(tp, tp + fp)
        precision = f"{tp / (tp + fp):.3f}" if tp + fp else "unknown"
        confidence = f"[{interval[0]:.4f}, {interval[1]:.4f}]" if interval else "unknown"
        recall = f"{tp / pos:.3f}" if pos else "unknown"
        abstained = sum(-cut < s < cut for s, _ in results)
        print(f"log-odds >= {cut}: precision {precision} ({fp} official hidden; {tp + fp} predicted other), "
              f"95% Wilson CI {confidence}, recall {recall}, abstention {abstained}/{len(results)}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    rows = dataset()
    channels = {key.removeprefix('live:').casefold() for key in rows}
    print(f"{len(rows)} labelled observations from {len(channels)} channels, {sum(y for _, y in rows.values())} other games")
    print("Development cross-validation only: labels and rules were tuned on these captures; "
          "this is not an independently reviewed holdout or a live-hiding release gate.")
    print("Wilson intervals summarize observations, including repeated captures of channels; "
          "they do not establish independent-sample precision.")
    cross_validate(rows)
    if args.write:
        data = json.loads(EVIDENCE.read_text())
        model = train(list(rows.values()))
        data["model"] = {"_comment": "Naive Bayes over title words (t:) and tags (g:), trained by tools/train_tibia_model.py; log-odds = bias + the weights of the features present. At log-odds >= confident it adds weights.model for other games, at <= -confident weights.model_tibia for Tibia.", "confident": 6, **model}
        EVIDENCE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {len(model['features'])} features")


if __name__ == "__main__":
    main()
