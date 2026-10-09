# T-28-5: Skip poll-started syncs when auto-import is off

| Field | Value |
|---|---|
| Wave | 28 |
| Scope ref | `always-in-scope: bug` (backlog B-261: a poll sync queued before auto-import was switched off still imports orders; it moves the gate's gang-sheet pool and, for a shop, imports orders after they said stop) |
| Spec | backlog B-261; `waves/P7/reviews/plan-architect.md` R1 |
| Owner | backend-engineer (area: channels) |
| Reviewer | `reviewer` (opus) |
| Co-reviewers | none (no risk flag: no contract, migration, auth or tenancy change) |
| Risk flags | none (golden-path area: import; the gate covers it) |
| Model | sonnet |

## Owned paths (edit)
- `invai-backend/src/modules/channels/**` (except `src/integrations/**`)

## Read-only paths
- everything else; `src/modules/jobs.ts`, `src/integrations/**`, `invai-web/e2e/**`

## Depends on
- nothing.

## Interfaces promised
- none (behavior change inside `syncConnection`).

## Acceptance criteria
1. Given a connection with `settings.autoImport === false`, when a **poll-started** sync job runs (`jobId` null/absent; queued by `channels.poll`, possibly before the switch), then it imports nothing, calls no adapter, and leaves the connection's status, `lastSyncAt` and error fields unchanged; a debug log says it was skipped.
2. A **manual** sync (`channels.syncNow`, which passes a `jobId`) still runs when auto-import is off, and its job row ends `done` as today.
3. With auto-import on, poll syncs behave exactly as before (existing tests unchanged).
4. The setting is read when the job runs, not when it was queued (a test switches auto-import off between enqueue and run).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test src/modules/channels 2>&1 | tail -n 40`, then the full backend suite once at the end (`set -o pipefail`, logged, FAIL/Error lines and tail).
- Exercise for real: `PORT=3151 pnpm dev:api` plus a one-off script (`tsx`) that, against the dev DB, turns auto-import off on a seeded mock Shopify connection of Desert Bloom, runs `syncConnection(companyId, connId)` with no jobId and prints `imported: 0`, then with a jobId through `channels.syncNow` as office@ and prints the job's final status; restore auto-import to its previous value in a `finally` block. Record PIDs and stop them.

## Out of scope
- The E2E hold helper (B-263, QA). The poll scheduler itself. Webhook-delivered orders when auto-import is off (`handleWebhook`, `sync.ts` ~905): unchanged here; backlog B-292 asks the PM.

## Budget
- About 1 hour. Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
