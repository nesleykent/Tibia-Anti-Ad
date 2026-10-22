# Project instructions

- Preserve the public filter-list URLs and the shared extension source in `extension/src/`.
- Keep local originals, captures and caches in the visible, ignored `local/` folder. Build output belongs in `dist/`.
- Run `PYTHONDONTWRITEBYTECODE=1 python3 tools/check_project.py` for repository checks. Record browser verification separately from build and signature verification.
- Commit verified changes and push directly to `main`, as requested by the maintainer. Integrate concurrent remote changes without force-pushing.

## Safari: read before giving installation advice or rebuilding

Read [Safari signing status](docs/SAFARI_STATUS.md) and the [installation guide](docs/INSTALL_SAFARI.md).

The maintainer's Mac has an **Apple Development-signed app installed in `/Applications/Tibia Anti-Ad.app`**, verified on 2026-10-22. It is an installed app containing an extension, not an **Add Temporary Extension** installation. Do not apply the temporary ZIP's 24-hour/quit lifetime to this signed app.

The public Release app and default CI build still use **ad-hoc signing**. Personal signing is explicit through `--sign-identity` or `TIBIA_SAFARI_SIGN_IDENTITY`. Do not replace the personally signed installed app with an ad-hoc preview during routine builds or updates.

Safari acceptance with unsigned extensions disabled and persistence after quitting Safari remain **unverified**. Do not describe these as tested, promise permanent validity, or infer macOS renewal periods from iOS rules. Never publish the maintainer's certificate, private key, identity details or personally signed app as a public release.
