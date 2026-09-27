---
name: fixture-margin-fee-schedule
description: market.acceptance.test.ts THIN_COSTS-style fixtures must not assume channelFeesCents feeds the margin signal
metadata:
  type: project
---

`market/compute.ts`'s margin signal (`marginBasis`) never reads `profitLines.channelFeesCents`; it
recomputes the channel fee fresh from the default fee schedule (`finance/profit.ts`
`defaultFeeTable`/`orderFees`, e.g. Amazon apparel referral: 5% under $20, jumping tiers above
that). A `Costs` fixture that puts a hand-picked `fees` value alongside `blank/transfer/label/
packaging/labor` and expects a specific `marginPct` will be wrong unless the *real* dynamic fee at
that price/category is accounted for -- `fees` in the fixture is bookkeeping only for
`profitLines`, not an input to the market margin calc.

**Why:** wave 18 T-18-3 second pass: AC26/AC30's `THIN_COSTS` (P0=$12.99, `fees:195`) was tuned
assuming `fees` counted, giving an intended ~19% margin; the real engine computed ~29% (above the
R2 `<25%` threshold), so R2 silently never fired. Cost a full debug cycle (added temporary
`console.log`s of the stored `market_signals` margin/price_position rows) to find.

**How to apply:** for any market-module fixture that needs a specific margin band (R2 `<25%,
>=15%`, R3 `<15%`, R5), compute `unitCost = blank+transfer+label+packaging+labor` and the real
channel fee via `orderFees(defaultFeeTable(channel), {revenueCents: p0, ...})` (or just probe it
with a throwaway `tsx` script importing `finance/profit.ts`) before choosing the price and cost
split -- don't trust the `fees` field to do anything for the market signal. Also keep the price
comfortably below the mock provider's comparable floor (`mock.ts`'s `baseCents` range, currently
$12.00-$32.00) so `p0 * r2TestMax` never gets capped below a randomly low per-ref median -- see
[[fixture-iso-week-offset]] for the sibling AC17 pitfall in the same file.
