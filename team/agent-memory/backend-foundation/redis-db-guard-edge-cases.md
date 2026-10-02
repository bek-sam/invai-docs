---
name: redis-db-guard-edge-cases
description: B-205 — number-parsing and identity-check pitfalls when guarding against accidental use of Redis DB 0 or the dev Postgres DB in tests
metadata:
  type: feedback
---

From T-23-0 r2/r3 (Redis test-DB redirect and dev-DB guard, B-205).

- Don't parse a URL path with `Number(path)` to decide "did the caller already pin a DB":
  `Number("0/")` is `NaN`, `Number("0.5")` is `0.5`, `Number("0x1")` is `1` (hex strings parse) —
  all three read as "non-zero, already pinned" and escape a DB-0 redirect meant to catch every
  DB-0 spelling. Anchor on the literal shape instead (`^[1-9]\d*$`), not on matching the downstream
  library's own parser (ioredis uses `parseInt`, which has the same holes for `/0/` and `/0x1`).
  When testing "does X get redirected", assert the literal redirected value, not a loose predicate
  (`!== 0`) that the bug itself can also satisfy.
- A guard meant to refuse a specific database by identity (the dev DB) must check identity even
  for values an "explicit pin wins" exemption would otherwise trust — `assertTestDatabase` trusted
  any URL `=== TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` outright, so pinning the dev URL by
  mistake bypassed the whole guard. Fix: check the forbidden identity first, unconditionally,
  before any pin/opt-in exemption.
- A bare `/test/i` substring match matches `invai_latest`/`contest`; use a segment-boundary regex
  (`(^|_)test(_|$)`) when the safe-list is meant to be "test" as a whole word, not a substring.
