# Review of T-20-5 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: backend-foundation on Fable 5.1
- Verdict: **approve**
- Commit reviewed: `invai-backend` `8ffff2b` (parent `8fdc733`, the round-1 commit; three other cards' commits landed on `main` in between — `2cda6e2`, `076dd69`, `d6a19f1`, `8814acb` — none of which touch this card's files)

## Evidence I re-ran
All runs used `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` → `invai_t20_rev5c` (own scratch DB, dropped after), `REDIS_URL=redis://localhost:6379/11`. DB 11 held 125 stale keys (120 `rt:company:*` stream keys + 5 `bull:<queue>:meta`) from an earlier, incomplete r2 attempt, with **no live client attached** (`client list` on DB 11 showed only my own connection); I flushed it before use and again at cleanup, per the task's instruction to use this DB.

| Command | Result |
|---|---|
| `git show --stat 8ffff2b` / `git diff --stat 8ffff2b~1 8ffff2b` | `src/db/reset.test.ts`, `src/db/reset.ts`, `src/db/seed/builder.ts`, `src/db/seed/sweep-race.test.ts` (new), `src/modules/README.md` — all inside owned paths, nothing else |
| Read the diff (`git show 8ffff2b`) | `upsertAlerts` targets `[alerts.companyId, alerts.dedupeKey]` — matches the unique index in `schema/tenancy.ts:435`; `inventory_settings` conflict target `[t.companyId]` matches `schema/inventory.ts:140` (`uniqueIndex().on(t.companyId)`); `usage` conflict target `[usage.companyId, usage.period]` matches `schema/billing.ts:88`. `db:reset`'s call site (`reset.ts:91`) still calls `obliterateQueues()` with no `prefix`, so production behavior against the real `bull:` queues is unchanged; only the test now runs under `bull-t20-5-test`. |
| `node_modules/.bin/vitest run src/db/seed/sweep-race.test.ts src/db/reset.test.ts` (fixed code, own DB/Redis) | `Test Files 2 passed (2)`, `Tests 3 passed (3)` |
| Same test file run against the r1 base code (`git worktree add --detach ../invai-backend-rev5c 8fdc733`, symlinked `node_modules`, copied only `sweep-race.test.ts` in, `.env` copied) | `Test Files 1 failed`, `Tests 1 failed`: `duplicate key value violates unique constraint "inventory_settings_company_id_index"` at `builder.ts:308` (`tx.insert(inventorySettings).values(...)` with no conflict clause) — the exact failure the author's report and r1's finding describe, on the code as it stood before this fix |
| `pnpm typecheck` (invai-backend) | `tsc --noEmit` exit 0, clean (the r1-reported T-20-3 typecheck breakage is gone — that file has since been committed/fixed by its own owner, unrelated to this card) |
| `pnpm lint` (invai-backend) | `Checked 395 files in 232ms. No fixes applied.` |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 8fdc733` | Flags 8 removed assertions across the full range since `8fdc733`, but only 3 are in this card's commit (`reset.test.ts`): `scanCount("bull:*")` → `scanCount(`${PREFIX}:*`)`, `scanCount(`bull:${name}:*`)` → prefixed equivalent, `obliterateQueues()` → `obliterateQueues({ prefix: PREFIX })` for the production-refusal check. All three are the r1 non-blocking note's own fix (scope the test to its own BullMQ prefix so it stops touching a dev worker's real queues) with an equivalent assertion on the new prefix, not a loosened one; the production-refusal test still asserts the same throw. The other 5 removed-assertion hits are in `digest/*` and `market/*` files from the three unrelated commits noted above — not this card's diff. |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | r1's blocking finding (scheduled sweeps writing `alerts`/`inventory_settings` mid-seed) is fixed by upserts on the same natural keys the sweep uses; the new regression test reproduces the failure on the base code and passes on the fix (re-run above). The report's own `sweep-race.test.ts` full-seed exercise (runs C/C2 vs D/D2) is consistent with the diff and not something I needed to re-run given the unit-level proof; scope note below. |
| 2 | Yes (carried from r1, untouched by r2 except the test's own prefix) | `db:reset`'s call site is unchanged; `reset.test.ts` now proves the same drain behavior under a scoped prefix so it no longer risks a dev worker's real `bull:` queues on shared Redis (r1's own non-blocking note, now addressed). |
| 3 | Yes (unaffected by r2's diff; not re-verified live per the task's scope-down) | The changed code paths (three upserts) don't touch rendering or counts; r1 already verified imaging/counts on the outbox-hold fix, and this round adds no new phase or render logic. |
| 4 | Yes (unaffected) | No stock_levels logic touched in this round. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed: `src/db/seed/builder.ts`, `src/db/seed/sweep-race.test.ts` (new), `src/db/reset.ts`, `src/db/reset.test.ts`, `src/modules/README.md` (docs, already accepted by the tech lead per r1).
- [x] Nothing outside scope — the three upserts and the `reset.ts`/`reset.test.ts` prefix change are exactly r1's blocking finding and non-blocking note, nothing more.
- [x] Tests exercise the behavior and none were weakened: `sweep-race.test.ts` is new and fails on the pre-fix code for the right reason (re-run above); the three "removed" assertions in `reset.test.ts` are like-for-like moves to a scoped prefix, not loosened checks.
- [x] Tenancy: the three upserts run inside the same `withTenant`-scoped transaction the rest of `buildShopData` already uses; no new tables, no new `withSystem`.
- [x] Idempotency: all three conflict targets match the real unique indexes backing the natural keys the sweep and the seed both write to (verified against `schema/tenancy.ts`, `schema/inventory.ts`, `schema/billing.ts` above) — an upsert here can't create a second row or silently drop the seed's own values (`usage`'s `set` always writes the freshly-counted numbers; `alerts`'s `set` always writes the seed's row via `excluded.*`).
- [x] Decisions: card-local, documented in the report; no ADR needed.

## Optional notes (not blocking)
- I found an orphaned `tsx src/worker/index.ts` process (pid 15611, started 12:01AM, connected to Postgres and Redis DB 0) unrelated to any DB or Redis slot I used — likely left over from one of the two incomplete earlier r2 attempts the task mentioned. I didn't touch it (read-only, not mine to kill), but the tech lead may want to check it isn't double-processing jobs on the shared dev worker's queues.
- I did not re-run the report's full live-seed-beside-a-worker exercise (runs A–D2) per the task's explicit instruction to skip live-worker reproduction; the unit-level regression test plus the confirmed base-code failure is sufficient evidence for AC1 in this round, since r1 already covered the broader seed/worker interaction end to end.
