# Scheduled Tibia learning

The classifier follows [DECISIONS.md](../DECISIONS.md). Its runtime model contains
character features from candidate identifier spans, structural features and the
existing relational context features. It contains no server alias inventory,
channel features, images or title vocabulary model. Hashing is feature encoding,
not anonymization against a determined dictionary attack; no raw local capture,
screenshot, channel or local filename is published.

`tools/tibia_spans.py` and `extension/src/tibia-classify.js` implement the same
candidate extraction and inference. The shared specification is exported by
`tools/twitch_evidence.py`. Per-shape recognition cutoffs come from negative
training identifiers. Generic negative controls prevent OT-like endings such as
loot/robot from serving as identifiers. Spacing augmentation applies only to
annotated identifier spans inside each training fold. A second fitted context
logit preserves sponsor, negation and mixed-session semantics. A tag can identify
an independent server even when another part of the title contains a shop command.

`research/twitch/model/span-supervision.json` is the feature-only supervision
packet: all 399 supplied inputs, historical supervision and generic controls.
Historical targets remain unchanged. Explicit acceptance baselines are hard
constraints; other historical disagreements remain soft targets alongside the
new annotations. The old v2/v3 models and their original experiments remain
historical artifacts, separate from the active v4 model.

## Reproduce

Fit requires Python with NumPy 2.3.5. Inference and repository checks use the
standard library and Node. Run:

```sh
python3 tools/train_tibia_spans.py fit
python3 tools/train_tibia_spans.py holdout
python3 tools/twitch_evidence.py --write-js
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py
```

The holdout refits both stages separately for every annotated server identity in
the supplied capture. It excludes all matching historical and new examples,
including candidate identity matches, before fitting or choosing cutoffs.
`span-holdout.json` reports stream/identity pairs, since one stream can identify
multiple servers. The six requested new-name controls must all pass. This is an
explicit development acceptance benchmark, not a claim of untouched evaluation.
A newly labelled capture can provide a separate pre-training check.

## Capture and agent labelling

The coding agent labels metadata itself during project work, following
DECISIONS.md. There is no separate inference model, server, API or weight cache.
GitHub Actions and scheduled captures are disabled by maintainer instruction.
The existing reproduction commands verify the model. Publish verified ZIPs and
checksums through the maintainer's authenticated GitHub account, with written
release notes. No replacement scheduler is introduced. Preserve source captures and labels in ignored local storage.

The Twitch capture CLI remains available for authorized local capture using
Twitch client credentials. No credentials are committed or printed. The extension
continues downloading the stable public rules URL.

## Domain/name equivalence regression

An observed live title containing two bare server brands was assigned 99% official,
although both corresponding domains were already recognized. Domain supervision
now produces the bare registered brand as a derived training view, including
multi-label suffixes such as `.com.br`. Negative tool/shop domains get the same
transformation. Spacing views remain restricted to annotated identifiers.

The trainer deduplicates these views and regularizes frequent character fragments
more strongly than rare character fragments. This retains structural recognition
for servers excluded from training while fitting the derived names. These are
training transformations; runtime inference still has no name/alias inventory.
Retained API captures can refresh derived views without changing existing labels,
identities or provenance; missing source captures fail the migration closed.

## Protocol and project regression

Revision 7 adds learned structural features for the relationship between a
candidate project name and its adjacent protocol version, launch context,
identifier length and numeric protocol suffix. Domain suffix analysis uses the
registered brand label, including common multi-label country suffixes. Numeric
brand/domain transport views are generated within the training fold for both
positive identifiers and negative controls. Runtime inference still contains no
name inventory.

Recognition cutoffs distinguish compound project names from generic standalone
suffix words, and a Poke/Pokemon prefix with a brand tail from the generic prefix
alone. This keeps generic negative examples from setting the cutoff for a
different identifier shape.

Private session rows with missing identifier annotations cannot calibrate
negative identifier cutoffs. Metadata review completed 18 missing identifier
annotations in existing rows; the packet records those corrections and prior
groups explicitly. Original session labels, targets and input identities remain
unchanged. Canonical server aliases share a holdout identity, including protocol
suffix variants; changed grouping retains the previous groups in the packet.
The prefix indexed by `historical_count` also contains supplemental
controls; the original 399-input export remains the final block. The supplement
contains 145 newly reviewed metadata inputs and four protocol controls.

Revision 8 adds nine project/protocol regression controls, including the reported
project plus Tibia plus protocol title. The project proposal retains that full
identifier span rather than dropping the version. Numeric brand and protocol
spellings produce training views with and without the game descriptor; domain
brands also produce single and country-suffix domain views. Both identifier
classes receive transport views. Negative protocol proposals also vary the
version spelling, so changing a gameplay title from 7.4 to 8.60 cannot supply
server evidence. Each held-out server loses all its derived
views with its original examples. These transformations do not add a runtime
name inventory or change the v4 inference contract.

Identifier shapes with both positive and negative supervision retain their signed
maximum-negative calibration boundary. A forced zero floor was rejecting valid
held-out domains even when their scores exceeded every training negative. Shapes
without positive examples, including bare protocols, retain the zero floor.
History augmentation revision 4 reconstructs prior capitalized project proposals
from retained source metadata when a longer protocol proposal supersedes them.
It preserves existing identifier annotations and session outcomes.

Format v4 makes this feature contract explicit. A v3 runtime rejects v4 model
downloads instead of silently ignoring structural features; it needs the updated
extension source. New v4 installations reject older cached rules and use their
bundled model. Scheduled history migration re-derives features from retained
captures while preserving original labels, groups and label provenance.
