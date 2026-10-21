# Website assessment methodology

Evaluate unfiltered and filtered behavior separately. A site's rating describes the dated unfiltered observation, not its reputation or its ability to fund itself. Each dimension gets a score from 0 to 3 only when evidence exists; use **unknown** otherwise. Never treat unknown as zero or average it into a total.

| Score | Advertising intrusiveness | Tracking | Performance impact | Usability interference |
| --- | --- | --- | --- | --- |
| 0 | No advertising observed in the test session | No tracking observed in the tested flows | No measurable ad/tracker overhead in paired runs | No interference observed |
| 1 | Static, clearly separated placements | Limited analytics without observed cross-site IDs | Median overhead above noise, below 10% | Cosmetic clutter without obstructed tasks |
| 2 | Sticky, floating, autoplay or repeated promotions | Cross-site tracking or identifier synchronization | Median overhead 10–30% | Focus/scroll interference, obstructed controls or dismissals required |
| 3 | Overlays, forced redirects or anti-adblock content denial | Observed fingerprinting or extensive cross-site identifier sharing | Median overhead above 30% | Navigation hijacking, inaccessible content or broken tasks |

Performance: report absolute and percentage deltas for transferred bytes, requests and main-thread blocking time separately. Use at least five paired cold-cache runs on the same device/network/page, alternate order, report medians and spread, and use the highest measured band. A difference within baseline variability stays inconclusive. Record blocker overhead separately; do not infer speed from an empty ad slot. A score is not proof of a website's intent.

Every published rating needs date/time, exact URL and page type, device/viewport, OS/browser/blocker versions, active lists and versions, consent/login state, delayed interactions, baseline and filtered captures, network evidence and functional results. Redact tokens, cookies, account details and unrelated browsing data. Distinguish directly observed behavior, simulation and inference. Reassess after material site changes or within 30 days; older ratings are stale.

Publish positive examples only after the same checks. A claim of "no intrusive advertising observed" is scoped to tested pages and dates. It never means "tracking-free forever" or permits ads through the filters. Exevo Pan's supplied report describes no detected ad-network/tracking stack, but also a floating promotional video and upsell; it is a useful comparison, not a clean-site award. No website currently has a verified positive award in this release.

Allow corrections with reproducible evidence. Publish the revision history and resolve false positives before broadening rules. Historical reports without raw artifacts are research leads, not verified leaderboard entries.
