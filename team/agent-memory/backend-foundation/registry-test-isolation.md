---
name: registry-test-isolation
description: A shared Redis lock-registry's own unit tests must never touch the real registry keys, even for cleanup
metadata:
  type: feedback
---

From T-P1-1 r2 (review finding, B-228, DB-15 Redis lock registry).

A unit test of a shared-registry claim/release module must never touch the real registry keys even
to "clean up after itself" — an `afterEach` doing `KEYS <realPrefix>:*` + `DEL` wiped other live
agents' claims. Fix pattern: thread the registry's key prefix (and/or DB) through as an optional
param, defaulting to the real one for production callers, and have the test pass a unique prefix
(`<prefix>-ut-<pid>-<uuid>:`) so every assertion and cleanup is scoped to keys only that test run
created — reusing the same DB (15) is fine, isolation comes from the prefix.

Proved the fix with two real concurrent full `pnpm test` runs plus a 5s-interval poll of the real
registry logged to a file (152 polls over ~12.7 min, grepped for a zero-count line) instead of a
Monitor heartbeat on every poll — Monitor fired a notification per 5s poll and had to be
stopped/restarted with an explicit `N % 12` throttle (heartbeat every 60s + immediate alarm only on
an actual empty reading) to avoid flooding the conversation.
