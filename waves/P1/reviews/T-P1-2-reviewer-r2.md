# Review of T-P1-2 (round 2)

- Reviewer: reviewer on Claude Opus 5.5
- Author: imaging-engineer on Claude Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `uv run ruff check . && uv run pytest -q` (invai-imaging @26699d8) | All checks passed; 119 passed, exit 0 |
| `scan-test-weakening.sh invai-imaging f77e6e8` | no hits, exit 0 |
| imaging on :8052 (PIDs 76583/76586, STORAGE=local scratch in /tmp; killed, port free, dir deleted) + `tsx` script using backend `createImagingClient` (read-only) | default request: 350px photo in 2in slot → `OK []`; 900x300 photo in square slot → `OK []` (r1: `ImagingError 200 unexpected response shape`) |
| same server, raw fetch with `photo_flags: true` | 200 `["upscale"]` and 200 `["aspect_mismatch"]` |
| `grep -rn aspect_mismatch\|upscale app/`; importers of `app.render` | codes emitted only in render.py:200,223, which only `/render/personalization` (main.py) calls; no other route emits them |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 0, 2-6 | yes | unchanged from r1; 26699d8 touches only app/main.py and tests/test_api.py |
| 1 | yes | default response filters the two new codes (main.py:210, 247-249); backend client parses it live; opt-in returns them; tests `test_personalization_default_response_has_no_new_photo_flag_codes` and `..._opt_in_returns_new_codes` |

## Blocking findings
none (r1 finding 1 fixed and proven with the real backend client)

## Checks
- [x] Only owned paths changed (invai-imaging app/main.py, tests/test_api.py); untracked .DS_Store not committed
- [x] Nothing outside scope; no contract or backend change, per tech lead ruling
- [x] Tests exercise the behavior, none weakened (scan clean)
- [x] Tenancy/idempotency/money/i18n: n/a (stateless service, additive opt-in field defaulting off)

## Optional notes (not blocking)
- Follow-up for the architect/backend: widen the `flags[].code` enum in contracts and client.ts:74-81, then the backend can send `photo_flags: true`.
