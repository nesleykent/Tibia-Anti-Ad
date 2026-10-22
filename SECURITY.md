# Security policy

## Supported scope

Security fixes currently target the latest `main` revision. There is no supported stable release series yet. Update a development installation from `main` and rebuild it when a fix is published; old snapshots are not maintained.

In-scope reports include extension privilege misuse, unsafe page/extension messaging, unintended disclosure of stored data, malicious filter behavior and compromised build or release artifacts. Ordinary missed ads, broken layouts and classification errors belong in public issues unless they expose a security or privacy vulnerability.

## Report privately

Use [GitHub private vulnerability reporting](https://github.com/nesleykent/Tibia-Anti-Ad/security/advisories/new). Include the affected commit, browser/OS versions, impact, minimal reproduction and a proposed mitigation if known. Use synthetic data and redact tokens, cookies, account identifiers and personal browsing history.

If private reporting is unavailable, open an issue asking the maintainer for a private reporting channel without disclosing exploit details. Do not put an unpatched exploit or credentials in a public issue.

The maintainer will assess reports as capacity allows, coordinate remediation and credit reporters with their consent. There is no guaranteed response time or paid bounty. Publish details after a fix or an agreed disclosure date.

## Privacy and permissions

The extension requests access to Twitch and the supported fansites to apply filtering and site repairs. Feature settings are stored locally. A small subset is mirrored into each relevant page's local storage so early page scripts can read it; page scripts can also read that mirror. It is not a secret store.

Offline classification checks do not need credentials or a network connection. Research collectors and thumbnail/OCR workflows are separate tools and may access external services or local captures. Inspect them before use and never commit private sessions. See the [extension guide](extensions/tibia-anti-ad/README.md) for feature controls and rollback.
