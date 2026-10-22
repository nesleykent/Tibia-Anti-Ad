# Research provenance

These assets were supplied in the local Adblock workspace on 2026-10-21. They predate this repository's creation. Reports describe earlier browser sessions, CSS injection, network simulations, assumptions and some user feedback. Their raw screenshots/HAR files were not present, and their claims were not independently reproduced during repository setup.

Reports and filter inputs retain their historical text, including limitations and outdated instructions. Current release-level installation/compatibility documentation takes precedence. Original working inputs and ZIP archives are preserved in the ignored local `local/legacy/` directory; a local SHA-256 manifest records their bytes. They are excluded from Git. The subsequently supplied `twitch-clean.zip` is unpacked as Tibia Anti-Ad extension source, plus its companion script/filter/report; its embedded vaft MIT notice is retained. The ZIP itself is not committed. SHA-256 provenance is recorded in `twitch/source-manifest.json`. The older raw archives remain local.

Userscripts are optional, unreviewed research artifacts, not part of generated subscriptions. Some change DOM APIs or body layout globally within their matched site, and MutationObserver timing does not guarantee prevention of parser-executed scripts. Tibiopedia's report explicitly describes page destruction without additional protection; it and TibiaWiki BR are excluded from generated bundles.

## Organization

- [Fansite research](fansites/README.md): historical reports and optional repair userscripts.
- [Twitch research](twitch/otserver-filtering.md): classification method, dated snapshots and offline evidence.
- [Source provenance](twitch/source-manifest.json): imported Twitch file hashes; path keys follow the current layout without changing the original digests.

Maintained filter inputs live in `filters/sources/`; generated subscriptions live in `filters/lists/`. Research userscripts are evidence and experiments, not automatically installed extensions.
