# Twitch Tibia snapshot — 2026-10-21

Public stream cards from the Twitch **Tibia** category directory, collected in the browser console and then classified by game/server. Research data only: no channel is blocked or hidden based on it.

## Files

| Path | Content |
|---|---|
| `raw/streams-1316-details-only.json` | 456 channels, ~13:16 BRT. Fields `channel`, `url`, `details` (raw card text) only — produced by an earlier collector version without title/tag parsing. |
| `raw/streams-1400.json` | 487 channels, ~14:00 BRT. Fields `channel`, `url`, `title`, `language`, `viewers`, `tags`, `details`, produced by [`collect-streams.js`](../../collect-streams.js) (fixed filename variant). |
| `analysis/classificacao.json` | Corrected classification of the 13:16 snapshot (456 channels, 12,989 viewers): per-category totals, confidence counts and per-channel rows. |
| `analysis/classificacao.csv` | Same per-channel rows as CSV (UTF-8 with BOM). |
| `analysis/relatorio.pdf` | Report (Portuguese) summarizing the classification. |
| `manifest.json` | Original filenames and SHA-256 of each file. |

## Classification summary (13:16 snapshot)

Confidence: Forte 344 · Provável 40 · Múltiplo 12 · Indeterminado 57 · Fraco 2 · confirmed by user 1.

Top categories by viewers: RubinOT 38.9%, PokeAlliance 17.8%, PokeXGames 11.7%, official Tibia 8.1%, other OTServers 5.6%.

## Caveats

- Card scraping is DOM-dependent; viewer counts and languages may be misread and the directory changes minute to minute.
- The classification was produced outside the offline prototype (`tools/classify_streams.py`) using title/tag rules plus manual review; it is not a validated detector and does not follow the prototype's strict `undetermined` policy.
- Channel names are public Twitch handles; this is not a blocklist.

## Reproduce a collection

Open `https://www.twitch.tv/directory/category/tibia`, paste `research/twitch/collect-streams.js` into the console and wait for the JSON download.
