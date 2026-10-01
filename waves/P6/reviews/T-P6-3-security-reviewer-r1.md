# Review of T-P6-3 (round 1)

- Reviewer: security-reviewer on fable (auth co-review)
- Author: floor-engineer on opus (card said sonnet); commit invai-floor `9304da1`
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show 9304da1 --stat` | `src/realtime/sse.ts`, `src/realtime/sse.test.ts`, `README.md` (one line) |
| `pnpm test` (invai-floor) | 13 files, 114 passed (5.45 s) |
| `grep -rn 'token=' invai-floor/src invai-floor/e2e` | only `codes.ts:36,61` (pairing QR, read-only by card) and the test's negative assertion; no `/events` URL carries a session |
| `scan-test-weakening.sh invai-floor b2cfd13` | one hit: `expect(urls[0]).toBe("/events?token=sess")` removed; replaced by `toBe("/events")` plus `urls.some(includes("token")) === false`, which is stronger, and the requirement itself changed (card AC4) |
| read `sse.ts`, `hooks/useRealtime.ts`, `app/actions.ts:284-297,363-371`, web `lib/realtime.ts:143-145` | loop analysis below |

## Acceptance criteria (security view)
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `const url = opts.url`; session only in `Authorization: Bearer`; `Last-Event-ID` header unchanged; doc comment states the rule |
| 2 | yes | `unauthorized` event and 401 at connect both set `stopped` and call `onUnauthorized` once; tests assert one fetch after a 30 ms grace. No loop: `onAuthFailure` → `lock({expired})` sets `session: null`, so `useRealtime`'s `[token]` effect tears down and does not reconnect until a new PIN login; `stationWasRemoved` clears the station the same way |
| 3 | yes | `ready`/`ping`/`shutdown` paths untouched; `unauthorized` is not forwarded to `onMessage`, consistent with transport control events |
| 4 | yes | 3 new/changed tests present; red-on-base is the primary reviewer's to re-run |

## Blocking findings
none

## Checks
- [x] Only owned paths changed, except the one-line `README.md` sync (floor-engineer owns the repo README; the old line described `?token=` and would have been false). For the primary reviewer to rule on; no security effect
- [x] Nothing outside scope (no backend, web, QR or outbox change)
- [x] Tests exercise the behavior; the changed assertion is stronger, not weaker
- [x] No PII, no token in any log or URL; en/es unchanged (no new copy; existing station-removed and PIN-lock screens reused)
- [x] Decisions: none needed

## Optional notes (not blocking)
1. A 401 at connect is now final on the floor. Today the backend also answers 401 when `buildContext` fails on a DB blip (no probe on the connect path, see T-P6-2 review note 2), so a tablet reconnecting during a blip relocks instead of retrying. Same outcome as the existing queue-poll 401 handling, so not a regression; the fix belongs on the backend (503 when anonymous and the probe fails).
2. On `unauthorized` the client does not abort the controller; it relies on the server closing (which it does right after the write). Harmless; `stop()` from the hook cleanup aborts anyway.
