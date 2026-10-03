# Review of T-27-2 (round 2)

- Reviewer: reviewer on fable
- Author: imaging-engineer on opus (finisher)
- Verdict: approve

Scope of this round: r1 blocking finding 1 (provider art inside the print box passed the lock) and no regression. Fix commit `invai-imaging` 6bd4ebf (README, `app/scenes.py`, `tests/scene_helpers.py`, `tests/test_scenes.py`; all owned; tree clean).

## Evidence I re-ran
| Command | Result |
|---|---|
| `uv run ruff check . && uv run pytest -q` | All checks passed; 195 passed in 38.30 s |
| r1 probe `/tmp/rev-t272/probe.py` (TestClient, `STORAGE=local`, scratch dir), art inside the print box with outline intact, tee navy/white + hoodie navy | 200, `passes=False`, `failures=['region_changed']`, c1 0.92–0.99 (outline intact), c2 `None`, `key=null`; no `photos/scenes/out/*` written for any of the three (listed the scratch dir) |
| Same probe, mock-style perturbed scenes | 200, passes, c1 0.92–0.99, c2 0.96–1.00, 670–800 ms at 1024 px base |
| Looked at `out/rv-perturbed-hoodie-1B3A6B.jpg` | design at real size, clean print, scene light carried (drawstrings through print still the known gap) |
| `scan-test-weakening.sh invai-imaging origin/main` | no hits; test diff removes no assertions (only an import line) |
| New gate test with `BOX_FOREIGN_MAX` patched to 1.0 via a pytest plugin (`-p gateoff`, no repo files touched) | the 4 `test_provider_art_in_the_print_box_fails_and_saves_nothing` cases FAIL, the 3 `test_perturbed_whole_frame_still_passes` cases PASS: the test proves the gate |

## r1 finding 1
Closed. `app/scenes.py` `print_box_foreign` (check 1b, gradient of log luminance in the print box minus the dilated base edges, limit 0.004) runs before any restore in `composite_scene`, and a hit returns `region_changed` with `key=None` before `_restore_and_print`. Shade carried from the scene is now blurred 0.4 in and clamped 0.7–1.2 as a backstop. Thresholds and measurements are in constants + README.

## Acceptance criteria (changed from r1 only)
| # | Met? | Evidence |
|---|---|---|
| 2 | yes | check 1b rejects art in the box (probe + 4 tests); check 2 still 0.96–1.00 on clean scenes |
| 3 | yes | 1b measured 0.000 on clean/relit/noisy/folded vs 0.012+ on the smallest mark (`test_print_box_check_ignores_light_folds_and_noise`, 4 blanks) |

## Checks
- [x] Only owned paths, in scope; no response-shape change, no new codes
- [x] No weakened tests; the new gate test fails with the gate off
- [x] Idempotency/tenancy unchanged from r1 (company-prefixed keys, same bytes on re-run)

## Optional notes (not blocking)
- The r1 note on a reproducible threshold sweep script still stands (constants now document 7 measured cases).
