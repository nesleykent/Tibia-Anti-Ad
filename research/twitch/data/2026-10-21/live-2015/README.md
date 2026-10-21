# Live sample — 2026-10-21 ~20:15 BRT

114 streams from the Tibia category directory, used to test multi-signal classification (`tools/twitch_evidence.py`).

- `streams.json`: channel and title (tags were not exposed in this directory layout).

Tags were not captured for this sample (titles only), so it under-represents the metadata stage. Current rules: 89 `other`, 12 `tibia`, 13 `undetermined`. No stream with an official marker (Global, official world) was hidden except where an OTServer-only client element was on screen (e.g. "King Aslan Global" with a Map View window).

Visual findings:

- RubinOT, King Aslan and RedOT clients show a titled **"Map View"** minimap window, a **Battle Pass** button and **Daily Missions**. The official client shows none of these: its minimap has no title, a compass rose and a vertical floor-level bar.
- RubinOT and Baiak Idle otherwise reuse the official client's panels (Skills, Hunt Analyser…), so those panels only mean "a Tibia-style client".

No ground-truth labels: titles were used only to sanity-check verdicts.
