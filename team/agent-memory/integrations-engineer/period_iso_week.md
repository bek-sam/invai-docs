---
name: period-iso-week
description: ISO week-1 anchoring bug pattern in period.ts's endOfIsoWeekIso, and how it was tested
metadata:
  type: project
---

`invai-backend/src/integrations/market/period.ts`'s `endOfIsoWeekIso` originally anchored ISO
week 1 on 1 January and walked back to that week's Monday. That is wrong: ISO 8601 defines week 1
as the week *containing* 4 January. Any year whose 1 Jan falls on Fri/Sat/Sun (2020-2023, 2027,
2028 among others) came out one week early — found in T-18-2 round 2 review
(`invai-docs/waves/18/reviews/T-18-2-reviewer-r2.md`, finding 1).

**Why:** the bug only showed up outside 2024-2026, so a test written with only "this year" or a
couple of hand-picked years missed it. It fed a weekly `asOf` a week stale into `confidence.ts`'s
freshness/staleness scoring, silently down-weighting real market signals.

**How to apply:** any date-math fix in this file (or similar ISO-week/period code elsewhere) needs
a round-trip test across a real span of years (2020-2030 used here), including 53-ISO-week years
(2020, 2026), and the round-trip check must use an *independently derived* implementation (here:
Richards' `p(y)` formula + ordinal-date week calc) rather than reusing `isoWeek()` from the same
file — otherwise a shared bug in both cancels out and the test proves nothing. Watch for the
subtlety that ordinal-day math must floor/round from UTC *midnight*, not from a time already at
`23:59:59.999`, or the day count rounds up by one.
