# Review of T-23-8 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-foundation on Opus (card lists sonnet; the high-risk model split doesn't apply, no risk flags)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck`; `pnpm lint` (invai-backend @ 032b9f6) | clean; `Checked 422 files … No fixes applied` |
| `pnpm test --reporter=dot src/db/seed src/modules/digest src/modules/finance` (own `invai_rv238_test`, `TEST_REDIS_URL=…/10`) | 16 files passed, 1 skipped; 111 passed, 2 skipped, 1 todo |
| Fresh scratch `invai_rv238_seed`: `createdb` + `db:migrate` + `db:seed` (imaging up, `SEED_OUTPUT_FILE` in scratchpad) | `digest.build … weekKey 2026-W39 status ready`; `orders 360 items 674 transitions 3903 dueSoon 88` |
| Counts after seed 1 | `digests` 1 (`2026-W39:ready`); `profit_lines` 674 rows / 674 distinct items, net 580048, revenue 1842268 |
| Second `db:seed` | exits early (`Desert Bloom Tees already exists`); digests 1, profit_lines 674 / same sums |
| Scratch probe: `recomputeProfit` for the whole company again (the path the drained `finance.recompute` job takes), then `buildWeeklyDigest` again | `recompute 674`; digest `status: exists`, same id; profit_lines still 674, net 580048 (upsert replaces, no double count) |
| `scan-test-weakening.sh invai-backend 032b9f6~1` | no hits |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Seed calls real `buildDigest` (`weekly-digest.ts:41`) for `lastCompleteWeek(localNow)`, the sweep's own helpers; no inserts. Gives 2026-W39, the week the `digest.spec.ts` and `digest-dates.spec.ts` headers name (as of 2026-09-29). |
| 2 | Yes | Re-seed refuses before touching data; the wrapper called again returns `exists` (my probe and `weekly-digest.test.ts`). |
| 3 | Partly, accepted | Seed counts match the author's run. The only new writes are 674 `profit_lines` (the same upsert the worker would write) and one digest row plus one `digest.ready` outbox event. Steps 8–13 couldn't run on a scratch DB (`e2e/helpers/api.ts:98` reads a fixed seed-output path). Leaving them to the integration gate on a fresh seed is fine: the change only fills early data that the worker would fill anyway. |
| 4 | Not re-run | The author reports 14 passed and 1 skipped (unsubscribe, no `E2E_DIGEST_UNSUB_TOKEN`). I only confirmed that the digest row exists and is `ready`. The gate runs these specs. |

## Blocking findings
none

## Checks
- [x] Only owned paths changed: `src/db/seed/{index,weekly-digest,weekly-digest.test}.ts`
- [x] Nothing outside scope; `modules/digest` and `modules/finance` are unchanged, only called
- [x] No test weakened. The new test fails on the base commit (the module is missing). It covers wrapper idempotency only (quiet company).
- [x] Tenancy: `recomputeProfit` and `buildDigest` run under `withTenant`. `withSystem` is only for `localNow` (pure SQL clock, same as the sweep's `dueShops`), which the seed allows. No new table; cents unchanged; no UI text.
- [x] No decision needed

## Optional notes (not blocking)
- `weekly-digest.test.ts` doesn't cover the profit-before-digest ordering (a non-null margin change). If someone reorders the two calls, nothing fails until E2E.
- The week is based on the date: after 2026-10-05 the seed builds W40. The W39 in the specs appears only in comments (checked with grep); no assertion hardcodes it.
