# Review of T-27-2 (round 1)

- Reviewer: reviewer on fable
- Author: imaging-engineer on opus (finisher)
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-imaging`: `uv run ruff check . && uv run pytest -q` | All checks passed; 184 passed in 18.79 s, exit 0 |
| `git show --stat 6b8f964 6d0cac1`; `git status --short` | 10 files, all `invai-imaging/**`, no Dockerfile; tree clean |
| `scan-test-weakening.sh invai-imaging origin/main` | no hits (removed=0 added=61) |
| `git show 6b8f964 -- uv.lock \| grep '^+name'` | only `numpy` added (reason in report: FFT NCC + SSIM, no scipy) |
| Probe `/tmp/rev-t272/probe.py` (TestClient on the real routes, scratch `LOCAL_STORAGE_DIR`): perturbed scenes tee navy/white, hoodie navy | 200, passes, c1 0.92–0.99, c2 0.94–0.99, 650–780 ms at 2048 px |
| Same probe, provider art inside the print box only (outline intact) | 200, **passes=true**, c1 unchanged, c2 0.858 / 0.914 / 0.941, key written |
| Looked at `/tmp/t272/out/contact.jpg`, `zoom.jpg`, and my `/tmp/rev-t272/boxes.jpg` (print-box crops clean vs drifted) | design at real size, scene light carried; drifted outputs show the provider's bars and disc through the design |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `test_scene_base_and_mask_in_the_provider_convention` (3 sizes), mask alpha opaque only on print area + 0.5 in; contact sheet |
| 2 | partly | check 1, restore, lbb upscale (README), amazon_main 422, XMP seen in test; **check 2 does not detect provider art in the print box** (finding 1) |
| 3 | partly | constants + comment; perturbed/folds pass, moved/widened/far fail, swapped/recolored fail (direct metric). The realistic drift case is untested and passes |
| 4 | yes | `check_scope` on all keys, 401 without secret, size cap before download, magic/size/pixel caps → 400 (`test_untrusted_scene_is_refused_with_400`), HEAVY_PATHS; budgets in README |
| 5 | yes | contact.jpg + zoom.jpg looked at (known: beige tint on white tee B-287, drawstrings through print) |

## Blocking findings
1. `app/scenes.py:716-717,729-730` (`_shade_field`, relief) and `:508-512` (de-shade) — the scene's luminance inside the print box is applied to the restored blank and the design with no limit on its shape (sigma 0.08 in, 0.6–1.25), and check 2 then removes the same structure as "shading" (sigma 0.06 of the region, 0.6–1.6). Scenario: GPT Image ignores the mask (the wave file says masks are guidance only) and draws a logo and text in the chest area while keeping the garment outline; imaging renders those bars at full strength across the shop's design, returns `passes=true` with `design_lock_score` 0.86–0.94, writes the file, and T-27-4 pushes it to the live Shopify product. The lock never locks against the one drift the card was written for. The backend mock's `IMAGE_GEN_MOCK_DRIFT` also paints a ring, so check 1 hides this end to end. Fix is the owner's call: for example, compare the scene's print-box luminance structure to the base's before restoring (a bounded "print region unchanged" check), or tighten the shade field inside the box so only low-frequency light survives, and in either case add a test with provider art inside the box only (outline intact) that must fail or produce a clean print.

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (scan clean; `_restore_and_print` monkeypatch in `test_design_drift_fails_and_saves_nothing` is a test of the fail path, not of the unit)
- [x] Tenancy (company-prefix keys), idempotency (same bytes on re-run, tested), money n/a, en/es n/a (no user copy)
- [x] Decisions recorded where needed (numpy reason in report; thresholds in constants + README)

## Optional notes (not blocking)
- The 32-scene threshold sweep has no script in the repo (`bench/photo_bench.py` is wave 26); the ranges can't be regenerated. A `bench/scene_sweep.py` would make AC3's justification reproducible.
- `background_not_white` is always reported for white-required presets, even if the scene happens to be white; fine as a conservative flag.
- Pytest "fails without the change" is trivial here (new module import), so the both-ways tests are the real integrity evidence; they are present.
