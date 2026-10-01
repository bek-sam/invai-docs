# T-P3-1: Rate-limit buckets by intent, not HTTP method (B-236, High)

| Field | Value |
|---|---|
| Wave | P3 |
| Scope ref | `always-in-scope: bug` (High: a busy floor gets real scans rejected with 429; blocks the P1/P2 gate) |
| Spec | `waves/P2/reports/gate-rootcause.md`; backlog B-236 |
| Owner | backend-foundation |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (opus): the change moves procedures between rate-limit buckets (a security control) |
| Risk flags | auth (rate-limit control), floor-correctness |
| Model | sonnet |
| Depends on | nothing |

## What QA found
`bucketFor` (`invai-backend/src/api/orpc.ts:159-165`) returns `writes` for every non-GET procedure. `files.downloadUrl` is a POST (body param) but a pure read; the floor's `Thumbnail.tsx` calls it once per queue item (92 calls in one floor run), drains the per-company `writes` bucket (120/min, 2/s), and the next real `production.scan` gets HTTP 429. Redis after the run: `tb:writes` 5.79/120, `tb:reads` 299/300.

## Owned paths (edit)
- `invai-backend/src/api/orpc.ts` (`bucketFor` and its doc comment only) and a test next to it (`src/api/*.test.ts`)
- `invai-backend/src/lib/ratelimit.ts` only if a type needs to change (no limit values)

## Read-only paths
- `invai-contracts/**` (no contract change on this card: no new meta field), `invai-floor/**` (T-P3-2 runs in parallel), `invai-web/**`, every `src/modules/**`.

## Acceptance criteria
1. Read-only procedures that are not GET go to the `reads` bucket. Use an explicit, reviewed set (same pattern as `AI_CHEAP_READS`), not a blanket rule. At least `files.downloadUrl` is in it. For every other non-GET procedure whose permission is a read permission (walk the contract with `listProcedures` from `@invai/contracts`), read the handler and decide: side-effect-free read → in the set; anything that writes, enqueues, sends, signs an upload, or calls a paid/outbound service → stays `writes`. List each decision with one reason in the report.
2. **No limit changes.** Capacities and refill rates in `src/lib/ratelimit.ts` are unchanged; no procedure moves from `writes`/`ai`/`auth` to a looser bucket unless AC1's read check put it there. `ai.*` and `auth: "station"` handling is unchanged.
3. A test pins the classification: it walks every procedure in the contract and asserts its bucket; every non-GET procedure with a read permission must be either in the reads set or in an explicit "stays writes" list in the test, so a new POST read fails the test until someone classifies it.
4. Exercised for real on your own stack (API `PORT=3136`, `REDIS_URL=redis://localhost:6379/13` on every backend command; dev DB read-only, no reset): as a floor session (PIN login from `seed-output.json`), call `files.downloadUrl` 150 times, then read Valkey DB 13: `tb:writes:<companyId>` is untouched (absent or full) and `tb:reads` dropped by about 150. Then one `production.scan` (or another real mutation) returns 200, not 429. Flush DB 13 afterwards.
5. A refused case still refuses: draining `reads` (set the key to 0 tokens in DB 13) makes `downloadUrl` return 429 `RATE_LIMITED` with a `Retry-After` header.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 40` in `invai-backend` (run your own test file first, the full suite once at the end).
- The AC4/AC5 curl script and its output (counts, token values) in the report.
- E2E: none on this card; the floor suite runs at the gate.

## Out of scope
- Raising, lowering or splitting any bucket; a new contract meta field (`rateBucket`): if you think one is needed, say so in the report and the architect decides later.
- Floor client changes (T-P3-2).

## Rules
- Role file `.claude/agents/backend-foundation.md`; `team/agent-brief.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-foundation/`.
- Commit only your paths in `invai-backend` (`git add <paths>`), message ends with the attribution line. **Don't push; only the tech lead pushes after the gate.**
- Ports: API :3136 only. Don't touch :3000, :5173, :5174, :8000 (gate slot). Record every PID you start in the report and stop them before reporting.
- Report (≤ 60 lines, `verify-and-report` format) to `invai-docs/waves/P3/reports/T-P3-1.md`; add one progress line there after each milestone.

## Budget
- Escalate to the tech lead if blocked for about 30 minutes of work, or if a fix seems to need a contract change.

## Architect plan review notes (2026-10-01, checked at review)
- Design confirmed: explicit backend reads set, no contract field now (B-240 later).
- Must stay `writes` (read permission, but they write, enqueue or render): alerts.markRead/markAllRead, orders.addNote, digest.feedback/recordClick, market.recommendations.vote, tenancy.org.set, tenancy.today.start/reset/leave, today.dismissChecklist/recordActionClick, analytics.export, finance.exportCsv, personalization.preview. Good `reads` candidates besides files.downloadUrl: inventory.stock, shipping.batchLabelPdf (verify each handler).
