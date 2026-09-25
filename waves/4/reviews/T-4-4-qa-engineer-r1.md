# Review of T-4-4 (round 1)

- Reviewer: qa-engineer on Fable
- Author: floor-engineer on Opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Worktrees: `invai-floor-r44` (base `a0d88bd` + diff, untracked files copied, `node_modules` symlinked), `invai-ui-r44` (base `e7a7e31` + diff) | set up clean, matches the shared trees' now-committed state (`df18e53`/`178c829`) exactly (diffed to confirm) |
| `invai-floor-r44`: `tsc --noEmit`, `biome check .`, `vitest run --passWithNoTests`, `vite build` | clean / clean / 7 files, 82 tests passed / built (268.64 KB gzip main bundle) |
| `invai-ui-r44`: `tsc --noEmit`, `biome check .`, `vitest run` | clean / clean / 4 files, 20 tests passed |
| Backend: fresh DB copy `invai_r44_copy` (`createdb -T invai`), `pnpm db:migrate` (up to date), API on `:3194` (`DATABASE_URL` → the copy, `REDIS_URL=redis://localhost:6379/13`, `FLOOR_ORIGIN=http://localhost:5194` — needed for CORS at a non-default port), worker on the same DB/Redis, invai-backend HEAD `bdffe6f` (includes T-4-1) | API `/health` ok, worker running |
| Floor dev server on `:5194` (`VITE_API_URL=http://localhost:3194`) from `invai-floor-r44` | up |
| `E2E_API_URL=http://localhost:3194 E2E_FLOOR_URL=http://localhost:5194 playwright test e2e/floor.spec.ts e2e/offline.spec.ts e2e/press.spec.ts` | **3 passed, 0 failed** (8.8s) — floor.spec.ts (pack with a missing unit blocked, then complete), offline.spec.ts (T-4-2's suite, unaffected by this card), press.spec.ts (pair/PIN/wrong-style-BLOCKED/press/QC/pack, includes the `wrong_style` regression check) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-floor a0d88bd` | 1 hit (the `pressFlow.test.ts` assertion, see below), otherwise clean: no `.skip`/`.only`, no deleted test files, no config loosening |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-ui e7a7e31` | clean |
| Ran the changed `pressFlow.test.ts` against an `a0d88bd` archive (base code, before this card) | **fails on base code** (6/19 tests fail, expected `message: null` but base code produces `message: "server text"`) — this is the proof the assertion is a real fix, not a weakened check |
| Read `src/api/packOrder.test.ts` in full | exercises `commandId`/idempotency-key-as-entry-id, a live refusal not parking an entry, an offline-replayed short pack parking with `errorCode: "pack_incomplete"`, a replayed hand-over completing, and — the specific ask — a `CONFLICT` (on-hold order) being parked and **not** counted as already applied. Also exercises the demo backend's role gating (packer FORBIDDEN, owner/admin allowed) and idempotent replay (`again` equals the first result) |
| Cleanup | killed API/worker/floor dev server, confirmed `lsof -iTCP:3194,5194 -sTCP:LISTEN` empty; dropped `invai_r44_copy`; removed both worktrees (`git worktree remove --force`); shared dev DB `invai` untouched throughout |

## Acceptance criteria (test coverage focus)
| # | Met? | Evidence |
|---|---|---|
| 1a/1c/7 Pack with a missing unit blocks, lists it, persists across reload, completes | Yes | `e2e/floor.spec.ts` — read the whole file: it deliberately makes the tablet's pack list stale via `page.route` (since the real server never lists a short order — the server-side check is real, only the client's view of the queue is faked for test setup, which is a legitimate way to reach an otherwise-unreachable client state) and drives the full blocked → reload-restores → complete path against the real backend. Ran green |
| 1b Hand to lead, packer FORBIDDEN | Yes | Live: `e2e/floor.spec.ts` asserts the button is visible for the owner. `packOrder.test.ts`'s demo-mode test explicitly asserts a packer's override attempt `rejects.toMatchObject({code: "FORBIDDEN"})` and that owner/admin succeed with a `PackOverride` recorded; T-4-1's backend test suite (separate card, already reviewed) covers the real server 403 |
| 5 `wrong_style` regression | Yes | `press.spec.ts` (existing suite, unmodified for this AC — a "no regression" check as the card specifies) asserts "Wrong style" and passed live against T-4-1's backend |
| Idempotency of `packOrder` on the client | Yes | `commandId()` (`outbox.ts`) returns `command.input.idempotencyKey` for `packOrder`, the same convention as `clientScanId` for scans — a genuine offline replay of the same entry can't double-submit. A retry of a *refused* "Mark packed" tap (via "Check again") deliberately uses a **new** key (`uuid()` per tap in `PackStation.tsx`), which is correct: the server stores no result for a refusal, so reusing the old key would just hang against nothing stored |
| Offline behavior | Yes | `offline.spec.ts` (T-4-2's, unaffected) still green. `packOrder.test.ts` exercises the offline-specific park path directly (an offline-saved pack that replays short parks as `blocked`/`pack_incomplete`, not silently dropped or falsely reported success), and I confirmed the same live in `floor.spec.ts`'s reload-persistence step |

## Test-integrity scan, in detail
The scan script surfaces one hit in `invai-floor`: `src/scan/pressFlow.test.ts:157-161`, one `toMatchObject` assertion changed from `message: "server text"` to `message: null`.

This is a **correct update, not a weakening**:
- `src/scan/result.ts`'s `viewFromResult` is changed in the same diff from `message: r.ok ? null : r.message || null` to unconditionally `message: null`, with a comment explaining the server's message is English and must never reach the screen (AC4). The test change is the direct, expected consequence of that fix.
- I proved it the hard way per the independent-review playbook: I copied the *new* test file onto a checkout of the pre-change code (`a0d88bd`) and ran it. It fails — the old `viewFromResult` really did leak `"server text"` through. The new assertion is therefore evidence the bug existed and is now fixed, which is the opposite of a weakened test.
- Net effect across the whole diff: 41 assertion lines added, 1 changed (not removed), 0 test files deleted, 0 `.skip`/`.only`/`.todo` added anywhere. Coverage went up.

The new file `src/api/packOrder.test.ts` is not in the card's enumerated owned-paths list, but it is squarely inside floor-engineer's general ownership of `invai-floor/**` (outside `e2e/**`/`*.acceptance.test.ts`/`security.test.ts`, none of which apply here), and it tests only the lines the wave granted this card (`outbox/db.ts`, `outbox/outbox.ts`, `api/rpc.ts`, `api/demo.ts`). It doesn't touch or duplicate anything in `qa-engineer`'s owned `e2e/**` suites, and it doesn't mock the unit under test — it drives real `FloorDB`/`enqueue`/`flushOutbox`/`createDemoApi` code paths. No objection to it staying.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — confirmed against the card's owned-paths list plus `wave.md`'s named grants (see the primary reviewer's file for the full path-by-path accounting; I independently re-derived the same list from `wave.md` and it matches).
- [x] Nothing outside scope.
- [x] Tests exercise the behavior, and none were weakened — see the detailed scan above.
- [x] Golden-path / E2E: `floor.spec.ts`, `offline.spec.ts`, `press.spec.ts` all green against the real stack on a fresh DB copy from a current template.
- [x] Idempotency: `packOrder`'s key discipline (fresh key per user-initiated attempt, stable key on offline replay) is correct and tested at both the unit level (`packOrder.test.ts`) and E2E level (`floor.spec.ts`'s reload step doesn't re-trigger a new attempt, `offline.spec.ts` unaffected).
- [x] Decisions recorded — 0010 is implemented as specified; I did not find any path that lets a packer see or click "Hand to lead," and no path that changes order status via the override (that's T-4-1's server-side guarantee, already reviewed separately, and the client-observed behavior — `orders.get` still showing `in_production` with `packOverride` set — is consistent with it).

## Optional notes (not blocking)
- The demo backend's `packOrder` doesn't cache a *refused* (no-override, units missing) result under its `idempotencyKey` — by design, matching the real server ("A refusal stores nothing on the server, so 'Check again' must be a new request," per the report). I checked this against T-4-1's actual backend implementation notes and it's consistent, not a demo-only quirk that would diverge from production behavior.
- I'd suggest a future card give the offline-replay alert row for `packOrder` its own title text instead of borrowing T-4-2's "N offline scan(s) was/were rejected" — already flagged by the author and the product-designer's review as non-blocking copy work.
