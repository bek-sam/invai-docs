---
name: outbound-http-review-pattern
description: How to verify a new outbound-HTTP integration module (SSRF, key handling, prod-safety) without a live key
metadata:
  type: project
---

For an integrations module with real adapters gated behind a never-set API key (T-18-2 market
providers is the reference case, wave 18, 2026-09-27), a useful, cheap verification set:

1. **SSRF:** confirm the host allowlist check happens before the token-bucket wait and before
   `fetch`, and that `redirect: "manual"` is paired with an explicit rejection of any 3xx status
   (Node's fetch with manual redirect returns the 3xx response rather than throwing/opaquing it —
   don't assume it's blocked just because redirect isn't "follow"). Then grep every adapter file
   for how it builds its request URL: user/tenant data must only ever land in a query value, a
   fixed path segment or a POST body — never in the host/scheme part of the string.
2. **Key leakage:** grep for the pattern `key: \`...${env.SOME_KEY}\`` or similar string
   interpolation feeding a Redis/rate-limit/cache key — a secret used as a cache key ends up in
   Redis, in BullMQ's `failedReason` (often retained for days), and in any log line that includes
   the key. Also force a real `fetch` network failure (point at `127.0.0.1:1` with a fake secret
   in the query string) and check `String(err)` — Node's fetch network-error messages don't
   normally include the URL, but verify it for the actual error class in use rather than assuming.
3. **Prod-safety for optional integrations:** run the env module directly under
   `NODE_ENV=production ALLOW_MOCKS=true` with the outage/test switch set, and check the resolved
   config object (not just the source) — e.g. `env.marketMockFail` should resolve to an empty set
   in prod regardless of the raw env var. Also grep the fixed `PRODUCTION_KEYS` array to confirm
   new optional keys were never added to it.
4. **Mutation-test the regression tests, don't just read them.** For at least the one finding you
   most doubt, temporarily revert the fix in your own worktree, rerun the specific test, confirm
   it fails, then restore. Cheap (one file edit + one test run) and catches a decorative
   "reviewer finding N" test that doesn't actually exercise the old bug. Same rule as
   [[s34-taxonomy-equality-test]], now confirmed useful a second time.
5. **PII/identity stripping across a provider boundary:** the strongest test shape is a stubbed
   response that embeds the sensitive field with an obviously-fake but greppable value (e.g.
   `SellerId: "A_SELLER_1"`), then `JSON.stringify` the returned object and assert the string does
   *not* contain it — stronger than only checking `Object.keys()`, since a key-shape check would
   pass even if the value leaked under a differently-named field.
