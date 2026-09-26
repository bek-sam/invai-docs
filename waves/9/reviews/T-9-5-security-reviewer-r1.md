# Review of T-9-5 (round 1) — security co-review

- Reviewer: security-reviewer on Sonnet 5
- Author: imaging-engineer + platform-sre on Opus
- Verdict: approve (security-relevant surface only; see the reviewer's r1 file for the one
  ownership/scope finding, which is not a security issue)

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-imaging show 87e01e0` (full read: `app/guard.py`, `app/limits.py`, `app/config.py`, `app/vips.py`, `app/pdf_input.py`, `app/main.py`, `Dockerfile`) | read in full |
| `git -C invai-backend show 2b98c13` (`src/env.ts`, `src/integrations/imaging/client.ts`, `client.test.ts`) | read in full |
| `cd invai-imaging && uv run pytest -q` | 102 passed |
| `grep -n "def download\|isSafeKey" invai-imaging/app/storage.py` | pre-existing key handling untouched by this card; imaging still doesn't validate `isCompanyKey` (backend's job per the report and the imaging-change-with-budget skill's "no auth today: internal-only" note — now auth exists but tenancy scoping is still explicitly out of scope for imaging) |
| `grep -n "secret\|PRODUCTION_KEYS\|missingProductionKeys" invai-backend/src/env.ts` | `IMAGING_SHARED_SECRET` uses the `secret()` wrapper (trims, optional) and is in `PRODUCTION_KEYS`; with `ALLOW_MOCKS=true` in prod it's allowed to be unset, and `env.IMAGING_SHARED_SECRET` is then `undefined` (never falls back to the dev default when `isProd`) — client sends no header, imaging answers 401. Fail-closed, no silent fallback. |

## Threat-model checklist (threat-model-change)
| # | Threat | Control (file:line) | Verified |
|---|---|---|---|
| Auth bypass | missing/forged secret reaches a heavy or decode endpoint | `app/guard.py::GuardMiddleware` — pure ASGI, checked before `receive()` is ever called for the body; `secret_ok` uses `hashlib.sha256` then `hmac.compare_digest` per configured secret, no early exit (`ok |= ...`) so equal-time whether 0, 1 or N secrets match | Yes — `test_missing_auth_header_is_401`, `test_wrong_secret_is_401`, `test_rejected_before_body_is_parsed` (garbage JSON body, still 401, proves order) |
| Dev-secret-in-prod | image ships with the public `invai-imaging-dev-secret` | `app/config.py::production_config_error` — refuses `imaging_env=="production"` unless every configured secret is present, not the dev default, and ≥32 chars; called from `lifespan()`, raises before `uvicorn` binds; Docker image bakes `IMAGING_ENV=production` | Yes — `test_production_refuses_to_start_on_dev_secret`, `test_production_requires_a_real_secret` (both the "no secret" and "short secret" branches) |
| Fail-open on the backend side | backend can't reach imaging or has no secret configured | `env.ts`: `IMAGING_SHARED_SECRET` only defaults to the dev value outside production; in prod with `ALLOW_MOCKS` it's `undefined`, so `client.ts` sends no header, and imaging (which never accepts an empty/missing header, `secret_ok(None) == False`) answers 401 — no path where a missing secret is silently treated as authorized | Yes, by reading; also `client.test.ts::"surfaces a wrong secret as a 401 ImagingError"` |
| Denial of wallet / memory exhaustion | many parallel large composes | `app/guard.py::HeavyJobLimiter` takes a slot before the route runs; `IMAGING_MAX_HEAVY_JOBS` config-driven; slot always released in `finally`, including on a validation error inside the route (`test_slot_released_when_the_job_fails`) | Yes |
| Decompression bomb (raster) | a PNG header claims 100k×100k px | `app/vips.py::load()` reads the header lazily (`img.width`/`img.height`, no pixel decode) and calls `pixel_budget_error` before returning; format-specific loader only, `pyvips.block_untrusted_set(True)` blocks libvips' own "untrusted" loaders (e.g. magick, matload) as a second line | Yes — `test_oversized_png_is_refused_from_its_header` asserts it's refused in <1s (nothing decoded) |
| Decompression bomb (SVG) | a tiny SVG declares a huge viewport | Same pixel cap applied via `svgload`'s header (`width`/`height` from the declared `width="1000in" height="1000in"`, scaled by DPI) before any rasterization | Yes — `test_oversized_svg_is_refused_before_render` |
| Decode-cap bypass via PDF (AC7, the reason this card exists in part) | `pypdfium2` doesn't go through libvips at all, so the raster cap alone doesn't cover it | `app/pdf_input.py::rasterize_pdf` computes page size (pt→in) × DPI and calls `pdf_page_budget_error` *before* `page.render()` | Yes, and rigorously: `test_pdf_page_over_budget_is_refused_before_render` monkeypatches `PdfPage.render` to raise if it's ever called, proving the check runs first, not just that the response is a 422 |
| Format/magic-byte bypass | a `.png` key that's actually something else, or an unlisted format (GIF/BMP/JPEG2000) | `app/limits.py::sniff_format` — allowlist by magic bytes (PNG/JPEG/WebP/TIFF/PDF/SVG only, no catch-all); `declared_type_error` compares the key's extension against sniffed bytes on every download path (`_CheckedStorage`, used by `/compose` and `_download`, which covers `/qa/check` (soft, `unreadable` issue), `/qa/clean-alpha`, `/render/personalization` background+photo slots, `/mockup`) | Yes — `test_formats_outside_the_allowlist_are_refused` (GIF/BMP/JP2 headers), `test_magic_bytes_must_match_the_declared_type`, `test_wrong_format_through_the_api` (renamed PNG→`.jpg` through `/qa/check`, `/mockup`, `/compose`) |
| Input bounds / injection via placement/slot fields | oversized strings, unbounded placement/slot arrays used for amplification | Explicit `Field(max_length=...)` on every string and list field touched by this card (keys ≤512, transfer_id/id ≤100, values ≤1000 chars, slots/values ≤50, placements/copies ≤10,000); mirrored width/length/DPI bounds in contracts (`311d357`) so bad requests are rejected before they leave the backend too | Yes — `test_compose_bounds` parametrized over 6 boundary violations, `test_nest_bounds`, `test_personalization_bounds` |
| Data/PII exposure | logs or error bodies leaking secrets or file content | `log.warning("imaging auth rejected %s %s", ...)` logs method+path only, never the header value; error messages (`declared_type_error`, `pixel_budget_error`) include only sizes/format names, no file bytes; the shared secret itself is never echoed anywhere in a response | Yes, by reading `app/guard.py`, `app/limits.py` |
| Double side effect | a retried request from the backend runs the same heavy job twice with a different outcome | 429 is sent by the middleware *before* the route (and its side effects) runs, so a client retry never risks a duplicate/partial render; the backend retry loop is capped at 5 attempts, and 429 alone is retried — any other status is returned to the caller immediately, no infinite loop | Yes — `client.test.ts::"gives up after the retry budget with the 429"` proves the cap; `secret_ok`/limiter code path confirms 429 precedes route execution |

## Constant-time comparison — specifically checked
`secret_ok` (`app/guard.py`): hashes the provided value and every configured secret with SHA-256,
then `hmac.compare_digest`s each pair, accumulating with `|=` and never short-circuiting on the
first match. This avoids both a timing leak on secret *content* (via `compare_digest`) and on
secret *count/order* (via hashing first, so all comparisons are fixed-length regardless of the
raw secret's length, and every configured secret is always checked). No blocking finding.

## Blocking findings
None from a security standpoint. See the reviewer's r1 file for one ownership/scope finding
(stray `header_height_in` lines in `invai-backend/src/integrations/imaging/client.ts`, outside
the file's narrow grant) — it's a process/attribution issue, not a vulnerability: the two lines
are additive optional-field typing with no auth, validation or data-flow effect.

## Residual risk (from the report, verified plausible)
Imaging still trusts any caller holding the shared secret to access any bucket key — it has no
per-tenant key scoping (`isCompanyKey` lives in the backend, not imaging). Accepted at Medium
while imaging stays internal-only/non-internet-facing, as the report states. No new finding id
needed in `security/v1-review.md`; this matches the existing G4/S-2x posture and isn't worsened
or newly introduced by this card — if anything this card meaningfully narrows it by adding auth
where there was none.

## Checks
- [x] Secret comparison constant-time (`hmac.compare_digest`, hashed first, no early exit)
- [x] Missing/wrong secret → 401 on every heavy endpoint, checked before the body is read
- [x] Production refuses the dev secret and refuses to start under 32 chars
- [x] Pixel cap covers both libvips (`vips.py`) and pdfium (`pdf_input.py`, AC7), each proven not
      to decode/render before the check runs
- [x] Magic-byte allowlist has no bypass found (no catch-all branch, extension must also match)
- [x] Input bounds present and tested at the boundary
- [x] Concurrency limit returns 429 + Retry-After before work starts; backend retry is capped
      (5 attempts) and only retries 429, never loops forever
- [x] Dev endpoints (`/labels/mock`, `/sample-art`) default off, and off in the Docker image
- [x] Docker image is non-root (`uid 10001`) with a `HEALTHCHECK`
- [x] No weakened tests found in this card's actual diff (scan-script hits are unrelated commits)
