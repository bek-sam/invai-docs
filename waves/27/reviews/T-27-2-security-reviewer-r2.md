# Review of T-27-2 (round 2, S-54 only)

- Reviewer: security-reviewer on opus
- Author: imaging-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-imaging show f2d2eda` | only `app/scenes.py`, `tests/test_scenes.py`; check sits right after `load()` (lazy header + pixel cap) and before `flatten`/`copy_memory`/`read_base_meta`/`template_maps` |
| own server :8152 (PID 17094, STORAGE=local, stopped, temp dir deleted), r1 probe: 9000x9000 PNG (237 KB) as `base_key` | 400 `base is 9000 x 9000 px; each side must be 256-2048 px` in 9 ms; RSS 139 MB before and after (r1: 200, 3.7 s, 2.59 GB peak) |
| same server, real 1024 px scene base | 200 in 0.7 s |
| `cd invai-imaging && uv run pytest -q` | 196 passed in 31.32 s |
| `uv run ruff check .` | All checks passed |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 4 (safety) | yes | Base now bounded to scene-base's own 256-2048 px range from the header; scene side already bounded (r1). Max template draw = 2048 px. |

## Blocking findings
none. S-54 marked Fixed in `invai-docs/security/v1-review.md`.

## Checks
- [x] Only owned paths; no test weakened (one new test, oversize + undersize + normal pass)
- [x] Refusal is a 400 with no foreign key in the message

## Optional notes (not blocking)
- The base file's byte size is not capped before download (disk only, not RAM); fine while bases are our own renders.
