# P1 wave plan review — architect

Verdict: **approve-with-changes**

1. `/preview` interface and `imaging.preview`: endpoint shape is fine, but the client signature in
   "Agreed interfaces" is camelCase (`{ fileKey, outKey, maxPx }` → `{ outKey, widthPx, heightPx }`).
   Every existing method in `invai-backend/src/integrations/imaging/client.ts` (compose, nest,
   mockup, qaCheck, cleanAlpha, renderPersonalization, sampleArt — checked all of them) takes and
   returns **snake_case** fields verbatim from the Python wire shape (`file_key`, `out_key`,
   `width_px`, `preview_key`, …) with zero camelCasing anywhere in the file. The new method should
   match: `imaging.preview({ file_key, out_key, max_px? }) -> { out_key, width_px, height_px }`.
   Fix in `wave.md` before T-P1-4 builds against it, or the one odd camelCase method sits
   inconsistently in an otherwise 100%-snake_case client.

2. Per-run test DB + Redis lock: sound, no race found. `vitest.config.ts` doesn't set `pool`, so
   Vitest 5 defaults to `"forks"` (confirmed in `node_modules/vitest/dist/chunks/plugin.d.*.d.ts`).
   Forks inherit the orchestrator's `process.env` at spawn time, spawned per file *after*
   `global-setup.ts`'s `setup()` runs — the same mechanism the code already relies on for
   `NODE_ENV=test` today, so mutating `process.env.TEST_DATABASE_URL`/`TEST_REDIS_URL` there will
   propagate. AC1's instruction to verify this live (not from memory) is correct and sufficient;
   no change needed, but flag in the build report if `pool` is ever changed later (threads would
   need `provide`/`inject` instead). Template-migration advisory lock, Redis `SET NX`+TTL, and the
   stale-DB cleanup (dead pid **and** >1h) all look race-free.

3. File ownership collisions: none. Verified every Owned/Grant path across all 5 cards is disjoint
   — `src/test/**` vs `src/ai/**`/`src/modules/ai/**` vs `src/modules/catalog/**` vs the
   single-line grants on `orders/mapping.ts`, `integrations/imaging/client.ts` (preview method
   only), `db/seed/**` (preview lines only), `integrations/market/http.test.ts` (test file only,
   confirmed `http.ts` uses plain `setTimeout` so fake timers need no product-code change), and
   `modules/market/signals.ts`/`compute.ts`. `invai-imaging` and `invai-floor` are separate repos.

4. T-P1-4's grant split: right-sized. `catalog/jobs.ts` already has the `defineJob`+`onEvent`
   pattern on the existing `design.updated` event (no new contract event needed — confirmed in
   `events.ts` and `catalog/service.ts:196,242`), and `previewKey`/`artworkPreviewKey` are already
   contract fields (`schemas/catalog.ts`, `schemas/orders.ts`) — contracts genuinely stay
   unchanged, as claimed. One gap: AC3's "filled in when the preview lands later" has no granted
   path for the preview job (catalog) to update already-mapped `order_items` (orders owns that
   write) — acceptable only if the report states plainly that pre-existing mapped items keep a
   null preview until re-mapped; this isn't a path/contract gap, just needs to be said, not built.

5. Missing: the "files" risk flag on T-P1-2 and T-P1-4. Decision 0019 names `security-reviewer`
   co-review unconditionally for `files`; `wave.md`'s Co-reviewers section narrows this to "only
   if a new storage path pattern or non-company-prefixed key," which is the tech lead softening an
   owner-decided control, not a routine call. Both cards add real new file-handling surface (a new
   `/preview` endpoint, a new backend client method, a new job writing PNGs) whose tenant isolation
   rests entirely on backend-side key discipline — imaging itself enforces no tenancy (`main.py`
   has no company concept, just the shared-secret header). Require `security-reviewer` as
   co-reviewer on T-P1-2 and T-P1-4 per 0019 as written, or get the owner to record a carve-out
   before these cards are pushed — don't let the primary reviewer alone decide this at review time.

No contract change is needed anywhere in this wave; confirmed by reading the actual schemas, not
just trusting the plan's claim.
