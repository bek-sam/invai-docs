---
name: profit-lines-cached-columns
description: profitLines.netCents (and channelFeesCents) are display-only caches; every real aggregate (getProfit, the digest's glance net) recomputes from the cost-bucket columns, never reads them back
metadata:
  type: project
---

`finance/profit.ts`'s `finalize()`/`sumBuckets()` compute `net = revenue - channelFees - blankCost
- transferCost - labelCost - packagingCost - laborCost - adsCost - refunds` from the raw cost-bucket
columns on `profitLines`. It never reads `profitLines.netCents` (or `channelFeesCents`) back for any
aggregate — those are write-once display caches for the row itself, not inputs to `getProfit`,
`comparePeriods`, or (wave 19) the digest's glance `net`/`netChange` facts.

**Why:** [[fixture-margin-fee-schedule]] already caught this for the market module's margin signal
(`channelFeesCents` ignored, fee recomputed from the default schedule). Wave 19's digest acceptance
tests hit the same fact from a different angle: a `saleAt()` fixture that set `netCents: -500`
directly on a reprint's profit line (revenue 0, no cost bucket set) produced a real aggregate net of
0 (= revenue), not -500, because nothing sums `netCents`. Cost a full debug cycle (traced
`comparePeriods` -> `channelProfit` -> `getProfit` -> `finalize` to find where the chosen number got
dropped).

**How to apply:** for any fixture that needs a specific aggregate net/margin (digest glance, profit
page, market signals), set `revenueCents` and the real cost-bucket column(s) (`blankCostCents` etc.),
not just `netCents`. Treat `netCents` as a value the fixture may set for row-shape completeness, but
never as the number an assertion should expect back from an aggregate query.
