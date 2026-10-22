# Project context for Claude

Read and follow [AGENTS.md](AGENTS.md). Before discussing Safari installation or signing, read [the current Safari status](docs/SAFARI_STATUS.md).

The maintainer's local Safari app was signed with a free **Apple Development** certificate and installed in **Applications** on 2026-10-22. It is **not the temporary ZIP installation**. Public downloads still use ad-hoc signing. Safari restart persistence has not yet been verified; preserve that distinction when reporting status.

For subsequent local updates, after checking your changes, run `PYTHONDONTWRITEBYTECODE=1 python3 tools/update_safari_extension.py`. It automatically selects a valid identity from the installed app's team, builds, signs, verifies and installs, retaining a backup and restoring the old app if installed verification fails. Do not ask the user to choose a certificate or manually copy the app when this command can do the work. Read the status document for OS prompts and activation limits.
