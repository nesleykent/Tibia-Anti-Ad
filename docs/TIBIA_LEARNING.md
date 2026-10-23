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
new annotations. The old v2 model and its original experiments remain historical
artifacts, separate from the active v3 model.

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
The newest scheduled capture provides a separate pre-training check.

## Scheduled workflow

[Learn Tibia identifiers](../.github/workflows/learn-tibia.yml) runs at 05:17 and
17:17 UTC and supports manual dispatch. It obtains an app access token using
Twitch's client-credentials flow, resolves Tibia through Get Games, and paginates
Get Streams. Only title and tags enter the labeller. Twitch category captures,
input hashes, labels and hashed features are retained in cumulative Actions
artifacts, including labels from failed gates. Each successive artifact includes
all previous captures and supervision; retention is 90 days per artifact. Thus
failed novel-name checks can supply training data for the next run without
publishing an unverified model.

The labeller uses OpenAI Responses with `store: false`, strict Structured Outputs
and no tools. Metadata is explicitly untrusted input. The default model is
`gpt-5.4-mini`; repository variable `LLM_LABEL_MODEL` can select another compatible
model. Every new input must have exactly one label; a private label must cite an
extracted identifier candidate. Invalid, missing, refused or incomplete output
fails the run. Labels are reused by exact title and deduplicated/sorted tag hash.
The decisions hash prevents silently reusing labels after a policy change.

Training excludes every newly labelled input from both historical seed and
retained history for the newest-capture check. Every new binary label must agree
with the pre-training model at 50%. After this check, all labelled data is fitted,
the complete repository acceptance suite runs, and the six server holdouts are
checked again. A failed stage fails the workflow; it cannot reach the publication
job. GitHub failure email follows the maintainer's Actions notification settings.

Publication has a separate job and credential. Its allowlist contains only the
active model JSON, the existing public `tibia-evidence.json` and its bundled JS
copy. It checks the validated main commit and uses a non-forced GitHub ref update.
Concurrent main changes cancel publication instead of overwriting changes. The
existing background updater downloads the public model every six hours. v3 needs
the extension version that supports identifier-span inference; older extensions
reject the incompatible format and retain their last valid model.

## Repository secrets

- `TWITCH_CLIENT_ID`: Twitch application client ID.
- `TWITCH_CLIENT_SECRET`: secret for that Twitch application.
- `OPENAI_API_KEY`: OpenAI API project key with Responses API access and billing.
- `MODEL_PUBLISH_TOKEN`: fine-grained GitHub token limited to this repository,
  Contents read/write, owned by an administrator allowed to bypass the existing
  main branch protection. The workflow does not weaken branch protection.

`GITHUB_TOKEN` is supplied automatically for artifact access. Credentials are
passed only to their steps, never stored in captures or committed. API response
bodies and exception representations are excluded from logs. Missing secrets fail
closed. Configure these in GitHub Settings, Secrets and variables, Actions.

Sources: [Twitch app tokens](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#client-credentials-grant-flow),
[Get Streams](https://dev.twitch.tv/docs/api/reference/#get-streams),
[OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[Responses](https://developers.openai.com/api/reference/resources/responses/methods/create).

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
