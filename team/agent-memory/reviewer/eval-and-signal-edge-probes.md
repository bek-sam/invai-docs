---
name: eval-and-signal-edge-probes
description: Probes that caught real gaps in T-P1-3 (eval tenant cleanup, act-by past dates, all-zero series, oRPC done event)
metadata:
  type: feedback
---
- 2026-09-30 T-P1-3: "eval deletes its tenant" claims: count `companies` before/after `pnpm evals <route>` on dev DB; routes may create their own extra tenant (evals/assistant/seed.ts). Delete the leftover you created by id.
- 2026-09-30 T-P1-3: act-by/date fixes: probe `actBy()` with 0 < weeksToPeak < leadWeeks, not only the clamped 0 case — date = peakStart − lead is already past.
- 2026-09-30 T-P1-3: when a stats function is rewritten (ln(y+1) transforms), probe all-zero input; `overall <= 0 → null` guards silently stop firing.
- 2026-09-30 T-P1-3: oRPC RPC handler always emits `event: done data: {}` even when the generator returns undefined; client cancels reader on it (B-132 is library-side).

**Why:** each was missed by the author's own unit tests. **How to apply:** run these probes with a tsx scratch file in /tmp importing the module by absolute path.
