---
name: analytics-ops-ta4
description: T-A4 facts - operations analytics conventions, dest_zone, and parity tests that run invai-docs metric SQL
metadata:
  type: project
---
- 2026-09-30 T-A4: `analytics.operations` parity tests read `invai-docs/metrics/sql/*.sql` from the sibling repo, swap `:'from'`/`:'to'` for date literals, set the test company's timezone to UTC, and run it under `withSystem`; `describe.skipIf` when the docs repo is absent (lone CI checkout).
- 2026-09-30 T-A4: `cost_settings` rows are created lazily; call finance `getCostSettings` before a raw UPDATE in tests or the update hits nothing.
- 2026-09-30 T-A4: shipments.dest_zone is written in buyLabel Tx 2 from the in-memory from/to ZIPs (`shipping/zone.ts`, approximate USPS bands); per-reason `rate_pct` rows in reprint_cost.sql don't sum to the total rate (rounding), so compare against total reprints / items pressed.
- 2026-09-30 T-A4 review r1: any `cost desc, count desc`-style sort on a grouped analytics cut needs a final `key.localeCompare` (or SQL tiebreak column) or ties come back in Postgres's nondeterministic row order and the test flakes ~1/3 runs; UUID keys always sort before literal keys like "unknown"/"in_house" since UUIDs are pure hex.
