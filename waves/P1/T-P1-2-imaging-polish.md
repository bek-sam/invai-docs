# T-P1-2: Imaging polish, film-use metric, and the preview endpoint

| Field | Value |
|---|---|
| Wave | P1 (carries T-23-3, never started) |
| Scope ref | `product/scope.md#mvp-in` items 4, 12; `always-in-scope: bug` for the preview endpoint (B-209) |
| Spec | backlog B-103 rest (template geometry, aspect/upscale flags, ICC profiles, mirror, input bounds), B-41 (imaging part), B-209 provider half |
| Owner | imaging-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (sonnet), `files` flag (architect ruling 5) |
| Risk flags | files |
| Model | sonnet |

## Owned paths (edit)
- `invai-imaging/**`

## Read-only paths
- All other repos. The backend imaging client is changed by T-P1-4, not here.

## Acceptance criteria
0. **First commit:** `POST /preview` exactly as in `wave.md` "Agreed interfaces" (`{file_key, out_key, max_px=512 (64..2048)}` → `{out_key, width_px, height_px}`; sRGB PNG, longest side ≤ `max_px`, never upscaled; shared-secret auth like `/compose`; 422 on bad input), with tests. Commit it alone and note the SHA in your report's first progress line, so T-P1-4 can start.
1. Template geometry validated (slots inside the print area); aspect-ratio and upscale flags returned per placed image (upscale > 1.5× at target DPI flagged); input bounds enforced with clear 422 errors.
2. ICC: sRGB conversion for inputs with embedded profiles; CMYK input converted, not rejected silently.
3. Mirror option for DTF output as a compose option, default off (backend wiring of a vendor-profile default is a later card; note it).
4. Compose returns length-weighted film use across the sheet set (B-41) alongside per-sheet use. Additive response fields only (existing backend callers must keep working unchanged).
5. Every storage read and write goes through the existing storage helper and `Key` validation; no new key shape.
6. `uv run ruff check . && uv run pytest` green; peak RSS and throughput for `/compose` and `/preview` reported against the budgets in `imaging-change-with-budget`.

## Verification
- `cd invai-imaging && uv run ruff check . && uv run pytest -q 2>&1 | tail -n 15`
- Run imaging on a free port (not 8000 if taken: `lsof -iTCP:8000 -sTCP:LISTEN`), call `/preview` on a seeded design key (`docker exec local-minio-1 ...` or `mc ls` to find one under `designs/`) and open the output PNG; call `/compose` with mirror on and look at the result.

## Out of scope
- Backend wiring (T-P1-4 for preview; mirror/vendor default and film-use display are follow-ups). Contract changes.

## Budget
- About 3 hours. Stop and tell the tech lead if blocked for 30 minutes.

Commit only your paths. Don't push. Report: `invai-docs/waves/P1/reports/T-P1-2.md`.
