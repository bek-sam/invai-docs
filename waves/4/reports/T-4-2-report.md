# Report: T-4-2 The floor offline queue never jams
Author: floor-engineer on Opus 5.5

Commits (invai-floor, `main`, not pushed):
- `f491737` Floor: offline queue that never jams (T-4-2, B-95)
- `aba5ccf` Floor: exhaustive command-kind switches in the outbox UI (T-4-2). This follows the tech lead's note so that T-4-4's `packOrder` kind fails typecheck until it's handled.

## Intake
```
Card: T-4-2  Owner: floor-engineer  Scope ref: product/scope.md#mvp-in item 5 (B-95)
Owned (edit): invai-floor/src/outbox/** (db.ts, not src/app/db.ts), src/app/actions.ts,
  src/components/SyncStatus.tsx, src/screens/LoginScreen.tsx, e2e/offline.spec.ts (qa co-owns),
  my own i18n keys (hand edit, only my hunks)
Read-only: contracts, backend, invai-ui, stations/*, StationShell.tsx, src/api/**
Risk flags → co-reviewers: floor-correctness → reviewer + qa-engineer, security-reviewer
Unknowns: the contract has no field for "attributed to the original staff with a flag"
  → decided: park + same-person resume + explicit lead "send as me" (see Decisions)
```

## Built
- **Parking** (`src/outbox/outbox.ts`, `db.ts`):
  - A 5xx, 408 or 429 (and `NOT_IMPLEMENTED`, `RATE_LIMITED` or a request timeout) stops the flush and retries with the engine's 3→60 s backoff. After `MAX_ATTEMPTS = 5` in a row the entry is parked `gave_up`, and the flush moves on.
  - Any other 4xx parks the entry at once as `rejected`.
  - Being offline (network error) never counts as an attempt.
  - Parked entries are never picked up by the flush, so they can't block later entries.
- **Schema, with no Dexie version bump:**
  - New optional fields: `parkedAt`, `parkReason`, `errorCode`, `staffId`, `stationId`, `unit` and `replay`.
  - New `"parked"` status. Legacy `"failed"` rows read as parked (`isParked`, `parkReasonOf`).
  - `undefined` is read as `null` everywhere (tested with a hand-built legacy row).
- **Problems sheet** (`SyncStatus.tsx`). Tapping the sync badge opens "Not sent yet" / "Sin enviar", which lists pending and parked entries oldest first:
  - what (command kind and station)
  - which unit (order, design, brand/style/color/size, tote)
  - when (locale time)
  - who ("By Pat Presser")
  - why, translated: the mismatch for BLOCKED, the error code in plain words for a 4xx, "tried 5 times", "sign-in ended" or "station forgotten"
- **What leads can do.** Owner, admin and office can:
  - retry (or "Try all again")
  - remove, with a confirm
  - "Send as me", with a confirm naming them, for entries whose sign-in ended
- **The badge** shows pending plus parked ("needs a check"), or "All synced". Sent entries are pruned after 60 s; the old limit was 24 h.
- **Rejected replays.** An entry that was saved offline (the `replay` flag is set atomically when `submit` returns `queued`) and is later refused raises a red modal with each unit, the reason, who and when, plus the error sound. This covers scans BLOCKED by the server, and QC, tote and reprint changes refused with a 4xx. The alert has "OK" and "See the list", and it swallows scans while open. A live BLOCKED scan stays a normal station result. An ended sign-in is listed but not alerted, because it isn't a verdict on the unit.
- **Attribution** (`actions.ts`, `outbox.ts`):
  - Every entry stores `staffId` and `stationId` next to its session token.
  - The old fallback that re-sent with *whoever is signed in* is gone.
  - On a 401 the entry is re-sent only under the same person's new session on the same station. Otherwise it's parked as `session`.
  - When that person signs in again on that station (`resumeOwnEntries` in `login()`), their entries go back in the queue under their new token.
  - A lead can instead send it explicitly under their own name.
  - The tablet only locks itself when the signed-in person's own session ended.
- **Forget this station** (`LoginScreen.tsx`):
  - `window.confirm` is replaced by a dialog. With unsent entries it says "1 scan on this tablet hasn't been sent… it will never be sent", and the button repeats the count ("Forget and don't send 1").
  - `forgetStation()` parks every pending entry as `station_forgotten`. Those entries can't be retried or sent as anyone, only removed.
- **Storage:** `navigator.storage.persist()` is requested at pairing (`connectStation`), and the result is stored in kv `storagePersisted`.
- **i18n:** one new `outbox` block in `en.ts` and `es.ts`, with no edits to existing keys.
- **E2E** `e2e/offline.spec.ts`:
  1. Pair a press station, presser PIN, wait for the queue to be cached.
  2. `setOffline(true)` and press 3 units (each "Checked on this tablet").
  3. The office holds the second unit's order.
  4. Reconnect. The alert names the order with "Order on hold", the badge shows "1 needs a check", and nothing is pending.
  5. The server shows 2 units `pressed` and 1 `on_hold`. The sheet shows 1 parked row.
  6. A 4th scan gets a live PRESS, so nothing is jammed.

  The spec prefers units from multi-unit orders, so the single-unit order that `press.spec` needs is left alone on a fresh seed (13 press-ready units on 7 orders).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Parking | yes | Unit tests: "retries a 5xx … up to 5 attempts, then parks it and moves on", "treats a 408/429 like a 5xx", "counts a timeout as an attempt, but not being offline", "parks any other 4xx at once, including 403 and 404" |
| 2 Problems sheet | yes | `sheet-lead-{en,es}.png`, `sheet-presser-{en,es}.png` (the non-lead view says who can act), `sheet-confirm-{en,es}.png`, `demo-sheet-en.png`. Unit tests cover retry, remove, the badge counts and pruning |
| 3 Rejected replays | yes | `alert-{en,es}.png` ("Order #1506 · Monsoon Season · Gildan 64000 Black 3XL — The server BLOCKED it: Order on hold"). The E2E asserts the order number and reason. Unit test "flags an entry saved offline and raises an alert…" |
| 4 Attribution | yes | Unit tests: "never sends an entry as whoever is signed in now", "re-sends under the same person's new session on the same station", "…not on another station", "resumes parked entries when their author signs in again", "a lead can send… only under their own name". Real stack run below |
| 5 Forget station | yes | `forget-{en,es}.png`. The real run showed the forgotten scan never reached the server; unit test "forgetting the station parks unsent entries so they are never replayed" |
| 6 `storage.persist()` | yes (requested) | Called at pairing. Headless Chromium answered `false` (Chrome grants it heuristically); on a real installed PWA it's usually granted |
| 7 E2E | yes | `offline.spec.ts` passed on a fresh DB copy (4.1 s), and `press.spec.ts` still passes after it |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-floor | `tsc --noEmit` | clean (0 errors; T-4-3's stub errors were fixed by its commits) |
| invai-floor | `biome check .` | "Checked 62 files … No fixes applied" |
| invai-floor | `vitest run` | 71 passed (25 in `outbox.test.ts`) |
| invai-floor | `vite build` | built. Main chunk 265.43 KB gzip vs 260.71 KB at HEAD before my work; that figure includes T-4-3's receiving station. No dependency changes |
| invai-floor | `playwright test e2e/offline.spec.ts e2e/press.spec.ts` (floor :5124 → API :3120, fresh `invai_t42_copy`) | 2 passed (7.3 s) |

## Exercised for real
Stack for these runs:
- The API and worker ran from a clean backend worktree at `d45e155` (T-4-1's head, after migrating the copy as the tech lead asked).
- They used port 3120, `REDIS_URL=redis://localhost:6379/2` and a DB copy freshly cloned from `invai` before each run.
- The floor dev server was on 5124, proxying to 3120.

A scratch Playwright scenario ran in en and es, and was deleted afterwards. Outbox rows are shown as `staff:status:reason`:
- **Offline A + B; the office holds A's order; reconnect.** A was parked `blocked` and alerted; B went to `done`.
- **Offline C + D; Pat's session revoked on the server; lock; reconnect.** Result: `Pat:parked:session` ×2. On the server C and D were both still `transfer_in`, so nothing was credited to anyone.
- **Owner (PIN 1111) signs in and uses "Send as me" on C, then removes A.** Result: `Riley Owner:done` for C, with C `pressed` on the server; D stayed `parked:session`.
- **Pat signs in again.** Result: D resumed and was `pressed` under Pat (`Pat Presser:done`).
- **Offline E; lock; forget the station (dialog showed the count); back online.** Result: E was `parked:station_forgotten`, and on the server E stayed `transfer_in`, so it was never replayed.
- **Demo mode** (`?demo=1`): PIN, the press station, and the sheet showing "All synced".
- **Refused case:** as a presser, the sheet shows no retry, remove or send buttons, only "The office, an admin or the owner can retry or remove these" (`sheet-presser-*.png`).

Screenshots at 1280×800, all looked at, are in `invai-docs/waves/4/reports/T-4-2/`:
- `alert-en/es`, `sheet-presser-en/es`, `sheet-lead-en/es`, `sheet-confirm-en/es`, `forget-en/es`, `demo-sheet-en`
- No raw keys or English fallbacks in Spanish, except the `@invai/ui` header "Online", which is known (see gaps).

## Decisions
- **Attribution without a contract change.** `ScanInput` has no "on behalf of" field, so the card's first option ("sent attributed to the original staff with a flag") would need an architect stub. I took the second option: park the entry. It then resumes automatically for the same person on the same station, or a lead explicitly sends it under their *own* name. That records the lead, visibly, and never the person silently signed in now. If shops want original-staff attribution after a session ends, the architect needs to add an attribution field to `ScanInput`/`QcInput` (follow-up).
- **Who is a "lead":** roles `owner`, `admin` and `office` (`isLead` in `actions.ts`). There is no lead role. The copy avoids the new word "lead" and says "needs a check" / "necesita revisión" and "The office, an admin or the owner…". The product-designer should confirm.
- **A BLOCKED replay can't be retried,** since the same `clientScanId` gets the same stored answer. It can only be removed after someone sets the shirt aside. A `station_forgotten` entry can only be removed.
- **Timeouts count toward the 5 attempts** (a slow server, not offline), so a request that always hangs can't jam the queue. Being offline never counts.
- **No Dexie `version(3)`:** the Problems Sheet reads `status in (pending, parked, failed)` from the existing index. `parkedAt` isn't queried.
- **Lock still revokes the session** on the server, so security is unchanged. Entries from that session park until the same person signs in again.

## Known gaps and follow-ups
- **Tension with the floor rule "overload is not an error".** Per the card, a server outage that lasts longer than about 90 s of backoff (5 attempts) parks entries one after another. Nothing is lost, and "Try all again" recovers them in one tap, but the reviewer should confirm this is the intended trade-off (qa-engineer, tech lead).
- Retry, remove and send-as-me are checked on the tablet only (role from the floor session). They touch only this tablet's IndexedDB, and a retry still uses the original author's token, so a presser who bypasses the UI can't gain server privileges (security-reviewer to confirm).
- `navigator.storage.persist()` returned `false` in headless Chromium. It's requested, but the real grant depends on the device.
- Now unused and left for T-4-4, which owns `src/i18n/**`, to remove: `header.failed_one/other` and `press.replayBlocked`.
- At 1280×800 the sheet shows about 2.5 rows before scrolling. The rows could be tighter (product-designer).
- The E2E creates a new press station each run, the same pattern as `press.spec.ts`.

## Blocked by other owners
- `invai-ui/src/floor/station-header.tsx:45` shows English "Online" in the Spanish UI (visible in `alert-es.png`). This is known (B-105) and belongs to the product-designer / T-4-4.
- No other blockers. T-4-3's lines in `db.ts` and `actions.ts` were already committed by T-4-3, and my commits contain only my hunks (checked with `git diff --cached`).

## Processes and data
- Stopped: my API and worker (cwd `invai-backend-t42`) and the floor vite server on :5124.
- Dropped `invai_t42_copy` and flushed Valkey db 2.
- Removed worktrees `../invai-backend-t42` and `../invai-floor-t42`, the scratch spec and `/tmp` outputs.
- Shared dev DB: untouched (only used as the template for the copies). The report and screenshots in `invai-docs` are written but not committed.

## Round 2 (reviews r1: security approved; the reviewer and qa-engineer asked for changes)
Commit `a0d88bd`: Floor: only a server verdict raises the offline-rejected alert (T-4-2 r2). Not pushed.

**Fixed**
- **Blocker (reviewer and qa-engineer), `src/outbox/sync.ts`:** the alert filter is now an allowlist of real server verdicts, `parkReason === "rejected" || "blocked"`.
  - A `gave_up` entry (5 attempts, the server never answered) no longer raises the full-screen "rejected, set these units aside" dialog or the error sound. It stays in the Problems sheet as "The server kept failing. Tried 5 times."
  - `session` and `station_forgotten` also stay out of the alert.
  - New test: "a server that never answers (permanent 500) parks the entry without an alert". It runs `engine.submit()` offline, then a permanent 500 for 5 flushes. The result is `parked/gave_up` with `alerts: []`, and `onReplayRejected` is never called.
- **Recommended, `src/app/actions.ts`:** `retryEntries` now has the same `isLead()` guard as `sendEntryAsMe` and `discardParked`. It returns 0 for a non-lead.

**Checks**
| Command | Result |
|---|---|
| `tsc --noEmit` | clean |
| `biome check .` | "Checked 69 files … No fixes applied" |
| `vitest run` | 72 passed (1 new) |
| `playwright test e2e/offline.spec.ts` against my API on :3120 at backend `bdffe6f`, on a fresh `invai_t42_copy` | 1 passed (3.6 s) |

**Staging:** the shared tree had only my hunks when I committed (no T-4-4 edits in these files). Checked `git diff --cached` before committing.

**Cleanup:** stopped my API, worker and the floor server on :5124. Dropped `invai_t42_copy`, flushed Valkey db 2, removed the worktree `../invai-backend-t42` and `/tmp` output.
