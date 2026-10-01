# T-P3-2: The floor shows a 429 as "busy", not "offline", and asks for fewer signed URLs (B-237)

| Field | Value |
|---|---|
| Wave | P3 |
| Scope ref | `always-in-scope: bug` (floor mislabels a server rate limit as offline; P2 gate root cause) |
| Spec | `waves/P2/reports/gate-rootcause.md`; backlog B-237 |
| Owner | floor-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (small UI copy change: reviewer alone, decision 0019) |
| Risk flags | floor-correctness, ui (copy) |
| Model | sonnet |
| Depends on | nothing (T-P3-1 fixes the server side in parallel; this card must work with or without it) |

## What QA found
A 429 `RATE_LIMITED` on `production.scan` is classed `unavailable` (`invai-floor/src/outbox/outbox.ts:95`), `SyncEngine.flushOnce` (`sync.ts:149-168`) reports `queued`, and `PressStation.runCheck` (`PressStation.tsx:77-84`) shows "Checked on this tablet while offline". The retry 3 s later (`sync.ts:200`) gets 200, but nothing re-renders the panel. `Thumbnail.tsx` calls `files.downloadUrl` once per item: its session cache has no in-flight de-dupe, so items mounting together with the same key each make a call.

## Owned paths (edit)
- `invai-floor/src/**` (outbox, sync, api, stations, components, i18n `en.ts`/`es.ts`) and unit tests in `src/`

## Read-only paths
- `invai-floor/e2e/**` (QA owns the E2E suite; if a spec needs a change, say so in the report), `invai-backend/**` (T-P3-1 runs in parallel), `invai-contracts/**`, `invai-web/**`.

## Acceptance criteria
1. A 429 (`RATE_LIMITED`) is its own failure kind, not "offline": the station shows a distinct busy state ("Busy. Checking again in {{n}} s" or similar; es tú form), never the offline wording. Offline (no network) and timeout keep their current behavior.
2. The retry honours the server's `retryAfterSec` (error data or `Retry-After` header), not the fixed 3 s backoff, and a 429 doesn't count toward `MAX_ATTEMPTS` parking.
3. When the queued scan's server answer arrives after a busy retry, the press panel replaces the busy state with the server's result (BLOCKED or PRESS). **Floor correctness:** a wrong blank is never shown as PRESS, and while busy the panel never shows a go state the server hasn't confirmed or the local check hasn't passed.
4. Fewer signed-URL calls: concurrent `fileUrl` requests for the same key share one in-flight promise; failed lookups aren't cached; cached URLs are dropped before their signed expiry (read the backend's expiry; don't change it). Report the before/after call count for one queue load.
5. English and Spanish strings in both catalogs; screenshots of the busy state at 1280×800 in en and es, looked at (no wrapping on buttons, no raw keys).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 40` in `invai-floor`.
- Unit tests: outbox/sync classify 429 apart from offline and timeout, use `retryAfterSec`, don't park on 429; the panel updates after a busy retry; the thumbnail de-dupe.
- Exercised for real: your own API `PORT=3137` with `REDIS_URL=redis://localhost:6379/14` and a floor dev server on a free port (e.g. 5184) pointed at it (read `vite.config.ts` for how the proxy target is set). Pair with the station token from `invai-backend/seed-output.json`, sign in with a presser PIN, set `tb:writes:<companyId>` to 0 tokens in Valkey DB 14, scan a wrong blank: see the busy state, then the server's BLOCKED once tokens refill. Screenshot both. Flush DB 14 afterwards.
- `pnpm e2e` in `invai-floor` against your own stack if you can point it there (`E2E_FLOOR_URL`, `E2E_API_URL`); otherwise the gate runs it.

## Out of scope
- Backend bucket classification (T-P3-1); any limit change; a batch signed-URL procedure (needs a contract change: note it in the report if you think it's needed).

## Rules
- Role file `.claude/agents/floor-engineer.md`; `team/agent-brief.md`; playbooks `build-floor-flow`, `write-plain-language-copy`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/floor-engineer/`.
- Commit only your paths in `invai-floor`, message ends with the attribution line. **Don't push; only the tech lead pushes after the gate.**
- Ports: API :3137, floor dev :5184. Don't touch :3000, :5173, :5174, :8000. Record every PID you start in the report and stop them before reporting. Don't reset the dev DB.
- Report (≤ 60 lines, `verify-and-report` format) to `invai-docs/waves/P3/reports/T-P3-2.md`; add one progress line there after each milestone. Put screenshots in `/tmp/p3-floor/` (not in a repo) and delete them after the review.

## Budget
- Escalate to the tech lead if blocked for about 30 minutes of work.

## Queued ruling (architect plan review, 2026-10-01; added after the build started, so it's checked at review and built in round 2 if missing)
- R1. AC3's "replace the busy state with the server result" applies only when the result's `clientScanId` still matches the scan on screen. A late result for an earlier scan must never overwrite the panel for a scan the presser has moved on to.

## Round 2 (tech lead, from `reviews/T-P3-2-reviewer-r1.md`)
1. **Blocking:** a live (online) press scan applies its result and plays its sound twice, because every sent scan is published to `resolved` and the PressStation effect (`PressStation.tsx:142-152`, `outbox.ts:172`) doesn't check the view. Apply a resolved result only when the view is still provisional/queued/busy for that `clientScanId` (or publish only replayed entries). Test: one live BLOCKED scan plays exactly one sound and renders once.
2. Clear `resolved` entries once consumed or when their station unmounts (pick, pack and abandoned press scans must not pile up over a shift).
3. Copy: es busy text says it retries on its own (not "Vuelve a intentarlo"), matching English; the rejected-scan alert for a busy scan must not say "sin conexión"/offline in either language.
