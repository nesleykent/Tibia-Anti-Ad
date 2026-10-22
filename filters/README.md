# Content-blocking filters

- `sources/sites/`: historical per-site rule inputs. Some are unsafe to install directly; the build scopes network rules and excludes known content-loss risks from subscriptions.
- `sources/twitch/`: imported Twitch filter input and classifier evidence.
- `lists/`: generated portable and extended subscriptions. Install one using the current links in the [project README](../README.md).

Edit sources and run `python3 tools/build_filters.py` from the repository root. Extension site assets are generated separately with `python3 tools/build_extension_sites.py`. Classifier evidence is copied into the extension with `python3 tools/twitch_evidence.py --write-js`. Run `python3 tools/check_project.py` to verify all generated files.

Subscription paths changed during the directory reorganization: replace old subscription URLs with the current `filters/lists/` URLs. The source inputs and research files are not installable bundles.
