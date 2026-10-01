# Review of T-P6-3 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: floor-engineer on Opus (card says sonnet; the different-model rule is met by the fable security co-review)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test` (invai-floor @ 9304da1, clean tree) | tsc clean; biome 82 files, no fixes; 13 files / 114 tests passed |
| `pnpm build` / `VITE_API_URL="" pnpm build` | bare build fails on the existing VITE_API_URL guard in vite.config.ts (not from this card); with `VITE_API_URL=""` it builds (dist/sw.js generated) |
| b2cfd13 archive in /tmp + new sse.test.ts | 3 failed / 1 passed: URL `'/events?token=sess'` vs `'/events'`; unauthorized event: onUnauthorized called 0 times; 401: called 596 times (old retry loop). Removed after. |
| Probe tests (scratch, /tmp) on head sse.ts | `shutdown`+`retry:` reconnects (3 or more fetches, onUnauthorized never called); 503 and a thrown network error alternating keep reconnecting, no onUnauthorized; `event: unauthorized` with no data line is ignored per WHATWG (backend sends `data: ""`, and Hono writes `data: ` so it dispatches) |
| `scan-test-weakening.sh invai-floor b2cfd13` | 1 hit: the removed `?token=sess` assertion, replaced by stricter ones (exact `/events` on connect and reconnect, plus no `token` in any URL). This is the requirement changing (AC4), not a weakened test |
| `grep -rn "token=" invai-floor/src` | only the pairing QR doc in `lib/codes.ts` (read-only per the card) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | sse.ts:94-95: `url = opts.url`, the token goes only in Bearer; Last-Event-ID path untouched (test asserts calls[1]); doc comment updated |
| 2 | yes | sse.ts:103-108 (401 at connect) and :116-121 (event) set `stopped` and call onUnauthorized; red-on-base proof above. useRealtime.ts wires `onUnauthorized: () => void onAuthFailure()`; actions.ts:293 sends the tablet to stationWasRemoved (revoked token) or `lock({expired})`, which clears `session`, so the effect re-runs and a fresh PIN login opens a new stream. The tablet can't stay stuck on a dead stream. I traced the screen in code; the author's live Playwright run (23.4 s, en/es) is the browser evidence |
| 3 | yes | parser and backoff unchanged for other events; probes above |
| 4 | yes | 3 new or changed tests, all red on b2cfd13, green on head |

## Blocking findings
none

## Checks
- [x] Only owned paths changed: sse.ts, sse.test.ts, README.md (granted after the fact; the new realtime line matches the code)
- [x] Nothing outside scope (no backend, web, QR or outbox changes)
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy, idempotency, money: n/a (client transport only); no new user-facing strings
- [x] Decisions: not forwarding `unauthorized` to onMessage is reasonable and noted in the report

## Optional notes (not blocking)
- sse.ts:116: after `unauthorized`, the read loop keeps parsing the rest of the stream. In my probe, a second `unauthorized` called onUnauthorized twice, and a later `queue.changed` was still passed to onMessage. That contradicts the doc's "called at most once". The current backend can't trigger it (events.ts:128 writes one event, then `break`s). Still, a guard like `if (stopped) return` at the top of the parser callback, or `reader.cancel()`, would make it true.
- After a stop, `live` keeps reading "open" until `lock`/`stationWasRemoved` clears the session. This lasts a moment and is harmless.
- A transient DB blip at connect gives a 401 (buildContext returns anonymous) and locks the tablet. That already happened before this card, since onUnauthorized fired on every 401. The only change is that the floor no longer retries, and after the lock the next PIN login reconnects.
