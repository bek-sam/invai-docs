# Review of T-4-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: floor-engineer on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
Worktrees: `invai-floor-t42-r1` @ `aba5ccf` (invai-floor `main` already sits at `aba5ccf`), `invai-backend-t42-r1` @ `bdffe6f` (HEAD), both with `node_modules` symlinked to the parent repos. DB copy `invai_r42_copy` (`docker exec local-postgres-1 createdb -U invai -T invai invai_r42_copy`, then migrated). API on :3193 (`REDIS_URL=redis://localhost:6379/11`), floor dev server on :5193 (`VITE_API_PROXY=http://localhost:3193`).

| Command | Result |
|---|---|
| `invai-floor-t42-r1$ ./node_modules/.bin/tsc --noEmit` | clean, 0 errors |
| `invai-floor-t42-r1$ ./node_modules/.bin/biome check .` | "Checked 69 files … No fixes applied" |
| `invai-floor-t42-r1$ ./node_modules/.bin/vitest run --passWithNoTests` | 6 files, 71 passed |
| `invai-floor-t42-r1$ ./node_modules/.bin/vite build` | built; main chunk 265.43 KB gzip (matches the author's report) |
| `invai-backend-t42-r1$ ./node_modules/.bin/tsx src/db/migrate.ts` (on `invai_r42_copy`) | "up to date" |
| `invai-backend-t42-r1$ ./node_modules/.bin/tsx src/api/server.ts` on :3193 | `{"ok":true,"db":true,"redis":true,"s3":true}` |
| `invai-floor-t42-r1$ E2E_FLOOR_URL=http://localhost:5193 E2E_API_URL=http://localhost:3193 ./node_modules/.bin/playwright test e2e/offline.spec.ts e2e/press.spec.ts` | 2 passed (7.4s) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-floor-t42-r1 04b34d9` | 5 removed assertions, all replaced by equal-or-stronger coverage after an intentional, documented behavior change (see below) |
| Archived `origin/main` (`04b34d9`), copied in the new `src/outbox/outbox.test.ts`, ran it against the old source | 21/25 new/changed tests fail on old code (missing exports, wrong shapes) — the new tests prove real new behavior |
| Ad hoc scratch test (`src/outbox/_scratch-review.test.ts`, written, run, then deleted — never committed): `engine.submit()` under a permanent 500, flushed 5x | `useSyncStore.getState().alerts` contains the `gave_up` entry — see Blocking findings |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Parking | yes | `outbox.ts:150-176` (backoff 3→6→12→24→48s, `MAX_ATTEMPTS=5`, ≈93s), unit tests "retries a 5xx … up to 5 attempts", "parks any other 4xx at once"; parked entries are skipped by `unresolvedEntries`/`flushOutbox`'s pending query so they never block (verified: `flushOutbox` only ever selects `status === "pending"`) |
| 2 Problems sheet | yes | `sheet-lead-{en,es}.png`, `sheet-presser-{en,es}.png`, unit tests for retry/discard/badge/pruning; badge (`sync.ts:194`) counts `pending+parked` only, `pruneDone` (`outbox.ts`) removes `done` after 60s |
| 3 Rejected replays | **partially** | `blocked`/`rejected` replays correctly alert (`alert-{en,es}.png`, E2E). But the same alert also fires for `gave_up` (never actually rejected — see Blocking finding 1), beyond what AC3 asks for ("a replayed command that the server rejects") |
| 4 Attribution | yes | Unit tests (`attribution` describe block), live run in the author's report, code walk of `sameAuthor`/`sendAsMe`/`resumeOwnEntries`. Never resent as whoever is signed in now |
| 5 Forgetting the station | yes | `forget-{en,es}.png`, `ForgetStationDialog` (`LoginScreen.tsx`), `parkForForgottenStation`, unit test |
| 6 `storage.persist()` | yes | `requestPersistentStorage()` (`actions.ts`), called at `connectStation`; correctly caveated as device-dependent |
| 7 E2E `offline.spec.ts` | yes | Re-ran myself on a fresh DB copy: passed (4.1s), `press.spec.ts` still passes after it (2.7s) |

## Blocking findings
1. `src/outbox/sync.ts:177`, `src/components/SyncStatus.tsx:394-410` (`ReplayAlert`), `src/i18n/en.ts:97-103`, `src/i18n/es.ts:100-106` — an entry parked for `gave_up` (5 attempts of 5xx/408/429/timeout — the server never returned a verdict on the unit) is put in `alerts` alongside real `rejected`/`blocked` entries and pops the same full-screen "N offline scan(s) was/were **rejected** … **find these units and set them aside**" dialog with the error sound. Confirmed by running a throwaway test: `engine.submit()` under a permanent 500 for 5 flushes puts the `gave_up` entry straight into `useSyncStore().alerts`. **Concrete failure scenario:** the shop's API restarts for 90 seconds during a rush. A presser's press scan gives up after 5 attempts (never rejected — the server just never answered), and the tablet pops a red "1 offline scan was rejected — find this unit and set it aside," telling the presser to pull a shirt that was almost certainly pressed correctly, purely because the server was briefly unavailable. This is the opposite of floor-engineer.md's non-negotiable rule 6, "overload is not an error," and exceeds what AC3 asks for (a real server rejection). **Fix:** exclude `parkReason === "gave_up"` from the `rejected` filter at `sync.ts:177`; it can stay in the Problems sheet with its existing "The server kept failing. Tried 5 times" text (no alert, no "set aside" instruction, no error sound). I am not asking for a change to the 5-attempt/~90s parking policy itself (AC1 specifies it, and it is a reasonable trade-off since ordinary blips self-heal well inside 90s and "Try all again" is one tap) — only for `gave_up` to stop being treated as if the server had rejected the unit.

## Checks
- [x] Only owned paths changed (`git diff --stat 04b34d9..aba5ccf`): `e2e/offline.spec.ts`, `src/app/actions.ts`, `src/components/SyncStatus.tsx`, `src/i18n/{en,es}.ts` (own hunks only), `src/outbox/{db,outbox,sync,outbox.test}.ts`, `src/screens/LoginScreen.tsx` — all within T-4-2's owned globs
- [x] Nothing outside scope: no other repo touched; no contract/backend edits
- [x] Tests exercise the behavior, and none were weakened: the scan script's 5 removed assertions are all from the intentional switch from "resend an auth failure under any current session, else stop the whole flush" to "resend only for the same author, else park just that entry and continue" (Decisions, card AC4/AC1) — every removed behavior has an equal-or-stronger replacement test ("never sends an entry as whoever is signed in now", "does not re-send as the same person on another station", "resumes parked entries when their author signs in again"). No `.skip`/`.only`, no loosened assertions on unrelated behavior, no mocking of the unit under test
- [x] Tenancy / idempotency / money / en-es: n/a for tenancy (client-only, no DB tables); idempotency unchanged (`clientScanId`, `isAlreadyApplied` for non-scan replays); en/es both complete for the new `outbox` block (finding 1 is a content bug present identically in both languages, not a missing-translation bug)
- [x] Decisions recorded where needed: report's "Decisions" section covers attribution, the lead role set, BLOCKED-replay non-retry, timeout-counts-as-attempt, no Dexie bump — reasonable and consistent with the card. None of these rise to a numbered `invai-docs/decisions/` entry (T-4-2's own scoped implementation choices, not a cross-cutting product decision like 0002/0010), though "who is a lead" will likely recur in T-4-3/T-4-4 — see Optional notes

## Rulings on the author's four open decisions
1. **Attribution (park instead of "sent as original staff with a flag"):** acceptable — this is literally the card's second stated option ("or it's parked for a lead to confirm"), not a deviation.
2. **Who counts as a lead (owner, admin, office):** acceptable. There is no formal "lead" role; office already gets comparable floor-adjacent grants elsewhere in wave 4 (`production.receive`). Non-blocking: get product-designer sign-off on the copy, as the author already flagged.
3. **Outages parking entries one by one after ~90s:** the ~90s-then-park design matches AC1 as written and is a defensible trade-off — no change required to the policy itself. What I do require is Blocking finding 1: don't let a `gave_up` (no verdict) entry masquerade as a `rejected` (real verdict) one in the alert.
4. **Security — retry/remove/send-as-me enforced only on the tablet:** confirmed safe. Every path that actually sends a command reuses a real, already-authenticated session token: either the original author's stored token (unchanged permissions — a retried entry is checked by the server exactly as it would have been the first time) or the current lead's own token via `sendAsMe` (their own real permissions, visibly recorded under their name). Nothing synthesizes or elevates an identity; the server's existing permission checks are what actually gate the effect. One non-blocking asymmetry: `retryEntries` (`src/app/actions.ts:137`) has no `isLead()` guard, unlike `sendEntryAsMe`/`discardParked` (`actions.ts:144-158`). The UI already hides the retry buttons from non-leads (`SyncStatus.tsx`: `{lead && parked && …}`), and calling it directly would still only resend under the entry's existing session, so this isn't a privilege escalation — just missing defense-in-depth. Recommend adding the same guard for consistency.

## Optional notes (not blocking)
- A `pending` (not yet parked) entry created *before* this upgrade lacks `staffId`/`stationId` (both new fields). If such a straddling row then hits a 401 under the new code, it parks with reason `session` but `entry.stationId` is falsy, so `canSendAsMe` (requires `!!entry.stationId`) is also false — the row becomes discard-only, with no automatic or lead-assisted resend path (only a manual re-scan recovers the work). Narrow, deploy-boundary-only window; not data loss (visible, describable, discardable) but worth a one-line mention in the report's gaps.
- Consider a lightweight `invai-docs/decisions/` entry for "who is a floor lead," since T-4-3 and T-4-4 will likely need the same answer.
