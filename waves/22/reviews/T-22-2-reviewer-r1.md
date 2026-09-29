# Review of T-22-2 (round 1)

- Reviewer: reviewer on opus · Author: backend-foundation on fable · Commits: invai-backend `3b50fb8`, `6a8856c` (T-22-3 commits in the same tree not reviewed here)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (shared tree, clean status at the time) | tsc exit 0; `biome check .` 410 files, no fixes |
| `vitest run --reporter=dot src/db src/worker src/lib/queues.test.ts src/modules/tenancy` on `invai_t22_2r`, Redis DB 10 | `Test Files 23 passed (23)`, `Tests 114 passed (114)`, 56.5 s |
| Canary: `ALTER TABLE bins ADD CONSTRAINT canary_single_fk FOREIGN KEY (order_id) REFERENCES orders(id)`, then `fk-coverage.test.ts` | 2 of 3 fail (`bins(order_id) -> orders(id)`, `canary_single_fk: orders(id)`); canary dropped |
| Script: 0030 SQL vs 0030 snapshot; 0029 vs 0030 snapshot FK actions; 0030 vs 0031 names | 49 FKs, 0 mismatches (table, columns, target, ON DELETE; every SET NULL lists the non-`company_id` column); no ON DELETE change vs 0029; 18 new unique keys all created before the FKs; 0031 VALIDATEs exactly the 49 names; both files start `SET LOCAL lock_timeout = '5s'` |
| `drizzle-kit generate` in a scratch worktree at `3b50fb8` | `No schema changes, nothing to migrate` (worktree removed) |
| SET NULL probe on `invai_t22_2r` (txn, rolled back): delete a station with scans | scan kept `company_id`, `station_id` nulled |
| `createdb -T invai invai_t22_2rdev` (374 orders, 30 migrations) + `time tsx src/db/migrate.ts` | 0.58 s wall for 0030–0033; 58/58 composite FKs `convalidated`; 0 unvalidated FKs; no cross-tenant row |
| API `PORT=3141` on the copy (pid 51137, stopped): PATCH `/api/v1/me/org` | owner `{shipsSaturday:true,transferAgeWarnDays:45}` → both returned, `productionPartner` kept, DB `true\|45`; `transferAgeWarnDays:0` and `"x"` → `BAD_REQUEST`; presser → `FORBIDDEN org.manage` |
| `pg_proc.proleakproof` (AC5 evidence) | `textlike`, `texticlike`, `similarity_op` = f; `texteq`, `uuid_eq`, `starts_with` = t (matches the report) |
| `scan-test-weakening.sh invai-backend origin/main` | T-22-2 files: additions only (3 removed assertions are T-22-3's `label-safety.test.ts`, already reviewed); no skips/snapshots/config |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | 49 composite FKs + 18 `(company_id,id)` keys, NOT VALID then VALIDATE under 5 s lock_timeout; 0.58 s on the seeded copy |
| 2 | yes | canary single-column FK turns the test red; cross-tenant insert refused with 23503 under `withSystem` (green in my run) |
| 3 | yes | `SET LOCAL statement_timeout = 0` + `lock_timeout '10min'` inside the lock txn; `migrate.test.ts` waiter with `-c statement_timeout=200` still waits 600 ms and acquires (green) |
| 4 | yes (caveat) | per-queue settings spread into `worker/index.ts:39`; `stall.test.ts` runs = 2 then `failed` (green). No per-job p95 exists; the lock-renewal reasoning is sound |
| 5 | descoped (tech lead, B-199) | evidence honest (leakproof check above); no trigram/GIN statement in 0030/0031 or the schema diff |
| 6 | yes | curl above + `org-settings.test.ts` |
| 7 | yes (scoped) | my targeted run green incl. `rls-coverage`; full suite left to the gate |

## Blocking findings
none

## Checks
- [x] Owned paths only (plus doc-only `src/modules/README.md` and the `CompanySettings` type AC6 needs); nothing outside scope, no half-built AC5
- [x] Tests exercise the behavior, none weakened; tenancy: updateOrg under `withTenant`, no new request-path `withSystem`; money/UI n/a
- [x] Decisions recorded (report "Decisions"; AC5 → B-199)

## Optional notes (not blocking)
- The 0030 header says `fk-coverage.test.ts` "checks the shape", but it doesn't check the SET NULL column list. A future drizzle regeneration of any of the 11 SET NULL FKs would emit plain `SET NULL`, and deleting the parent would then fail on NOT NULL `company_id`. Suggest asserting `confdelsetcols` is set whenever `confdeltype = 'n'`.
- `stall.test.ts` builds its own Worker, so the `worker/index.ts` wiring is verified only by reading it. 0030 and 0031 still run in one transaction, so the NOT VALID split doesn't reduce lock time yet (this is documented).
