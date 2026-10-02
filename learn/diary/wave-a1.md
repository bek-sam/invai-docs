# Wave A1 — analytics v2, the data and read services

**Dates:** started 2026-09-30 00:05 CDT, before waves 24/25 (paused pending AWS) and
before the rest of wave 23b.

## What was built
- **T-A1** Analytics-ready seed (backend-foundation): 18 months of realistic order
  history a shop owner could actually believe.
- **T-A2** `analytics.*` contract (architect): the new contract surface A2's screens will
  read from.
- **T-A3** Finance analytics service + `fixed_monthly_cents` migration
  (backend-engineer/finance): true unit economics — the real fixed-cost split per order.
- **T-A4** Operations and shipping analytics + `shipments.dest_zone`
  (backend-engineer/production, shipping): operations wait times and shipping margin by
  destination zone.
- **T-A5** Inventory and design analytics (backend-engineer/inventory): stock health and
  design-level performance numbers.

## Why
Through wave A1, "profit" existed but a shop owner couldn't see *why* a number moved —
losing orders, leakage, shipping margin by zone, operations bottlenecks, inventory health.
This wave builds the data services for all of that on 18 months of seed history; A2 turns
it into screens the owner actually sees.

## What went wrong
- T-A1's own build found and fixed a real bug in the seed before anyone else saw it: zero
  late orders across the entire history, and a market-demand test that took 60 seconds —
  both symptoms of unrealistic seed shape (the same category of problem `CLAUDE.md`
  already warns about: "unrealistic seed sizes made gang sheets look 51.7% efficient").
- T-A1's review round 1 came back **changes-required**: the history had a volume cliff of
  roughly 8x between live-month and historical order counts, and the wrong year was
  picked as "last complete Q4." Round 2 ramped history to ~6→11 orders/day, fixed the Q4
  multiplier to 1.75x, and picked the actual last complete Q4 — verified against the
  gate's own fresh seed (19.0 months, Q4 ~2.1x, live/history ratio 1.13x).
- A gate-level regression recurred here that had already been "fixed" once before: the
  Today greeting date showed an English date inside Spanish UI again, even though a
  `dateLocale()` helper had already been built specifically to prevent exactly that
  (B-207). Nothing stopped a *new* `toLocaleDateString(undefined, …)` call from being
  written somewhere else — the helper was opt-in, not enforced.
- A delegated screen check reported no Spanish text truncation while the Profit page's
  Spanish KPI card was visibly clipped — the screen-check prompt had listed *which*
  screens to look at, but not *what* to inspect on them (KPI value width at 1440px,
  per-locale number formats).

## What the team learned
- A helper function that *can* fix a bug class only fixes it if nothing can bypass it —
  the proposed fix moves from "use `dateLocale()`" to "ban raw `toLocaleDateString(undefined`
  with a lint/grep check across `invai-web/src`" (B-225).
- A delegated visual check needs to name the specific failure mode to look for (KPI value
  overflow, per-locale number format), not just the screen to open — and the tech lead
  still opens at least 3 screenshots itself rather than trusting the delegation alone.
- Review round 1 catching a volume-shape problem in 18 months of generated history before
  it reached a shop-facing screen is exactly what a seed review is for — "realistic" is a
  property that has to be checked against real shop numbers, not assumed from the
  generator's code looking reasonable.

## Files to look at
- `invai-backend/src/db/seed/` — the 18-month history generator and its Q4 ramp (T-A1).
- `invai-contracts/src/contract/analytics.ts` — the new contract (T-A2).
- `invai-backend/src/modules/analytics/finance.ts`, `src/db/schema/finance.ts`
  (`fixed_monthly_cents`) — T-A3.
- `invai-backend/src/modules/analytics/{operations,shipping}.ts`,
  `src/db/schema/shipping.ts` (`dest_zone`) — T-A4.
- `invai-backend/src/modules/analytics/{inventory,design}.ts` — T-A5.
- `invai-docs/team/lessons.md` (2026-09-30, "wave A1 gate" rows, two of them).
