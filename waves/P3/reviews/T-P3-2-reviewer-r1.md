# Review of T-P3-2 (round 1)

- Reviewer: reviewer on opus 5.5
- Author: floor-engineer on sonnet
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test` (invai-floor @0dd01ee) | tsc clean; biome 81 files clean; 12 files / 109 passed |
| New tests run against base `ef1d926` (archive in /tmp) | 9 of the new tests fail on base (busy kind, retryAfterSec schedule, resolved publish, reducer R1/AC3, Thumbnail de-dupe + expiry); proofs are real |
| `scan-test-weakening.sh invai-floor ef1d926` | 0 assertions removed, 27 added; the 429 `it.each` case was replaced by a stronger busy test; no skip/only/snapshot/config hits |
| Scratch PressStation render probe (/tmp, deleted; mocks submit and publishes `resolved` as `flushOnce` does) | A: an online sent BLOCKED scan gives feedback `["tick"],["error"],["error"]`; B: busy plus wrong blank shows BLOCKED + "Busy - confirming in 7 s", no PRESS; busy UPC shows BUSY, no offline text; C: a stale answer for scan 1 leaves scan 2's panel alone (R1 met); the same scan's late BLOCKED replaces provisional PRESS |
| Screenshots /tmp/p3-floor/02, 06, 07 viewed | Amber BUSY/OCUPADO, no raw keys, buttons don't wrap at 1280x800 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `classifyStatus` gives 429 -> `busy`; probe B; screenshots 02/06. Offline and timeout paths unchanged (TIMEOUT still counts as an attempt) |
| 2 | yes | `schedule()` uses `retryAfterSec`, clamped to 1-60 s (test: 9000 ms); busy is never parked (20-flush test). Backend always sends `data.retryAfterSec` >= 1 (`lib/errors.ts:65`, ratelimit.ts:159) |
| 3 | yes, but see finding 1 | Probe C plus reducer tests; wrong blank never PRESS; R1 met (same clientScanId only) |
| 4 | yes | Shared in-flight promise; failures not cached; drops a cached URL 30 s before `expiresAt`; 45 -> 26 calls reported |
| 5 | yes | en/es in both catalogs (typed); screenshots viewed |

## Blocking findings
1. `invai-floor/src/stations/PressStation.tsx:142-152` with `src/outbox/outbox.ts:172`: `flushOutbox` publishes every sent scan in `resolved`, including normal online ones, because `submit` goes through `flush`. The effect does not check that the view is still provisional or queued. So after `runCheck` applies the live result, the effect takes the same entry, re-applies it and calls `feedback()` a second time. Failure: on every online press scan, not only busy ones, the presser hears the OK chirp or the long error buzz twice (probe A: `error`, `error`). This regresses the floor's main scan signal. Fix: apply or beep only when `state.view.provisional || state.view.queued`, and drop or clear the entry otherwise. Or publish only entries with `replay: true`. Add a component or engine test that a live scan beeps once.

## Checks
- [x] Only owned paths changed: 16 files, all `invai-floor/src/**`
- [x] Nothing outside scope (no backend, contract or e2e edits)
- [x] Tests exercise the behavior and none were weakened (fail-on-base shown above)
- [x] Tenancy/idempotency n/a (client only; same clientScanId kept on retry); money n/a; en/es present
- [x] Decisions: none needed

## Optional notes (not blocking)
- `resolved` is never cleared for pick and pack scans, or for press scans after Next: entries pile up in memory for the whole shift. The fix for finding 1 can clear them too.
- es `press.busyQueued` "Vuelve a intentarlo en {{n}} s" tells the presser to retry themselves; the en text means it retries on its own. Suggest "Ocupado. Se verificará otra vez en {{n}} s."
- The replay-rejected alert still says "escaneo sin conexión" for a scan that was busy, not offline (existing copy, screenshot 07).
- `Thumbnail` treats an unparsable `expiresAt` (NaN) as never expiring. The backend sends ISO, so this is low risk.
