# Full live capture — 2026-10-21 ~21:15 BRT

All 562 streams in the Tibia category directory, with complete title, every freeform tag and viewer count, read from Twitch's React props (the same data the extension uses). Used to audit the Tibia filter in both directions.

- `streams.json`: the capture.
- `verdicts.json`: `tools/twitch_evidence.py` verdicts with evidence (title/tag metadata).
- `review.txt`: every stream grouped by verdict, sorted by viewers, for manual review.

## Result (current rules)

| Verdict | Streams | Viewers |
|---|---|---|
| other (hidden) | 352 | ~16.1k |
| tibia (visible) | 132 | ~1.2k |
| undetermined (visible) | 78 | ~0.3k |

## Manual review

Errors found in the first pass and fixed:

- **Official stream hidden:** keplerztv ("[CELEBRA - RP 1700+]"), because the boss tag "Bakragore" matched the Baiak tag pattern.
- **OTServer shown as Tibia:** lord_paulistinha_ofc (paulistinhaot.com) via the official world tag Lutabra.
- **OTServers left undetermined** because a generic `global`/`tibiaglobal` tag cancelled a server declared in the title: matts (King Aslan), bruxotibiano (Aldeia Online), bigode_junim (PXG), rendoryltda (DeusOT). Now the title outranks tags.
- **Confirmed by the user:** projeto0337 ("FARM ON de live coins do rubinot", tag tibiaglobal) is RubinOT; now hidden.
- **`!rubinot` in a title names the server** (user decision): el_tratorr, pagodines, beltranctz and other `!server`-only titles are now hidden.
- **Unlisted servers:** Future OT, Baiak variants, ClassiCores, Padventures, Ultron OT, Avalorium, Ravox Idle, Poke Idle spellings, `xxxot.com` domains.

Still open:

- Streams playing other non-Tibia games with a tibiaglobal tag (jhovitv, Conan Exiles) stay visible; they are not OTServers.
