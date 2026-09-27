---
name: shared-ratelimit-key-across-tests-causes-30s-hang
description: reusing the same connection/tenant id across tests that hit a real per-provider rate limiter makes a later test wait out an earlier test's token bucket
metadata:
  type: feedback
---

`src/integrations/suppliers/ratelimit.ts`'s `takeToken(key, {capacity, perMs})` is a real Redis
token bucket, not mocked in unit tests (only the outbound `fetch` is stubbed). If two tests in the
same file use the same rate-limit key (e.g. built from a shared `conn.id`) against a
capacity-1 bucket, the second test blocks until the bucket refills — for a 30s-per-token limiter
that's a real 30-second test hang / timeout, not a logic bug.

**Why:** Hit this in T-18-2's `providers/providers.test.ts` (Amazon pricing adapter, capacity 1
per 30_000ms, keyed `market:amazon_pricing:<connId>`): two `it()` blocks shared one hardcoded
`conn.id`, and the second one always timed out at exactly 30000ms.

**How to apply:** When a test calls real code that rate-limits on `<source>:<some-id>`, generate a
fresh id (`crypto.randomUUID()`) per test rather than reusing one module-level constant, so each
test gets its own bucket. This applies to any adapter built on `suppliers/ratelimit.ts` or
`lib/ratelimit.ts`, not just market providers.
