# Review of T-23-2 (round 2, co-review scope: S-44 fix in CameraScan.tsx)

- Reviewer: security-reviewer on Sonnet 5
- Author: floor-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-floor show 7900d0a --stat` / full diff | reviewed diff directly |
| `git -C invai-floor diff --stat 7900d0a^ 7900d0a` | only `src/components/CameraScan.tsx` and `src/components/CameraScan.test.tsx` — both under `src/**` |
| New race test run against `7900d0a^` (pre-fix) via `git archive` into `/tmp/review-T-23-2-r2`, `vitest run src/components/CameraScan.test.tsx` | 1 failed / 1 passed: "stops the stream's tracks..." **fails** on old code (`stopFns[0]` called 0 times, expected 1) — proves the test is real evidence of the fix, not a tautology. The second test ("assigns the stream... when still open") **passes** on old code, proving the normal open path was already correct and is unchanged. |
| `pnpm typecheck` (invai-floor) | `tsc --noEmit` clean |
| `pnpm lint` (invai-floor) | `biome check .` — 79 files, no issues |
| `pnpm test --reporter=dot src/components` (invai-floor) | 2 passed (1 file) |

## Findings
None blocking. The fix matches the exact fix prescribed in r1: `openRef` is set `true` in `start()` right after `setOpen(true)`, set `false` in `close()` and in the unmount-cleanup effect, and checked immediately after `getUserMedia` resolves — if false, every track on the newly granted stream is stopped and the function returns before `streamRef`/`detectorRef`/`loop()` run. The `catch` block was also updated to only call `setError` when still open, avoiding a state update after unmount/close, without changing `stop()`'s unconditional call.

## Acceptance criteria (S-44 close)
| # | Met? | Evidence |
|---|---|---|
| Close/unmount during pending `getUserMedia` stops new tracks and never starts the loop | yes | code inspection of `CameraScan.tsx:69-79`; new test passes on the fix and fails on the pre-fix code (mutation-style proof above) |
| Normal open path (dialog still open when `getUserMedia` resolves) is unchanged | yes | second new test passes on both old and new code; `stop()`, `videoRef` assignment, `loop()` start untouched outside the added guard |
| Only `src/**` changed | yes | `git diff --stat 7900d0a^ 7900d0a` shows only the two component/test files |

## Blocking findings
None.

## Checks
- [x] Fix closes S-44 per r1's exact prescription
- [x] New test fails on pre-fix code (verified by running it against `7900d0a^`)
- [x] Normal open path unchanged (second new test + code diff)
- [x] Only `src/**` touched
- [x] `pnpm typecheck`, `pnpm lint`, `pnpm test --reporter=dot src/components` all green

## Optional notes (not blocking)
- None.
