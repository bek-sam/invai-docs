# Review of T-9-5 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: imaging-engineer + platform-sre on Opus
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-imaging log --oneline -3` / `show --stat 87e01e0` | matches report's file list |
| `cd invai-imaging && uv run ruff check .` | All checks passed |
| `cd invai-imaging && uv run pytest -q` | 102 passed |
| `cd invai-backend && npx vitest run src/integrations/imaging/client.test.ts src/env.test.ts` | 2 files, 15 passed |
| `cd invai-contracts && npx vitest run` | 4 files, 31 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-imaging origin/main` | hits, but all in files/lines T-9-5 did not touch (test_compose.py/test_nesting.py churn is T-9-2's label_height_in default change, not in `87e01e0`'s diff) — none in `tests/test_limits.py`, `tests/conftest.py`, `tests/test_api.py` |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | one hit is a false-positive keyword match on `it("retries a 429 …")`; the untracked `orpc.test.ts` hit is unrelated WIP, not part of `2b98c13` |
| Sanity-checked new tests fail pre-change: archived imaging at `a5fd3b5` (parent of `87e01e0`), copied `tests/test_limits.py` in, ran pytest | `ImportError: cannot import name 'DEV_SHARED_SECRET'` — collection fails, confirms the tests exercise new code, not vacuous |
| Read full diffs: `git show 87e01e0` (imaging), `git show 2b98c13` (backend), `git show 311d357` (contracts) | see findings below |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Concurrency, 429 + Retry-After, backend retries | Yes | `app/guard.py` `HeavyJobLimiter`/`GuardMiddleware` gates `/compose` and `/render/personalization` before the body is read; `tests/test_limits.py::test_heavy_jobs_over_the_limit_get_429_with_retry_after` and `test_slot_released_when_the_job_fails` (slot released in a `finally`, even on 422). Backend `client.ts` `call()` retries a 429 up to `IMAGING_BUSY_RETRIES=5`, waiting `retryAfterMs` (clamped 100ms–30s), then raises `ImagingError(429)` — proven bounded by `client.test.ts::"gives up after the retry budget with the 429"` (exactly 6 requests, 5 waits). Never loops forever. |
| 2. Input limits (pixel cap, format allowlist, bounds) | Yes | Pixel cap in `app/vips.py::load()` from the lazy header (`pixel_budget_error`), before pixel decode; allowlist by magic bytes in `app/limits.py::sniff_format` (PNG/JPEG/WebP/TIFF/SVG/PDF only), `pyvips.block_untrusted_set(True)`; per-format loader, no `new_from_file`. Bounds on width ≤60in, length ≤240in, DPI 36–1200, placements/copies ≤10,000, keys ≤512 — all in `app/main.py` field constraints, contract-mirrored in `invai-contracts/src/schemas/vendors.ts` (`311d357`). Confirmed with `test_compose_bounds`, `test_nest_bounds`, `test_personalization_bounds`, `test_compose_placement_count_is_capped`. |
| 3. Service auth (constant-time, 401, dev-vs-prod) | Yes | `app/guard.py::secret_ok` hashes then `hmac.compare_digest`s every configured secret with no early exit (`ok |= ...`), so timing doesn't depend on which secret (or none) matches. Checked before the body is read (pure ASGI middleware, `test_rejected_before_body_is_parsed`). `production_config_error` blocks startup on the dev secret or <32 chars (`test_production_refuses_to_start_on_dev_secret`), and the Docker image bakes `IMAGING_ENV=production`. |
| 4. Dev endpoints off by default | Yes | `Settings.imaging_dev_endpoints: bool = False`; `/labels/mock` and `/sample-art` get `Depends(_dev_only)` → 404. Docker image also sets `IMAGING_DEV_ENDPOINTS=false` explicitly. `test_dev_endpoints_are_404_unless_the_flag_is_set`. |
| 5. Process safety | Yes | Dockerfile: non-root `imaging` user (uid 10001), `HEALTHCHECK` via Python (no curl in slim), `--timeout-graceful-shutdown 30`; lifespan logs in-flight heavy jobs at shutdown. `X-Render-Ms` on every response (guard middleware) plus `render_ms` in compose/personalization JSON. |
| 6. Tests (oversized input, wrong format, missing auth, concurrency) | Yes | `tests/test_limits.py`, 28 tests, covers all four plus rotation, PDF budget, and dev-endpoint gating. |
| 7 (added). Pixel cap covers pdfium too | Yes | `app/pdf_input.py::rasterize_pdf` calls `pdf_page_budget_error(*page.get_size(), dpi)` before `page.render`. `test_pdf_page_over_budget_is_refused_before_render` monkeypatches `PdfPage.render` to blow up if called, and asserts it never is. |

## Blocking findings
1. `invai-backend/src/integrations/imaging/client.ts:207,246` (as committed in `2b98c13`) — the card's grant for this file is `call()` only ("narrow grant... single class/field only", wave.md line 37/116), but the commit also adds `header_height_in?: number` to the `nest` and `compose` input type signatures, outside `call()`. This is T-9-2's field (wave.md line 117, granted to T-9-2, needed by its uncommitted `src/modules/production/sheets.ts`), not T-9-5's. It's harmless — additive, optional, no logic — and mirrors the same cross-card leak the report *did* disclose for imaging's `app/main.py` ("T-9-2's uncommitted `header_height_in` lines... left unstaged"), but this one wasn't disclosed for the backend repo and isn't on the tech lead's after-the-fact approval list (vips.py, pdf_input.py, conftest.py, test_api.py fixture, README, .env.example). Concrete scenario: if T-9-2 also adds the same two lines in its own commit expecting a clean diff, it'll find them already there under someone else's SHA, and no record exists of why. Fix: either the tech lead extends the after-the-fact approval to cover this (consistent with the imaging-side precedent), or these two lines are reverted from `2b98c13` and left for T-9-2 to add.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — imaging matches owned + already-approved-after-the-fact paths; contracts matches the card's required mirror. Backend has the one out-of-grant hunk above.
- [x] Nothing outside scope — same caveat as above; everything else traces to an AC.
- [x] Tests exercise the behavior, and none were weakened — scan script hits are all pre-existing/unrelated to this commit; new tests fail on pre-change code (see evidence).
- [x] Tenancy / idempotency / money / en-es — n/a (no tenant data, no money, no user-facing strings in this card); heavy-job slot release is idempotent-safe (released in `finally`).
- [x] Decisions recorded where needed — wave.md already records the grants and the after-the-fact approvals list.

## Optional notes (not blocking)
- Report says pytest was 99 passed; repo now shows 102 (other cards' tests landed in between) — not a discrepancy in T-9-5's own tests.
- RSS/time weren't re-measured before/after per the imaging-budget skill; acceptable here since the report notes the pixel pipeline itself is unchanged (same loader, middleware adds microseconds) and this isn't a compose/nest algorithm change.
- `invai-contracts` lint failure on `sheetSpecPdfCapError` and imaging's `app/labels.py` format debt are correctly attributed to other cards (T-9-3, T-6-2) in the report, confirmed pre-existing.
