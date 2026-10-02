---
name: imaging-guard-middleware-deny-by-default
description: invai-imaging's GuardMiddleware is deny-by-default (OPEN_PATHS allowlist of exemptions), so new routes inherit shared-secret auth automatically; no per-route auth test needed.
metadata:
  type: project
---

`invai-imaging/app/guard.py`'s `GuardMiddleware` requires `X-Imaging-Secret` on every path except
the `OPEN_PATHS` allowlist (`{"/health"}` as of 2026-09-30). A new route (e.g. `POST /preview`,
T-P1-2) gets the same auth as `/compose` automatically, with zero route-specific wiring — the
author doesn't need to (and the T-P1-2 diff didn't) touch `guard.py` at all.

**How to apply:** when co-reviewing an imaging card that adds a route, don't require a new
401/wrong-secret test for that specific route. `tests/test_limits.py`'s auth tests exercise the
mechanism via `/nest`/`/compose` once, which proves the path-agnostic middleware for every
current and future route. Still worth a quick live curl against the *new* route specifically
(no header → 401, right secret → 200) to prove the route wasn't accidentally added to
`OPEN_PATHS` or given its own early-return before the middleware runs.

Separately: `HEAVY_PATHS` (`{"/compose", "/render/personalization"}`) is an *opt-in* allowlist,
the opposite polarity from `OPEN_PATHS` — a new endpoint that does real decode/transform work
(e.g. `/preview` calling `to_srgba()`/`icc_transform`) is **not** covered by the per-process
heavy-job concurrency limiter unless explicitly added. Check this separately for any new route
that decodes/transforms images, especially ones with input-dependent cost (ICC transforms, large
PDFs) — it's an easy miss since it isn't deny-by-default like auth is.

See also [[imaging-key-trust-model]].
