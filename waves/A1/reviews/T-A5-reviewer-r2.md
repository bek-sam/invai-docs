Verdict: approve
# Review T-A5 r2 — reviewer (Opus 5.5); author backend-engineer (Opus 5.5). Fix commit b5ea7d0 on 6b531c2.

## Evidence I re-ran (own DB `invai_rv7_test`, app role `invai_app` / migration role `invai`, `REDIS_URL=…/12`; dropped + flushed after)
- `pnpm typecheck` exit 0; `pnpm lint` → `Checked 441 files in 258ms. No fixes applied.`
- `vitest run src/modules/inventory/ src/modules/analytics/` → 7 runs: 6× `14 passed (14)`, `128 passed`; 1× design-service.test.ts failed at file level (11 skipped, no assertion failed); could not reproduce in 6 reruns, and no other vitest was running afterwards. Probably DB/infra contention (non-blocking; tech lead to watch at the gate).
- inventory/service.test.ts + design-service.test.ts, 2 extra runs → `19 passed (19)` each.
- New tests on base 6b531c2 (git archive + b5ea7d0 test files): 5 fail (`expected 53 to be 40`, `expected 20 to be <= 1`, pure cap test, stage not `dead`, `expected true to be false`). They fail without the fix.
- `scan-test-weakening.sh invai-backend 6b531c2` → no hits; the only removed test line is an import reshuffle.
- `git show --stat b5ea7d0`: only inventory/service.ts(+test) and analytics/design-service.ts(+test). Uncommitted `src/db/seed/**` belong to T-A1, so I ignored them.

## Findings resolved
1. AC-C3 fixed. Scratch probe of `splitLinesBySizeCurve` at HEAD: my r1 case (S/M vel 5, L vel 10, L supplier 40) → S=95, M=95, L=40, so the cap holds. S avail 20 / M avail 0, equal sales → S=75, M=95, and both end at 95. Single-size group (qty 7, supplier 3) passes through untouched. A supplier-0 line and a line with no info both pass through. When every cap is below the total, the group shrinks (S=10, M=5).
2. AC-C4 fixed. Only `provenance.source === "own"` readings move the stage. The base-failing test shows a niche "rising" reading on a dead design → `dead`, with marketTrend null. The own-trend test still gives `dead -> growing`.
3. AC-B/C-screen1 fixed. In a new shop with 3 listings and no sales, `hasEnoughHistory` is false and nothing is dead. After backdating `created_at` by 61 days, all 3 are dead. `companies.created_at` reads correctly under `invai_app` RLS (the backdated case turns dead).
- Savepoint: scratch test with the market read mocked to run `select 1/0` inside `withTenant`. It logs `market trend read failed` with companyId and designId (no PII), returns both rows as `inactive`, and a later `select 1` in the same tx succeeds. drizzle node-postgres nests `tx.transaction` as `savepoint spN` (session.js:206-219).
- Finding 4 closed by the grant in wave.md.

## Optional notes (non-blocking)
- A zero-velocity size in a split group now gets a 0-qty line kept in the plan. That matches the old `splitBySizeCurve`. When the other sizes are capped, the group total shrinks instead of spilling into that size (S=0, M=4 from 20).
- N+1 `getTrendSignal` per design is still there, as the brief allows.
