# Review of T-26-2 (round 1), security co-review, flag `files`

- Reviewer: security-reviewer on opus
- Author: imaging-engineer on opus
- Verdict: changes-required (1 Medium: S-50)

## Evidence I re-ran
| Command | Result |
|---|---|
| `uv run pytest -q` (invai-imaging @ f282280) | 159 passed in 6.91 s |
| `scan-test-weakening.sh invai-imaging f282280~1` | no hits |
| Own server `uvicorn --port 8152`, `STORAGE=local` (PIDs 74664, 75005; both stopped, port free, temp dir removed) | see rows below |
| No secret / wrong secret on `/photo/palette`, `/photo/render`, `/photo/zip`, `GET /photo/templates` | 401 on all 5 calls |
| render: design under company B, out_key under A | 400 `design_key is outside out_key's company prefix` |
| keys `A/../B/..`, `A/%2e%2e/B/..`, `/B/..`, `A/./`, `A//`, `...%00`, backslash `..\` (as design_key and out_key) | 400 `not a valid storage key` on every one |
| zip: one item under company B | 400 `items[1].key is outside out_key's company prefix` |
| zip entry names `../../etc/passwd`, `/abs/x.jpg`, `..\..\win.jpg`, `..`, `C:\x.jpg`, NUL | stored as `etc/passwd`, `abs/x.jpg`, `win.jpg`, `file`, `C_/x.jpg`, `a_b.jpg` (no traversal) |
| `IMAGING_MAX_DECODE_PIXELS=200000`, 600x600 design on render and palette | 422 over the pixel limit (cap runs before decode) |
| PNG bytes under a `.jpg` key on render | 422 `file content is PNG but the key declares JPEG` |
| XMP subjects `</rdf:li></rdf:Bag><x:evil/>`, `]]>&amp;<?xpacket end="w"?>` | escaped; packet parses; no element injection |
| **zip: 25 items x 20 MB random** | **200, 500,154,879-byte zip in 8.9 s; a `.csv` item zips too (S-50)** |

## Acceptance criteria (security part)
| # | Met? | Evidence |
|---|---|---|
| 7 Zip names sanitised, same-company keys, else 400 | Yes | rows above |
| 8 Shared secret on all routes | Yes | 401 x5; `OPEN_PATHS` only `/health` |
| 8 Company-prefix check on every input key and out_key | Yes | `app/keys.py` `SAFE_KEY` + UUID prefix + `check_scope`; S3 keys are case-sensitive, so a case variant fails closed |
| 8 Pixel caps on untrusted design | Yes | render and palette both go through `load()` / `_CheckedStorage` |
| 8 Render and zip in `HEAVY_PATHS` | Yes | `app/guard.py:23`, exact path match at :90; test `test_photo_routes_need_the_secret_and_share_the_heavy_limit` |
| 8 Safety and budget for zip | **No** | S-50 below |

## Blocking findings
1. `app/main.py` `photo_zip` / `app/photos.py:412` `build_zip` (S-50, Medium, unbounded abuse): up to 500 items, no per-item or total byte cap, downloaded through raw storage (no declared-type check), so any kind in the prefix (gang-sheet print files, CSV uploads) is copied to imaging temp and zipped. Scenario: one call with 500 large print-file keys fills the imaging disk and stops compose, labels and renders for every shop. Fix: per-item and total byte caps checked before download (e.g. 50 MB / 1 GB), download via `_CheckedStorage`, item keys limited to `.jpg/.jpeg/.png`; one pytest per cap. Owner imaging-engineer, due 2026-11-01.

## Checks
- [x] Only owned paths changed (9 files under `invai-imaging`, no Dockerfile)
- [x] Nothing outside scope (security view)
- [x] Tests exercise the behavior, none weakened (scan: no hits)
- [x] Tenancy: imaging re-checks keys; the backend `isCompanyKey()` on T-26-4 remains the primary control
- [x] Decisions: none needed

## Optional notes (not blocking)
- Low: `xmp_subjects` allows control characters; `\x00` or `\x0b` gives 200 with a malformed XMP packet, so readers may drop `contains-synthetic-performer`. Reject chars below 0x20 in the validator.
- Low: `/photo/palette` decodes up to the full pixel cap outside `HEAVY_PATHS` (same as `/qa`, `/mockup` today).
- T-26-4: out_key kind is not restricted here (an out_key under `<co>/designs/` would overwrite art); the backend must build out_key itself, never from input.
