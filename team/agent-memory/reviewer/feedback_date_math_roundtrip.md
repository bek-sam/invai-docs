---
name: date-math-roundtrip
description: Review check for hand-written ISO week/month period math: round-trip across several years, not just the current one
metadata:
  type: feedback
---

When a diff hand-writes calendar math (ISO week to date, period end), round-trip it (`isoWeek(periodEndIso(p)) === p`) for 2021–2028 in a tsx script. End tsx scripts that import `src/env` or modules with `process.exit(0)`, because they otherwise hang on open handles.

**Why:** 2026-09-27 T-18-2 r2: `period.ts` `endOfIsoWeekIso` anchored on 1 Jan instead of 4 Jan. It was correct for 2024–2026, so the author's 2026-only tests passed, but it came back one week early in 2027 and 2028 (3 of 7 years).

**How to apply:** check any `asOf`, period or week helper this way. Also look for tests pinned to fixed years that will fall out of a rolling window.

Oracles: Node 24 here has no `Temporal`. Use Python `datetime.date.fromisocalendar(y, w, 7)` as a second independent oracle (dump it to JSON and compare in tsx). This worked in T-18-2 r3: 574 weeks from 2020 to 2030, 0 mismatches.
