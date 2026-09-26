# T-9-5 report: imaging limits and service auth (B-19)

**Status:** done, not pushed. Owner: imaging-engineer + platform-sre (opus).

| Repo | SHA | What |
|---|---|---|
| invai-imaging | `87e01e0` | auth middleware, heavy-job limiter, bounds, format allowlist, pixel caps (incl. PDF), dev-flag gating, render time, Dockerfile |
| invai-backend | `2b98c13` | `client.ts` `call()`: `X-Imaging-Secret` + 429/Retry-After retry; `env.ts`: `IMAGING_SHARED_SECRET` in `PRODUCTION_KEYS` |
| invai-contracts | `311d357` | `SheetSpec.widthIn.max(60)`, `.maxLengthIn.max(240)`, `.dpi.min(36).max(1200)` |

## What was built, per acceptance criterion
1. **Concurrency.** `app/guard.py` is a pure ASGI middleware. `/compose` and `/render/personalization` take a slot from a per-process counter (`IMAGING_MAX_HEAVY_JOBS`, default 2). With none free the answer is `429 {"detail": "imaging is busy; retry later"}` + `Retry-After: IMAGING_RETRY_AFTER_S` (default 5). It's sent before the body is read or any work starts, so a retry is always safe. The backend `call()` retries a 429 up to 5 times, waiting Retry-After (seconds or HTTP date, clamped 0.1–30 s), then surfaces `ImagingError(429)`.
2. **Input limits.**
   - Pixel cap: `app/limits.py` `pixel_budget_error`, checked in `vips.load()` from the lazy header before any pixel decode (raster and SVG). `IMAGING_MAX_DECODE_PIXELS` defaults to 570M (22 × 240 in × 300 DPI × 1.2, per the imaging skill). A 100k × 100k PNG header is refused in < 1 s.
   - Allowlist: `sniff_format` accepts PNG, JPEG, WebP, TIFF, SVG and PDF by magic bytes. `load()` calls that format's own loader (`pngload`, etc.), never `new_from_file`. `pyvips.block_untrusted_set(True)` is also set, with only `VipsForeignLoadSvg` unblocked (librsvg is marked untrusted; SVG art is T-9-1's feature).
   - Declared type = the key extension (backend keys are `…/<uuid>.<ext>`, `lib/s3.ts:51`). A mismatch is refused on every download: `_CheckedStorage` wraps storage for `/compose` and `_download` for the rest. `/qa/check` reports it as a 200 `unreadable` issue, keeping the skill's QA rule; everything else returns 422.
   - Bounds: compose `width_in ≤ 60`, `length_in ≤ 240`, DPI 36–1200 (already), placements ≤ 10,000, `x/y ≥ 0`, sizes ≤ 240, label strings capped. Nest `sheet_width_in ≤ 60`, items ≤ 5,000 and total copies ≤ 10,000. Personalization has ≤ 50 slots and values, each value ≤ 1,000 chars, and font/stroke/lines capped. Every key is 1–512 chars (matches `isSafeKey`), and QA targets are ≤ 240.
   - Contracts mirror: `SheetSpec` gained width ≤ 60, length ≤ 240 and DPI 36–1200. `PersonalizationTemplateInput` already had them from T-9-4 (confirmed).
3. **Service auth.** `X-Imaging-Secret` on every path except `/health`. It is compared as sha256 + `hmac.compare_digest` over each configured secret; a comma-separated list allows rotation. A missing or wrong secret gets 401 before the body is parsed. The dev default is `invai-imaging-dev-secret` on both sides. `IMAGING_ENV=production` refuses to start on the dev secret or one under 32 chars, and the Docker image sets `IMAGING_ENV=production`, so it fails closed. Backend `IMAGING_SHARED_SECRET` is in `PRODUCTION_KEYS`. With `ALLOW_MOCKS=true` and no secret, production sends no header and gets 401 (fails closed, no dev fallback).
4. **Test endpoints.** `/labels/mock` and `/sample-art` return 404 unless `IMAGING_DEV_ENDPOINTS=true` (a request-time dependency).
5. **Process safety.**
   - uvicorn `--timeout-graceful-shutdown 30` in the Dockerfile. The lifespan logs any heavy jobs still running at exit.
   - Docker `HEALTHCHECK` on `/health` via Python (slim has no curl). The image also runs as a non-root user (`imaging`, uid 10001).
   - `X-Render-Ms` on every response. `render_ms` in `/compose` (from compose's own `seconds`, audit B-103) and `/render/personalization` JSON.
6. **Tests.** New `tests/test_limits.py` has 28 tests: missing/wrong/right secret, auth before body parse, rotation, the production guard, 429 + Retry-After and slot release, compose/nest/personalization bounds, placement cap, PNG header bomb, config-driven cap, oversized SVG, the PDF page budget (asserts pdfium's `render` is never called), non-allowlisted formats, extension/magic mismatch (unit + API for QA, mockup and compose), and dev-endpoint gating. Backend `client.test.ts` has 5 tests: header sent, 401 surfaced, 429 retried with Retry-After waits, retry budget exhausted, and Retry-After parsing.
7. **PDF pixel budget.** `pdf_input.rasterize_pdf` checks page width × height (pt → in) × DPI against the same cap before `page.render`. The error is clear, e.g. `pdf page (200.00 x 200.00 in at 300 DPI) is 60000 x 60000 px (3600M pixels), over the 570M pixel limit`.

## Verification
- imaging: `uv run pytest` → **99 passed**; `ruff check` clean. The staged tree alone (checked out without T-9-2's uncommitted edits) also gives 99 passed. `ruff format --check` flags only `app/labels.py`, which was already unformatted at HEAD (T-6-2, not mine).
- backend: `tsc --noEmit` clean, biome clean on my files. vitest (own DB `invai_t95`, dropped): vendors + production + imaging client + env → **9 files, 62 tests passed**.
- contracts: typecheck and tests (31) pass. `pnpm lint` fails on `sheetSpecPdfCapError`'s line length (T-9-3's line, format only, not mine). Flagged below.
- **Live on port 8195** (`IMAGING_MAX_HEAVY_JOBS=1`, `RETRY_AFTER_S=1`, MinIO):
  - `/health` 200 without a secret; `/nest` 401 without one, 200 with one plus `x-render-ms`.
  - 3 concurrent 22 × 101 in / 300 DPI / 80-placement composes through the real backend client: imaging logged 7 × 429, the client logged `imaging busy, retrying` and all 3 completed (6600 × 30300 px) serially.
  - SIGTERM during a 22 × 201 in compose: uvicorn waited, and the compose returned 200 (`render_ms: 2803`) before a clean exit.
  - `IMAGING_ENV=production` with the dev secret: `RuntimeError: Refusing to start: IMAGING_SHARED_SECRET must be set …`.
- **Docker:** image built; the container runs as `user=imaging` and reports `healthy`. Inside it, `/sample-art` → 404 (flag off) and `/nest` without a secret → 401. `docker stop` shut it down cleanly, and the container refuses to start without a secret. Image removed afterwards.
- Budget: no change to the compose/nest pixel pipeline. The loader is the same PNG loader, now called directly, and the middleware adds microseconds. RSS/time for the full-sheet case wasn't re-measured before and after, because that needs a stash-free baseline. The live 22 × 201 in compose took 2.8 s.
- Cleanup: imaging stopped, `t95/` MinIO objects deleted, `invai_t95` dropped, temp files removed.

## Threat model (short)
| Entry | Caller | Threat | Control | Test |
|---|---|---|---|---|
| all imaging POSTs | backend (API, worker) | anyone on the network renders or reads any bucket key | shared secret, constant time, 401 before body | `test_missing_auth_header_is_401`, `test_wrong_secret_is_401`, `test_rejected_before_body_is_parsed` |
| production deploy | infra | ships with the public dev secret | imaging refuses to start (`IMAGING_ENV=production` baked into the image); backend guard | `test_production_refuses_to_start_on_dev_secret`, `env.test.ts` |
| `/compose`, `/render` | backend | memory exhaustion from parallel 240 in sheets | per-process slot limit, 429 + retry | `test_heavy_jobs_over_the_limit_get_429_with_retry_after` |
| art decode | a shop's upload | decompression bomb (PNG/SVG/PDF) | header pixel cap; PDF page × DPI budget before pdfium | `test_oversized_png…`, `test_oversized_svg…`, `test_pdf_page_over_budget…` |
| art decode | a shop's upload | exotic or vulnerable loader, or a renamed file | magic-byte allowlist, per-format loader, untrusted loaders blocked, extension must match | `test_formats_outside_the_allowlist…`, `test_wrong_format_through_the_api` |
| `/labels/mock`, `/sample-art` | anyone with the secret | fake labels or art in production | 404 unless dev flag; image default off | `test_dev_endpoints_are_404…` |

Worst remaining outcome: a leaked shared secret lets a caller on the private network read or overwrite arbitrary bucket keys through imaging. Keys aren't tenant-scoped at imaging; that's the backend's job (`isCompanyKey`). Severity is Medium while imaging stays internal-only.

## Scope notes and follow-ups (for the tech lead)
- **Files touched beyond the literal grant:**
  - `app/vips.py` `load()` and `app/pdf_input.py` (T-9-1's files; small hunks). AC2's "libvips limit" and AC7 live there, so the card requires them.
  - New `app/limits.py` and `app/guard.py`.
  - `tests/conftest.py` (+2 lines: dev flag) and the `tests/test_api.py` client fixture (+secret header).
  - `README.md` (env table) and `.env.example`.
  - The local, uncommitted `invai-imaging/.env` also got `IMAGING_SHARED_SECRET` and `IMAGING_DEV_ENDPOINTS=true`, so `dev.sh` and the seed keep working.
- **T-9-2's uncommitted `header_height_in` lines in `app/main.py` were left unstaged** (staged via a filtered blob). T-9-2 can commit its 4 lines on top of `87e01e0`.
- **Infra follow-up (not granted):**
  - `sst.config.ts`: set `IMAGING_SHARED_SECRET` (the same secret) on api, worker and imaging. Set the ECS stopTimeout ≥ 35 s.
  - `local/docker-compose.yml` `full` profile: imaging now needs `IMAGING_ENV=development` (or a real secret) plus `IMAGING_DEV_ENDPOINTS=true`, and api/worker need the matching secret.
  - Staging with `ALLOW_MOCKS=true` uses the mock carrier, which needs `IMAGING_DEV_ENDPOINTS=true` on imaging.
- The backend `.env.example` wasn't changed; the dev default needs no entry.
- The backend client's zod schemas drop `render_ms` (not granted; add `render_ms: z.number().optional()` if we want it logged).
- Lint debt, not mine: `invai-contracts` `sheetSpecPdfCapError` needs `biome format` (T-9-3). `invai-imaging/app/labels.py` needs `ruff format` (T-6-2). Both fail their repo's CI format check.
