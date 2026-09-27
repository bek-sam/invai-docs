# Review of T-18-3 (round 1)

- Reviewer: security-reviewer on claude-sonnet-5
- Author: backend-engineer (market) on claude-opus-5-5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show --stat 7ed3b4f 9dfb0c3 c2057df` | stub, module+migration+grants, price-unit/permanent-failure fix; only card-owned paths plus the exact 3 grants (`db/schema/index.ts`, `api/router.ts`, `modules/jobs.ts`) and the exact 2-edit `rls-coverage.test.ts` hunk |
| Worktree `../invai-backend-sec-t18-3` @ c2057df, own DB `invai_t18_sec_3`, Redis DB 9: `vitest run src/modules/market/service.test.ts src/modules/market/engine.test.ts src/db/rls-coverage.test.ts src/api/authz.test.ts` | 4 files, 75 tests passed |
| Same worktree, new file `src/modules/market/s34.security.test.ts` (capture the `queries` array actually passed to `provider.series()`, assert Set-equality with `CANONICAL_QUERIES`) | 1 passed — proves today's `refreshDemand` code is compliant (fetches the full taxonomy unconditionally), but this exact assertion does not exist anywhere in the shipped T-18-3 commits |
| Read `drizzle/0027_market_signals.sql` | 4 tenant tables get `ENABLE ROW LEVEL SECURITY` + a `..._tenant` policy keyed on `company_id`; `market_series_cache` gets `ENABLE ROW LEVEL SECURITY` + `market_series_cache_public_read` (`FOR SELECT ... USING (true)`) + `REVOKE INSERT, UPDATE, DELETE ... FROM invai_app`, appended to the same migration |
| Read `src/db/rls-coverage.test.ts` diff (9dfb0c3) | exactly 2 edits, nothing else: `market_series_cache` added to `PUBLIC_READ_TABLES`, and to the app-role-cannot-write assertion (`ins/upd/del: false`) |
| Read `src/modules/market/config.ts`, `src/modules/tenancy/demo-flag.ts` | `mockSourcesAllowed` = `!e.isProd \|\| e.allowMocks \|\| isSampleWorkspace(companyId)`, matching ADR 0015 and the wave hard fence exactly; `isSampleWorkspace` reads `companies.demoOwnerUserId`/`settings.demoRetiredAt`, set only at company creation/reset — no market procedure or any tenant-facing write touches either field, so a tenant cannot flip its own mock-visibility |
| Read `src/modules/market/history.ts`, `jobs.ts`, `service.ts` for buyer-PII columns | no reference to `buyerName`, `buyer_note`/`buyerNote`, `shipTo`, `encryptedText`, or any email/address field; own-history reads are unit/revenue aggregates only |

## Acceptance criteria (this review's scope: 1, 2a, 2b/S-34, 12, 13)
| # | Met? | Evidence |
|---|---|---|
| 1 (tables, RLS, global cache) | yes | All 4 new tenant tables have `company_id`, `tenantPolicy(...)`, `.enableRLS()` in the same migration; cross-tenant isolation test at `service.test.ts:1057` (another shop → 0 rows, `NOT_FOUND`). `market_series_cache` has no `company_id` column (`service.test.ts:472` asserts the column list), public-read policy, app role write denied (`permission denied` on insert, `rls-coverage.test.ts` green with both grant edits and nothing else touched in that file) |
| 2a (mock visibility) | yes | `mockSourcesAllowed` is the single predicate, applied in `refreshPricing` (skips mock providers when not allowed) and exercised for both branches (`service.test.ts:836-846`, `market-prod-mode.acceptance.test.ts:186-222`: production-like env + real shop vs. sample workspace) |
| 2b / S-34 | **no — stays open** | See "Blocking findings" below |
| 12 (router/permission matrix) | yes | `service.test.ts:1186-1238`: designer sets niches (OK), designer on `recommendations.list` → `FORBIDDEN`; presser → `FORBIDDEN` on taxonomy, niches.get, niches.set and recommendations.list; cross-tenant design id → `NOT_FOUND` (`service.test.ts:1057-1081`) |
| 13 (read-only by construction) | yes | `service.test.ts:1255` "the module writes only market_* tables" plus QA's `market.acceptance.test.ts:792/809` (jobs, reads and a vote write no business table; source scan for writes to catalog/listings/price/ads/stock/PO tables) |

## Blocking findings
1. `invai-backend/src/modules/market/service.test.ts:500-549` (the only S-34-adjacent test, "refreshDemand stores only taxonomy queries...") asserts only **containment**: every stored `query` is `∈ CANONICAL_QUERIES` (line 518, `for (const r of qs) ... expect(CANONICAL_QUERIES.has(r.q)).toBe(true)`). It never asserts the reverse — that the set of queries **fetched** (sent to `provider.series()`) equals the full taxonomy. AC 2b's exact wording is "A test asserts the fetched query set equals the taxonomy's." No such equality assertion exists in any T-18-3 commit (checked `service.test.ts`, `engine.test.ts`, and both acceptance test files under the module).
   - This is not a live vulnerability: I read `refreshDemand` (`jobs.ts`) and confirmed `const queries = [...CANONICAL_QUERIES]` is built unconditionally, with no tenant/design/niche input anywhere in the function — the implementation itself already matches ADR 0015 §7/the S-34 fix. I proved this by adding the missing equality test myself in an isolated worktree (`s34.security.test.ts`, above): it passes against `c2057df` today.
   - The gap is that the containment-only test would **not catch a regression**: if a future edit narrowed `queries` to "the niches some tenant currently has a design in" (the exact S-34 scenario — a cache row's presence/freshness becoming a low-fidelity cross-tenant signal), every existing market test would keep passing, because containment of a subset is still containment.
   - Per the card ("2b (security, T-18-1 co-review)... adds a test asserting the fetched query set equals the taxonomy's") and my `v1-review.md` S-34 row ("close before T-18-3's review round" once that test exists), this criterion is not met. **S-34 stays Open**, owner backend-engineer (T-18-3), Low severity, no clock (no PII/cross-tenant access today) — but block the card on it since it's an explicit, cheap, two-line acceptance criterion, not a judgment call: strengthen the existing test at `service.test.ts:518` to `expect(new Set(qs.filter(r => r.s !== "census").map(r => r.q))).toEqual(CANONICAL_QUERIES)` (or capture the `queries` argument passed into the provider double, as my proof test does) alongside the containment check that's already there.

## Checks
- [x] Only owned paths changed (`git diff --stat` on all 3 commits: `src/modules/market/**`, `src/db/schema/market.ts` + its migration, and exactly the granted lines in `src/db/schema/index.ts`, `src/api/router.ts`, `src/modules/jobs.ts`, `src/db/rls-coverage.test.ts`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (no `.skip`, loosened assertions, mocks of the unit under test, rewritten snapshots) — `rls-coverage.test.ts`'s two edits are additive only, nothing removed or loosened
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency (`refreshDemand`/`refreshPricing`/vote run-twice tests present), money in cents, en/es text (niche labels carry `labelEn`/`labelEs`)
- [x] Decisions recorded where needed (ADR 0015 covers the global-cache design; this review's one open item is tracked as S-34 in `security/v1-review.md`, already present from T-18-1's co-review)

## Optional notes (not blocking)
- `s34.security.test.ts` in my worktree is proof-only, not a deliverable; it is not part of this repo's history and was discarded with the worktree.
- Everything else co-reviewed here (AC1, 2a, 12, 13) is solid: the global-cache/tenant-table split, the mock-visibility predicate, and the permission matrix all match the spec and the wave's hard fences with real tests behind them, not just comments.
