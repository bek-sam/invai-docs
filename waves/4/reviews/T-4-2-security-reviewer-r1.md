# Review of T-4-2 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: floor-engineer on Opus 5.5
- Verdict: approve

Note on scope: the card's risk flag is `floor-correctness`, not one of security-reviewer's mandatory-co-review flags (tenancy, PII, auth, webhooks, files, payments) — the author raised an open security question themselves (decision 4) rather than the card requiring this seat. I reviewed with fresh, code-only context per `independent-review`/`threat-model-change`, same as any co-review.

## Threat model (per `threat-model-change`)
- **Entry points touched by this change:** none are new server entry points — T-4-2 is floor-client-only (IndexedDB/Dexie state and UI). The server-side procedures it calls (`production.scan`, `qc`, bin, reprint, `floor.login`) are unchanged by this card; only *when* and *under which stored session* the client calls them changed.
- **Who could call what, with which session:** every send in `flushOutbox`/`sendAsAuthor` (`src/outbox/outbox.ts`) uses either (a) the entry's own stored `sessionToken` (the original author's real floor session, unchanged), or (b) the current signed-in user's own real floor session (`sendAsMe`, `resumeOwnEntries`). No code path constructs or borrows a session that wasn't already a valid, currently-issued token for a real, authenticated person. The tenant/company is bound server-side to the session as it always was; nothing here lets a client claim a different session's identity.
- **Worst outcome if the client-side gates (`isLead`) were bypassed entirely** (e.g. via devtools console on a compromised tablet): a non-lead could tap "retry" (already ungated at the function level, see finding below) or, if they also bypassed `sendEntryAsMe`'s guard, "send as me." In both cases the resulting network request is still authenticated by a real session — either the original author's (server re-checks that author's actual permissions, same as a live retry) or the *bypasser's own* session (server checks their own real permissions). No new server-side capability is unlocked; at most, a non-lead could locally re-attempt a parked entry that a lead would otherwise have triaged first — a workflow/attribution concern, not an authorization bypass. Severity: none (this is not a High/Medium finding under the severity table — no cross-tenant access, no auth bypass, no PII exposure, no privilege escalation, since the server's own permission check is unchanged and is what actually gates every effect).

## Evidence I re-ran
Same stack as the primary reviewer: worktrees `invai-floor-t42-r1` @ `aba5ccf`, `invai-backend-t42-r1` @ `bdffe6f` (HEAD), `node_modules` symlinked, DB copy `invai_r42_copy` (createdb -T invai, migrated), API :3193 (`REDIS_URL=redis://localhost:6379/11`), floor :5193.

| Command | Result |
|---|---|
| `invai-floor-t42-r1$ ./node_modules/.bin/vitest run --passWithNoTests` | 6 files, 71 passed, incl. the `attribution` and `sync engine` describe blocks |
| `E2E_FLOOR_URL=http://localhost:5193 E2E_API_URL=http://localhost:3193 ./node_modules/.bin/playwright test e2e/offline.spec.ts e2e/press.spec.ts` | 2 passed (7.4s) |
| Read `src/outbox/outbox.ts` (`sendAsAuthor`, `sameAuthor`, `sendAsMe`, `resumeOwnEntries`, `retryParked`) and `src/app/actions.ts` (`currentSession`, `isLead`, `retryEntries`, `sendEntryAsMe`, `discardParked`) in full | no path builds a session token from anything other than a real, currently-valid `useApp.getState().session` or an entry's own previously-stored `sessionToken` |
| `grep -n "sessionToken" src/outbox/outbox.ts` | every send site passes either `entry.sessionToken` or `current.token`/`current.userId`-sourced values, never a client-supplied identity string |
| `grep -rn "withSystem(\|company_id\|RLS" invai-floor-t42-r1/src` | no results — confirms this card touches no server/DB tenancy surface |

## Acceptance criteria (security-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| 4 Attribution | yes | `sameAuthor` requires both `staffId` and `stationId` to match the *current, real* session before an auto-resend happens (`outbox.ts`); a 401 with no match parks as `session`, never silently resent as whoever is signed in |
| 5 Forgetting the station | yes | `parkForForgottenStation` marks unsent entries so they can never be replayed under a different station's token; `canRetry`/`canSendAsMe` both explicitly exclude `station_forgotten` |

## Blocking findings
none

## Ruling on decision 4 (security)
**Confirmed.** Retry, "send as me" and remove are gated in the UI only (`isLead()` in `src/app/actions.ts`, checked before rendering the buttons in `SyncStatus.tsx`), but this is safe because none of the three ever fabricates a session: a retry resends under the entry's own already-issued `sessionToken` (the original author's session, so the server enforces that author's actual permissions exactly as it would on a live scan), and "send as me" explicitly switches the entry to the *current, really-authenticated* lead's own token (`sendAsMe`, `actions.ts:144-152`), which the server then checks under that lead's own real permissions. The server is therefore the actual enforcement point in both cases, matching the author's own reasoning.

One non-blocking asymmetry, for defense-in-depth rather than because it's currently exploitable: `retryEntries` (`src/app/actions.ts:137-141`) has no `isLead()` guard at the function level, while `sendEntryAsMe` (`actions.ts:144-152`) and `discardParked` (`actions.ts:154-158`) both check it. Today this is harmless — a bypass only resends an already-authorized token — but I'd rather every lead-only action be defended at the function boundary, not only by what the UI renders, in case a later change makes `retryEntries` do something less inert. Recommend adding the same guard for consistency; not blocking this review.

## Checks
- [x] Only owned paths changed (`git diff --stat 04b34d9..aba5ccf`)
- [x] Nothing outside scope; no contract, backend, or tenancy-table changes
- [x] Tests exercise the behavior, none weakened (see the primary reviewer's and qa-engineer's files for the full `scan-test-weakening.sh` breakdown — I independently read the same diff and agree: the 5 removed assertions belong to a deliberately replaced auth-fallback test, superseded by stronger, more specific tests)
- [x] Tenancy / idempotency / money / en-es: n/a for tenancy (no server or DB surface in this card); idempotency preserved (`clientScanId` unchanged, no new re-send path bypasses it); PII: no new PII is stored or logged — `OutboxUnit` carries only order/design/blank/tote labels already visible on the tablet, nothing beyond what the presser already sees on screen
- [x] Decisions recorded where needed

## Optional notes (not blocking)
- I reviewed and agree with the primary reviewer's Blocking finding 1 (the `gave_up` entry wrongly raising the "rejected" `ReplayAlert`) — it is a floor-correctness/UX bug, not a security issue, so it does not change my verdict here, but the card cannot ship until the primary reviewer's file also says `approve`.
- Add the `isLead()` guard to `retryEntries` (see above) next time this file is touched.
