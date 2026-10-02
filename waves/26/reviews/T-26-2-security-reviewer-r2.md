# Review of T-26-2 (round 2), security co-review, flag `files` (S-50 only)

- Reviewer: security-reviewer on opus
- Author: imaging-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show 9d66957 --stat` | 3 files: `app/main.py`, `app/storage.py`, `tests/test_photos.py` (owned) |
| `uv run pytest -q` (invai-imaging @ 9d66957) | 162 passed in 7.27 s (was 159) |
| `uv run ruff check .` | All checks passed |
| `scan-test-weakening.sh invai-imaging f282280` | no hits |
| Own server `uvicorn --port 8152`, `STORAGE=local` (PID 78832, stopped, port free, temp dir removed) | rows below |
| r1 proof again: 25 x 20 MB random bytes under `.jpg` keys | 422 `unsupported image format` after the first item (was 200, 500 MB zip) |
| `.csv` item in `<co>/uploads/` | 422 `must be a .jpg, .jpeg or .png file` (0.9 ms, nothing downloaded) |
| 60 MB sparse `.jpg` | 422 `63 MB, over the 52 MB per-item limit` (metadata only) |
| 22 x 49 MB sparse `.jpg` (1.08 GB) | 422 `items total 1079 MB, over the 1074 MB total limit` (metadata only) |
| legit `ok.jpg` + `ok.png` | 200, 1,050-byte zip |
| no secret | 401 |

## Acceptance criteria (security part)
| # | Met? | Evidence |
|---|---|---|
| 8 Safety and budget for zip (S-50) | Yes | caps checked from `storage.size()` before `workdir()`; extension allowlist; `_CheckedStorage` download; rows above |
| 7, 8 (rest) | Yes | unchanged since r1; check_scope still runs first in `photo_zip` |

## Blocking findings
none

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope (optional r1 notes not acted on, as stated)
- [x] Tests exercise the behavior (one per cap plus the extension); none weakened
- [x] Tenancy: unchanged; `S3Storage.size` uses `head_object` on the already scope-checked key
- [x] Decisions: none needed; S-50 marked Fixed in `security/v1-review.md`

## Optional notes (not blocking)
- Low: size is checked by HEAD and then GET (TOCTOU); an object replaced in between could exceed the cap. Backend presigned PUTs bind the exact size, so not reachable through the app today.
- Cosmetic: messages print MiB as "MB" (50 MiB shows "52 MB").
- r1 Lows (XMP control chars, palette outside `HEAVY_PATHS`) remain open as notes.
