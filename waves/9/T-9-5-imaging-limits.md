# T-9-5: Imaging limits and service auth (B-19, plus §A-INF B-12, B-13, B-16)
## Acceptance criteria
1. **Concurrency:** a per-process limit on heavy jobs (compose, render), from config. Excess requests get 429 with Retry-After, and the backend client retries.
2. **Input limits:**
   - a pixel cap on decode (the libvips limit);
   - a format allowlist, where magic bytes must match the declared type;
   - input bounds on `/compose`, `/nest` and `/render` (width, placements count, values, DPI 36–1200, width ≤ 60 in).
   The contracts gain the same bounds.
3. **Service auth:** a shared-secret header between the backend and imaging (from env), with constant-time comparison. Requests without it get 401. Dev uses a default secret, and production requires a real one (add it to T-1-1's production key guard).
4. **Test endpoints:** `/labels/mock` and `/sample-art` are disabled unless a dev flag is set.
5. **Process safety:** graceful shutdown with a timeout, a Docker HEALTHCHECK, and render time returned in responses.
6. **Tests:** oversized input, a wrong format, a missing auth header, the concurrency limit.

## Plan review r1 — files, sequencing, gaps, testability
Runs **solo, last** (see `wave.md` §Plan review r1) — it wraps `app/main.py` with auth/concurrency/bounds/dev-flag gating across the whole app, so it should land once the parallel batch's new endpoint fields (`ComposeRequest`, `NestRequest`, `SlotModel`/`TemplateModel`) are stable, not churn against them mid-flight. It's opus and the highest-risk card, so it also gets the smallest, most isolated diff window.

**Owns:** `app/main.py` (auth dependency, concurrency limiter, bounds, dev-flag gating for `/labels/mock` and `/sample-art`), `app/config.py`, `Dockerfile` (HEALTHCHECK). **Narrow grant:** `invai-backend/src/integrations/imaging/client.ts`'s `call()` function only, for the 429/Retry-After retry in AC1 — that's outside invai-imaging and not owned by any other card; don't route around it, this is the explicit grant.

**AC2 concrete gaps to close before the "oversized input" test is writable:** as of this read, `ComposePlacementModel`'s `placements: list[...]` has no `max_length`, and `ComposeRequest.width_in`/`NestRequest.sheet_width_in` have no `le=60` (only `gt=0`) — DPI bounds (36–1200) are already present on `ComposeRequest`/`PersonalizationRequest`. Add the missing bounds first, then the test.

**Contracts mirror:** the same width ≤ 60in and DPI 36–1200 bounds belong on `invai-contracts/src/schemas/vendors.ts` (`SheetSpec.widthIn`, `.dpi`) and `schemas/personalization.ts` (`PersonalizationTemplateInput.widthIn/heightIn`, `.dpi`) — already specified in `wave.md`; this card doesn't own those files but should confirm at review time that T-9-2/T-9-3/T-9-4 actually added them.
