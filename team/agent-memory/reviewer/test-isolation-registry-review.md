---
name: test-isolation-registry-review
description: Reviewing per-run test isolation (DB/Redis claims) - the infra's own tests can wipe the shared claim registry; prove it with a live registry poll during concurrent runs
metadata:
  type: feedback
---

2026-09-30 T-P1-1 r1 (changes-required): `claimTestRedisDb` itself was correct, but its test file's
`afterEach` did `KEYS test-redis-db-lock:*` + `DEL` on the real DB-15 registry, wiping every live
run's claim. Both concurrent runs still passed, so a green AC7 does not prove isolation.

**Why:** tests for a lock/registry usually run against the same shared registry they protect.

**How to apply:** for any lock, claim or registry in shared infra, grep its tests for broad cleanup
(`keys(`, `del(`, `flushdb`, `DROP ... IF EXISTS` on fixed names, "assert registry is empty"). During
the concurrent runs, poll the registry in the background every 2 s into a /tmp log and check that no
live run's claim disappears. Related: [[shared-infra-contention-review]].
