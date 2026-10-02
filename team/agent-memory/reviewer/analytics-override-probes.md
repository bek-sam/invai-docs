---
name: analytics-override-probes
description: Probes that caught T-A5 bugs — redistribution dropping existing caps, market getTrendSignal niche fallback, hasEnoughHistory = rows>0
metadata:
  type: feedback
---

2026-09-30 T-A5: when a card "redistributes" or "overrides" an existing number (reorder size split, market-trend override), probe the invariants the old code enforced, not just the new ratio: the split dropped `baseSuggestion`'s `min(qty, supplierStock)` cap and ignored current stock (mock supplier stock = 40 + sha256(sku)%2400, so search SKUs for a small value). `market.getTrendSignal({designId})` falls back to niche-level outside (mock) readings, so "market trend wins" turned dead designs into growing; dev DB has only `insufficient` design own trends.

**Why:** the author's tests used all-zero stock and an own-source signal, which hide both.

**How to apply:** write a scratch test in a `git archive` copy (scratchpad), force-print with `expect(str).toBe("x")` (vitest hides console.log on pass), run it on base and HEAD. Also check any `hasEnoughHistory = rows.length > 0` against the metric doc's minimum sample. See [[analytics-sort-tie-flake]].

2026-09-30 T-A5 r2: prove a savepoint-wrapped read with a scratch `vi.mock` that runs `select 1/0` on the passed tx, then query again on the outer tx.
