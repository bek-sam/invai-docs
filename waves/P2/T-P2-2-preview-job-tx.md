# T-P2-2: Floor scan timeout: prove the cause, then take the imaging call out of the DB transaction (P1 gate fix 2, B-233 part)

| Field | Value |
|---|---|
| Wave | P2 |
| Scope ref | `always-in-scope: bug` (P1 gate failure, `waves/P1/reports/gate-rootcause.md` §2; B-233) |
| Spec | `waves/P1/reports/gate-rootcause.md` §2; backlog B-233 |
| Owner | backend-engineer (catalog) |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (sonnet), `files` flag: the tenant key checks (`isCompanyKey` on both keys) move with the code |
| Risk flags | files |
| Model | sonnet |
| Depends on | nothing |

## What QA found
- Gate run 2: one floor `production.scan` hit the floor client's 10 s timeout (`invai-floor/src/api/rpc.ts:13`) and fell back to the offline check; `press.spec.ts:9` took 16.5 s (A2: 2.7 s). No API restart during the suite.
- Leading hypothesis, **unproven**: the `catalog.renderDesignPreviews` job (`src/modules/catalog/jobs.ts:43-57`, queue `render`, concurrency 2) runs `renderDesignPreviews` (`service.ts:~342-366`) inside `withTenant`, so a DB transaction stays open across every `imaging.preview()` HTTP call. The scan code (`src/modules/production/floor.ts:453`, router `production/router.ts:111`) doesn't touch previews; any effect is indirect.

## Owned paths (edit)
- `invai-backend/src/modules/catalog/**`
- Grant: `invai-backend/src/integrations/imaging/client.ts` (+ its test), the `preview` method and its error handling only.
- Grant: `invai-backend/src/modules/production/router.ts`, one duration log around the `scan` handler only (no behavior change).
- Grant: a test for the mapping preview copy in `invai-backend/src/modules/orders/` (a new or existing `*.test.ts`, test code only; no product code in orders).

## Read-only paths
- `invai-web/**` (T-P2-1), `invai-floor/**`, `invai-imaging/**`, `src/db/**`, `src/lib/**`, `src/test/**`, every other module.

## Acceptance criteria
0. **Prove the cause first** and put the numbers in the report before the fix lands. On your own stack (API `PORT=3122`, worker and imaging `:8022`, a scratch DB or the dev DB read-mostly, **`REDIS_URL=redis://localhost:6379/12` on every backend command**, `team/agent-brief.md`), with the duration logs from AC4 in place: measure `production.scan` latency (station token from `seed-output.json`, or a seeded item) idle, then while ~40 preview renders drain (enqueue `catalog.renderDesignPreviews` for every design). Report p50/max scan ms both ways, render job ms and imaging ms, and how many DB connections were open (`pg_stat_activity`, `state = 'idle in transaction'`). State plainly: hypothesis confirmed, refuted, or not reproduced. If refuted, still do AC1–AC3 (B-233 debt) and name the next suspect.
1. `renderDesignPreviews` reads the design's files in a short transaction, calls `imaging.preview()` with **no transaction open**, then writes each `preview_key` in its own short transaction, only if the file row still has the same `file_key` it rendered (a replace during the render must not get the old thumbnail). `isCompanyKey` still checks both keys before every call. Idempotency unchanged (same deterministic key, same jobId).
2. Transient imaging failures (connection refused, timeout, 5xx) throw so the job retries with the queue's existing backoff, instead of writing a permanent gray placeholder. The mock placeholder stays for "imaging not configured" (local mock mode; never remove a mock). A 4xx/422 for bad input is permanent and leaves `preview_key` null with a warn log (no placeholder).
3. Tests (each red before the fix where it is a fix): imaging is called with no open transaction (your choice how to prove it, explain); transient error → job throws and no preview written; replace clears the preview (T-P1-4 AC2) and a render that finishes after a replace doesn't write the stale key; mapping copies the design preview to `artworkPreviewKey` (T-P1-4 AC3); tenant check refuses a foreign key (still).
4. Duration logs: `production.scan` logs `durationMs` (info, `companyId`, station id; no PII); the render job logs total `durationMs` and `imagingMs`. One line each, no new log levels.

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint 2>&1 | tail -n 20`; `pnpm test src/modules/catalog src/modules/orders src/modules/production src/integrations/imaging --reporter=dot 2>&1 | tail -n 20` (plain runs isolate their own test DB).
- AC0 numbers from your own stack (record every PID; stop them all before reporting). Never reset the shared dev DB; for a scratch seed follow `team/agent-brief.md` "Scratch seed stacks".
- The floor suite re-run happens at the integration gate, not in this card.

## Out of scope
- Deleting old preview objects on replace, the orders subscriber for late previews, the seed's direct `imaging.preview` call (rest of B-233, backlog). Imaging code (B-232). Floor client timeout. Migrations.

## Budget
- About 3 hours. Stop and tell the tech lead if blocked for 30 minutes.

Commit only your paths in `invai-backend` (`git add <paths>`). Don't push. Report: `invai-docs/waves/P2/reports/T-P2-2.md` (at most 60 lines, `verify-and-report` format, AC0 numbers first, PIDs started and stopped).
