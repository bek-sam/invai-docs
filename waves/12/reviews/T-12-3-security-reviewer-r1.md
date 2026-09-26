# Review of T-12-3 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-foundation on Sonnet 5
- Verdict: **approve**

Risk flag: `auth` (wave.md). Focused on spoofing, atomicity, cross-process correctness and
fail-open safety of the new rate-limit/fairness paths.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show e02fd17 -- src/api/orpc.ts` | `rateLimit` middleware keys on `context.companyId` only; classifies bucket from server-side procedure metadata (`meta.auth`, HTTP method), never from a request header |
| `grep -n companyId src/api/context.ts` | `companyId` is set from the resolved session/station/`me.switchOrg` active-org lookup (`session.companyId`, `active?.orgId`), never read off a client-supplied header |
| Read `TOKEN_BUCKET_SCRIPT`, `AUTH_FIXED_WINDOW_SCRIPT`, `ACQUIRE_SCRIPT` (`lib/ratelimit.ts`, `lib/fairness.ts`) | each is a single Redis `EVAL` doing read+refill+decide+write (or SISMEMBER+SCARD+SADD) atomically — no separate get/set round trip that a concurrent request could race |
| `vitest run src/lib/ratelimit.test.ts src/api/ratelimit.test.ts` (own DB, Valkey db 15) | passes, including "keys by company_id, not IP" and "two 'processes' sharing one Redis see the combined count" |
| `vitest run src/lib/fairness.test.ts` | passes, including the fail-open-on-Redis-error case for `acquireSlot` |
| Read `withFairness` (`lib/fairness.ts`) | slot acquired before `process()`, released in `finally` (covers thrown errors); `SLOT_TTL_SEC=300` on the Redis set as the crash-not-caught-by-finally backstop |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend e02fd17^` | only fail-open mocks of `redis.eval`, which is exactly what AC3 requires as evidence; no loosened assertions |

## Checklist (security-relevant)

- **Atomicity.** Both the token bucket and the semaphore use one Lua `EVAL` for their
  read-modify-write, not `MULTI`/`EXEC` — equivalent atomicity guarantee for this use case (Redis
  runs a Lua script as a single atomic unit; no other client's commands can interleave). Verified
  by reading the scripts directly, not the report's description of them.
- **Key spoofing.** `bucketFor`/`rateLimit` middleware key exclusively on
  `context.companyId`, which is populated in `context.ts` from the authenticated session (user
  session org, station-token lookup, or `me.switchOrg`'s active membership) — there is no code
  path that reads a company/tenant id from a request header or body for this purpose. A caller
  cannot claim a different tenant's (larger) bucket, nor force another tenant into `RATE_LIMITED`,
  by sending a header. `betterAuthConsume`'s key derivation is unchanged from Better Auth's own
  existing (pre-card) logic — this card only swapped the storage backend, not the key.
- **Better Auth Valkey storage across processes.** `customStorage.consume` is called per request
  regardless of which API process handles it, and reads/writes the same Redis key via one atomic
  `EVAL` — confirmed directly with a test that alternates two independent call sites (simulating
  two processes with no shared JS state) against the same key and shows the limit trips on the
  *combined* count (5th of 6), which is impossible under the old per-process `Map`. `secondaryStorage`
  was deliberately avoided (would also swap session/verification-token storage, out of scope and a
  bigger blast radius) — a sound, narrowly-scoped choice.
- **Fairness semaphore release on failure or crash.** `withFairness` releases the slot in a
  `finally` block, so a thrown handler error (including the re-delay's own `DelayedError` — but
  that path releases nothing because the slot was never acquired for a rejected job) still frees
  the slot. For a hard process crash (no JS exception, no `finally` runs), `SLOT_TTL_SEC = 300`
  on the Redis set is the TTL-based backstop the card asks for ("always releases... TTL"). Not
  tested directly (no test kills a worker mid-job to prove the TTL expires and frees the slot) —
  noted below, not blocking, since the mechanism (`EXPIRE` on every acquire) is correct on
  inspection and the try/finally path (the common case) is tested.
- **Fail-open, not fail-closed.** All three new checks (`takeToken`, `betterAuthConsume`,
  `acquireSlot`) return "allowed" on timeout/error, matching the existing PIN-lockout convention
  in the same file. This is the intentionally-chosen tradeoff (availability over strict limiting
  during a Redis outage) and is explicitly what the card asks for; it does mean a sustained Valkey
  outage removes rate limiting and fairness protection entirely (defense-in-depth is the app's own
  authz/tenancy checks, not this layer, during such an outage) — consistent with the rest of the
  codebase's fail-open policy, not a new risk introduced by this card.
- **Poll jitter is a scheduling/fairness concern, not a security boundary** — hash is not
  security-sensitive (doesn't need to be unpredictable), and it's per-connection, not
  cross-tenant, so no spoofing concern.
- **Load-test evidence credibility.** Uses the real queue name/concurrency, a real BullMQ
  `Queue`/`Worker`, and measures wall-clock latency directly rather than asserting a canned number
  — read the script in full, not just the report's table; the methodology supports the reported
  611ms → 309ms improvement.

## Blocking findings
none

## Optional notes (not blocking)
- Add a test that lets `SLOT_TTL_SEC` expire (or shortens it via a param for the test) and
  confirms a crashed-worker's slot is eventually reclaimed, so the TTL backstop is verified rather
  than only inspected. Worth a follow-up card, not a blocker for this one — the try/finally path
  (the common, non-crash case) is well tested, and the TTL mechanism itself (`EXPIRE` set on every
  acquire, including idempotent re-acquires) is correct on inspection.
