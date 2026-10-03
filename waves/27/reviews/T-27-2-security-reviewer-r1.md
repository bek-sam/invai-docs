# Review of T-27-2 (round 1)

- Reviewer: security-reviewer on opus
- Author: imaging-engineer on opus
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-imaging && uv run pytest -q` | 195 passed in 32.27 s |
| own server :8152 (PID 15970, STORAGE=local, stopped), scene routes without `X-Imaging-Secret` | 401 |
| scene_key under another company prefix | 400 `scene_key is outside out_key's company prefix` |
| `load_scene` on 16-bit RGB PNG, palette PNG, RGBA, grey, CMYK JPEG, 5000x300 WebP | all -> 3-band uchar sRGB (16-bit scaled right); 5000 px -> 400 |
| S-54 probe: 254 KB 9000x9000 PNG as `base_key` (+ garment/view), composite | 200, 3.7 s, server peak RSS 2.59 GB, 1.60 GB held after (template cache) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 4 (safety) | partly | Secret on both routes (guard deny-by-default, probe 401); `check_scope` covers scene/base/design/out/mask_out keys; both routes in `HEAVY_PATHS`; scene: storage size <= 25 MB before download, declared-type + magic sniff, header pixel cap and 256-4096 px sides before decode, odd modes normalized, errors carry no foreign keys. Base input is unbounded (S-54). |
| 1-3, 5 | n/a | Primary reviewer's scope |

## Blocking findings
1. `invai-imaging/app/scenes.py` `composite_scene` (base `load`/`copy_memory`, then `template_maps(garment, view, base.width, base.height)`) — S-54, Medium. The base gets only the global 570M-pixel cap. Any PNG in the company prefix (a shop's own design upload is enough once T-27-3 passes a base key it doesn't control) at ~23000 px a side makes one call allocate >10 GB and pin GBs in the lru cache; with two heavy slots the imaging process is OOM-killed for every tenant's gang sheets. Fix: refuse a base outside 256-2048 px a side (scene-base's range) from the header, 400, before any decode or template draw; add a pytest. Due 2026-11-02 (30 d).

## Checks
- [x] Only owned paths changed (app/, tests/, README, pyproject/uv.lock; no Dockerfile)
- [x] Nothing outside scope (no model calls)
- [x] Tests exercise refusals (400 scene, keys, secret/heavy); none weakened
- [x] Tenancy: company-prefix check on all five keys; no DB, no money, no UI text
- [x] numpy dependency: reason in report (FFT/SSIM, avoids scipy); registration runs on a coarse grid and scene sides are capped, so numpy work is bounded once the base is

## Optional notes (not blocking)
- XMP subjects reuse wave 26's validator (`PhotoRenderRequest._subjects`), already reviewed.
- A missing own-company key echoes the key in the 422 (same as existing routes; internal only).
