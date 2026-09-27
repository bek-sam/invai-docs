---
name: fixture-iso-week-offset
description: a fixed day offset for weeksAgo-style test fixtures only lands in the right ISO week for some weekdays of `now`
metadata:
  type: project
---

Placing a fixture sale/movement at `now - weeksAgo*WEEK - k*DAY` for a fixed constant `k` only
lands inside `completeWeeks`' intended ISO week when `now`'s ISO weekday is Thursday-Sunday
(`k=3` needs weekday >= 4). For a Monday-Wednesday `now`, it lands one week early, silently
shifting every `weeksAgo` bucket by one and leaving the true last complete ISO week empty.

**Why:** wave 18 T-18-3 second pass, AC17: `market.acceptance.test.ts`'s `sale()`/
`weeklySales()` used a fixed `-3 * DAY`; several `NOW` fixtures were Tuesdays (`2026-09-01`,
`2026-09-15`), so `weeklySales(60, 3, ...)` populated real weeks 2..61, not 1..60, and the yoy
math (`last 4 weeks / same 4 weeks a year earlier`) was silently off (0.75 instead of the
asserted 0).

**How to apply:** for any weekly-bucketed fixture, use a weekday-aware offset,
`isoWeekday(now) - 4` (always lands mid-week of the *intended* ISO week, for any `now`), not a
constant. `isoWeekday` needs the local calendar date (`signals.ts`'s exported `localYmd`), not
raw `getUTCDay()`, if `now` could ever be near a local-midnight boundary. When a companion
"hand SQL" test needs the same week's boundary, get it from `completeWeeks()` itself rather than
a second hand-rolled offset -- two independently-guessed windows are how this bug hid for a
whole first pass. See [[fixture-margin-fee-schedule]] for the sibling AC26/AC30 pitfall in the
same file.
