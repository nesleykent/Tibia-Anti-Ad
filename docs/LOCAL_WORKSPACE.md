# Local workspace organization

The checkout separates published files from original working material and generated output.

| Location | Purpose |
| --- | --- |
| `extension/`, `filters/`, `research/`, `scripts/`, `tools/`, `tests/` | Maintained project files |
| `docs/` and root project documents | Public usage, contribution and maintenance guidance |
| `dist/` | Reproducible development builds; ignored by Git |
| `local/legacy/fansites/<domain>/` | Original local filters, reports and userscripts, grouped by fansite. `tibiavip.app` is stored as `tibiavip.app-site/`: macOS treats any folder ending in `.app` as an application and lists it in Launchpad and Spotlight. |
| `local/legacy/twitch/scripts/` | Original Twitch scripts |
| `local/legacy/archives/` | Supplied ZIP archives |
| `local/legacy/notes/` | Original working notes |
| `local/legacy/manifest.json` | Original filenames, current relative paths and SHA-256 values |
| `local/cache/` | Collected bytecode caches and Finder metadata |
| `.claude/worktrees/` | Claude-managed linked Git checkouts |

The `local/` contents belong to the local workspace and are not included when cloning the repository. New clones do not need the originals to build or run checks. The local `local/README.md` indexes the retained files.

Keep one maintained copy of each input in the public source tree; retain older originals as provenance under `local/legacy/`. Compare hashes before and after relocating original material. Do not hand-move linked Git checkouts or edit their `.git` pointers: inspect `git worktree list` and coordinate with their owning sessions first.

To verify the public checkout without creating new bytecode folders beside the source:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py
```

Rebuild Chrome with `python3 tools/build_chrome_extension.py`. Its output stays in `dist/tibia-anti-ad-chrome/`.
