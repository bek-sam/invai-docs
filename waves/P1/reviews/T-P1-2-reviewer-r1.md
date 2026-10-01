# Review of T-P1-2 (round 1)

- Reviewer: reviewer on Claude Opus 5.5
- Author: imaging-engineer on Claude Opus 5.5 (card says sonnet)
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `uv run ruff check . && uv run pytest -q` (invai-imaging) | All checks passed; 117 passed, exit 0 |
| `scan-test-weakening.sh invai-imaging 58b67ee` | no skips/snapshots/config; 3 removed asserts in test_render.py are tightened to include the new flags (not loosened) |
| imaging on :8052 (PIDs 74024/74026, STORAGE=local in /tmp scratch, stopped, port free, dir deleted) `/preview` | no secret → 401; 3000x1500 → 512x256 RGBA PNG; 350px src with max_px 2048 → 350x350 (no upscale); max_px 63/2049/"x" and empty file_key → 422 with clear detail |
| same: `/render/personalization`, 350px photo in 2in slot @300dpi | 200, flags `[{code:"upscale"}]` |
| `tsx` script calling backend `createImagingClient` (read-only file) against :8052 | `/nest` (with `overall_utilization`) parses OK; `/render/personalization` → `ImagingError 200 "unexpected response shape"` (zod enum rejects `upscale`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 0 | yes | 2fc3806 alone; shape matches wave.md; auth via GuardMiddleware (all paths but /health); live curls above |
| 1 | no | geometry/bounds 422s pre-existing (main.py:191-200) OK; new flags break the backend consumer (finding 1) |
| 2 | yes | test_vips.py 4 tests; icc_transform gated, CMYK falls back to colourspace |
| 3 | yes | compose.py `_prepare_design` fliphor only on design layer, default False; test_compose mirror test |
| 4 | yes | `/nest` `overall_utilization` additive; backend NestResult (z.object, non-strict) parses live; /compose response unchanged |
| 5 | yes | /preview uses `_download` (`_CheckedStorage`, declared-type check) + `get_storage().upload`, `Key` field; no new key shape |
| 6 | yes (author's numbers) | README perf section; not re-measured |

## Blocking findings
1. app/render.py:197-228 — new flag codes `aspect_mismatch` and `upscale` are emitted on `/render/personalization`, but the existing backend caller parses `flags[].code` with a closed `z.enum` (invai-backend/src/integrations/imaging/client.ts:74-81; also invai-contracts/src/schemas/personalization.ts:~102). Proven live: the call throws `ImagingError(status 200, "unexpected response shape")`; `renderValues` (personalization/service.ts:~379) marks it `failed` with `transient: false`. Scenario: a buyer uploads a 350 px photo for a 2 in photo slot (1.7x upscale, still 175 DPI) or a 3:1 photo into a square fill slot — today it renders; after this commit the personalization is permanently `failed`. This is a non-additive response change for an existing caller. Fix options (tech lead to pick): don't emit the new codes unless the request opts in (e.g. `extra_flags: true`), or land the contract + backend enum widening first (architect/backend-engineer paths, outside this card).

## Checks
- [x] Only owned paths changed (`invai-imaging/**`: app/, tests/, README.md; untracked .DS_Store not committed)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy/idempotency/money/i18n: n/a (stateless service; key-only storage access, no new key shape)
- [x] Decisions: AC4-on-/nest ruling recorded in wave.md build log; verified additive

## Optional notes (not blocking)
- wave.md says "PDF-first-page", but `load()` refuses multi-page PDFs (422 "must be single-page"); fine if uploads already reject them, worth a line in the interface.
- `/preview` is not in `HEAVY_PATHS`; it is bounded by the decode pixel cap like `/qa/check`, acceptable.
- Add a test pinning that every flag code `render_personalization` can emit is in a shared list, so a backend enum drift is caught.
