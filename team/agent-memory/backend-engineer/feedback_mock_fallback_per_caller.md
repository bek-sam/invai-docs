---
name: feedback_mock_fallback_per_caller
description: Disabling an integration client's mock/placeholder fallback for one caller (e.g. a job) breaks any test that relied on that fallback without mocking the client itself
metadata:
  type: feedback
---

When a client wraps an external service with a "fall back to a mock/placeholder when
unreachable" branch (e.g. `imaging.preview()`'s gray-square PNG), and a card narrows that fallback
to specific callers only (a new option like `allowPlaceholder: false`, used by one caller), check
every test that calls the now-stricter function **directly** (not through a mock) — those tests
were silently depending on the fallback to succeed without a real backing service running, which
is normal for a plain `pnpm test` in this repo (no imaging process is started for unit tests).

**Why:** T-P2-2 round 2 made `renderDesignPreviews` (the catalog preview-render job's own
function) always pass `allowPlaceholder: false` to `imaging.preview()`, per the tech lead's
ruling that a job must never save a permanent placeholder. `service.test.ts`'s own
`renderDesignPreviews` tests called that same function directly and had been passing only because
the old placeholder fallback silently covered for imaging not actually running in the test
sandbox — removing it broke `pnpm test src/modules/catalog` with real `ECONNREFUSED` errors.

**How to apply:** after narrowing or removing a fallback for one call site, grep for other direct
callers of that same function/method in tests, and mock the integration client there the same way
the existing job/queue tests already do (see `jobs.test.ts`'s `vi.mock(".../client", ...)`
pattern), rather than assuming "it passed before, it'll pass now."
