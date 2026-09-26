# Review of T-12-3 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-foundation on Sonnet 5
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend log --oneline e02fd17^..1d077e2` | 2 commits, T-12-3 only |
| `git -C invai-backend diff --stat e02fd17^..e02fd17` | 13 files, matches owned+coordination paths |
| `git -C invai-backend diff --stat e02fd17..1d077e2` | `src/lib/queues.ts`, `src/modules/ai/jobs.ts` only (out-of-owned-path, grant confirmed in `wave.md`) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend e02fd17^` | hits are only `vi.spyOn(redis, "eval")` fail-open mocks (AC3's own required test shape); 0 assertions removed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 1d077e2^` | no hits |
| `vitest run src/lib/ratelimit.test.ts src/lib/fairness.test.ts src/modules/channels/jobs.test.ts src/api/ratelimit.test.ts src/lib/queues.test.ts` (own DB `invai_review_t123`, Valkey db 15) | 5 files, 28 tests passed |
| `git archive e02fd17^` extracted to `/tmp/review-T-12-3` | `src/lib/fairness.ts` does not exist on base — new tests can't pass without the change (not rubber-stamped) |
| Read `scripts/t12-3-fairness-loadtest.ts` in full | real BullMQ `Queue`/`Worker` on the real `sync` queue name/concurrency, obliterated before/after; before/after numbers in the report (611ms → 309ms) match the script's methodology |
| Cleanup | dropped `invai_review_t123`, flushed Valkey db 15 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Per-tenant token bucket, Valkey | yes | `lib/ratelimit.ts` `TOKEN_BUCKET_SCRIPT`, one atomic `EVAL`; `lib/ratelimit.test.ts` proves N+1 denied, waits `retryAfterSec`, next admitted; separate buckets/companies independent |
| 2. Better Auth → Valkey storage | yes | `auth.ts` `rateLimit.customStorage: { consume: betterAuthConsume }`; `ratelimit.test.ts` "two 'processes' sharing one Redis" test proves combined count trips at 5, not 2×5 |
| 3. Fail-open on Redis trouble | yes | `withTimeout` (500ms) + try/catch around every new check (`takeToken`, `betterAuthConsume`, `acquireSlot`); tests mock `redis.eval` to hang/reject, assert `allowed: true` |
| 4. Per-tenant job fairness semaphore | yes | `fairness.test.ts` "tenant fairness under load": A enqueues 200, B enqueues 5, B completes within an 8s concrete bound while A's backlog is still unfinished |
| 5. Bulk vs interactive priority | yes | `BULK_PRIORITY=10`; wired into `csv_import` (existing), `reports` default, `ai.generateListingDrafts` (`1d077e2`); test: interactive job lands before position 25 of a 50-job bulk backlog |
| 6. Poll jitter | yes | `pollJitterMs` FNV-1a hash mod `POLL_EVERY_MS`; `jobs.test.ts`: >50 distinct offsets of 100, same id stable across calls |
| 7. Load-test evidence | yes | `scripts/t12-3-fairness-loadtest.ts`, real BullMQ on real queue name; report table matches script output shape |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`src/lib/ratelimit.ts`, new `src/lib/fairness.ts`, `src/auth.ts`) plus the named coordination files (`api/orpc.ts`, `api/context.ts`, `api/app.ts`, `worker/index.ts` processor-only, `modules/channels/jobs.ts` poll jitter); `1d077e2`'s two extra files are grant-approved in `wave.md` ("Grant approved after the fact... T-12-3 `1d077e2`")
- [x] Nothing outside scope — sharding by `hash(companyId) % K` correctly left unbuilt (card says build only if the load test shows the semaphore isn't enough; it doesn't)
- [x] Tests exercise the behavior, and none were weakened (scan clean both commits; new-file imports don't resolve on base code, so tests can't pass pre-change)
- [x] Tenancy/idempotency: no new tables (N/A for RLS); fairness re-delay uses `moveToDelayed`+`DelayedError` (BullMQ's `skipAttempt` path — doesn't burn a retry attempt, confirmed by author against `node_modules`, and consistent with BullMQ's documented `DelayedError` handling)
- [x] Decisions recorded: `customStorage` vs `secondaryStorage` choice, and `capForQueue` scaling vs the card's literal "at most 2", both documented in code comments and the report

## Optional notes (not blocking)
- `capForQueue`'s `Math.max(1, concurrency - 1)` deviates from wave.md's illustrative "at most 2 render jobs" — well-justified (a flat 2 regressed an uncontested tenant on `sync`, concurrency 10) and disclosed prominently in the report; not a scope issue since the card's own AC4 wording ("at most K concurrent jobs... K") leaves K to the implementation.
- The semaphore's crash safety net (`SLOT_TTL_SEC = 300`) is generous; a worker that hard-crashes holds a slot for up to 5 minutes before it's released. Acceptable for this wave — no test exercises the TTL expiry path itself (only the try/finally release path is tested), which is a gap I'd ask for in a future round if the semaphore proves under-provisioned.
