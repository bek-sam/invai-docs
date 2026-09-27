---
name: project-market-module-boundaries
description: T-18-3 market module cross-module interface review notes (wave 18, contract 0.6.0)
metadata:
  type: project
---

2026-09-27 T-18-3: `src/modules/market/deps.ts` is a single funnel for both external deps (T-18-2
providers via `../../integrations/market` index; T-18-4 `classifyDesignNiche`/`screenMarketTerms`
via `../ai/niche`), with a `setMarketDeps()` test-double hook. Consumers (`modules/ai/*`) reach the
module only through `market/service.ts`.

**Why:** cross-module interface review is mine to co-review; this made the grep-based boundary
check fast in both directions (module's imports of others' internals, and others' imports of the
module beyond its public service file). Good template to ask for on future cross-module cards.

**How to apply:** when co-reviewing a new backend module against `wave.md`'s "Agreed interfaces",
check for a `deps.ts`-style funnel before assuming imports are scattered; flag its absence even
without a leak yet.

Also: `SignalProvenance.asOf` (`Timestamp = z.iso.datetime({offset:true})`) survived T-18-2 round 2
changing the provider's `asOf` string format, because the market module normalizes through
`asOfDate()`/`new Date(...)` at write time into a real `timestamptz` column and re-serializes with
`.toISOString()` at read time — that column is the seam that decouples contract shape from
provider string format. Worth checking this parse-on-write/serialize-on-read pattern on any future
provider-consumer boundary instead of trusting provider strings to already match the contract.
