# Review: T-A9 (security co-review, round 1)
Reviewer: security-reviewer on Sonnet 5. Author: backend-engineer on Opus (commit `522433b`, not pushed).

## Verdict: approve

## Scope of this review
Tenancy, auth, PII focus only, per dispatch (decision 0019: re-run only affected tests). Did not re-review
money-calculation correctness (D9–D13 thresholds) or the A1 tiebreak — that is `reviewer`'s primary scope.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm test src/modules/today` | 2 files, 16 passed |
| `pnpm test src/modules/digest/track-e.test.ts` (part of digest suite) | passed |
| `pnpm test src/api/authz.test.ts` (alone) | 7 passed |
| `pnpm test src/api` (batched with `today`) | 1 file failed on `companies_slug_unique` collision in `createCompany` (fixtures.ts, parallel workers) — pre-existing test-isolation flake, unrelated to this diff (fixtures.ts not touched); `authz.test.ts` passes alone |
| `pnpm test src/db` (rls.test.ts, rls-coverage.test.ts, fk coverage) | 11 files, 33 passed |

Read (no code edits): `db/schema/digest.ts` (today tables), `today/actions.ts`, `today/router.ts`,
`today/jobs.ts`, `digest/track-e.ts`, `digest/snapshot.ts`, `digest/detectors.ts` (D9–D13),
`invai-contracts/src/schemas/digest.ts` (`DigestActionParams`, href regex — unchanged, T-A10).

## Findings
None blocking.

## Checklist
- **withTenant for today.actions / recordActionClick**: both handlers in `today/router.ts` wrap
  `actions.getTodayActions` / `actions.recordActionClick` in `withTenant(tenant.companyId, ...)`. Confirmed.
- **finance.read enforced, role matrix**: contract `today.ts:35,44` marks both procedures `finance.read`.
  `actions.test.ts:286-305` calls the real `router.today.actions`/`recordActionClick` (not the bare service)
  as designer, presser, packer, receiver, and a vendor org — all `FORBIDDEN`. Ran and passed.
- **Cross-company action key can't be referenced**: `recordActionClick` (`actions.ts:255-267`) looks up the
  action by `(companyId, date, key)` under the tenant's own `tx`; a miss throws `ACTION_NOT_FOUND` (404), never
  `FORBIDDEN` or a leak. `actions.test.ts:237-284` (AC-E4) proves company B: sees no A actions/clicks on read,
  gets `ACTION_NOT_FOUND` clicking A's key, a raw RLS read of A's rows returns `[]`, a raw insert under B
  pointing at A's `companyId` fails RLS, and a click row for B referencing A's action id fails the composite
  FK (`23503`) even bypassing RLS via `withSystem`. All passed.
- **withSystem confined to the sweep/purge, scoped per company**: `jobs.ts` `shopsMissingToday` (sweep) reads
  only `company.id` + local date via `withSystem`, no financial or PII columns, then enqueues one
  `buildTodayActionsJob` per company which runs `buildTodayActions` under `withTenant`. `purgeTodayActions`
  is a single age-based `DELETE` via `withSystem` — no per-row company scoping needed since it deletes by
  `date` only and cascades; contains no buyer data (dates, keys, integer cents). Matches the existing
  `orders/jobs.ts` purge pattern. The one other `systemContext()` use (`track-e.ts` `getBlank` call) doesn't
  cross tenants: it runs on the same tenant-scoped `tx` (RLS still applies), `getBlank` ignores the ctx
  argument entirely — not a real privilege elevation.
- **No buyer PII in params/copy/logs**: `DigestActionParams` (contract, unchanged) only accepts channel,
  design/blank/supplier ids and names, style/color/size, points, deltaCents, n — no name/email/address/note
  field exists on the schema. `track-e.test.ts:441-462` asserts every D9–D13/D2 candidate's params key set is
  a subset of that allowlist and schema-valid. `render.ts` en/es copy has no buyer-field references (grepped).
  Logs (`actions.ts` `log.info`, `snapshot.ts` `log.warn`) carry only `companyId`, `date`, counts and
  `err.message`/stack — consistent with the existing `errorData()` helper used elsewhere.
- **href stays an internal path**: contract regex `/^\/(?!\/)[^\\\s]*$/` (unchanged) enforced on output; every
  D9–D13/D2 href literal starts with `/analytics/...` or `/inventory` and is asserted by the same allowlist
  test.
- **RLS/FK on new tables**: `today_action_sets`, `today_actions`, `today_action_clicks` all have
  `tenantPolicy()` + `.enableRLS()`, composite `(company_id, id)` unique indexes on parents and composite FKs
  from children (schema read, migration `0038_today_actions.sql` inspected: `ENABLE ROW LEVEL SECURITY` +
  tenant policy present for all three). `rls-coverage.test.ts` and `fk` coverage green.
- **Idempotent click**: `recordActionClick` inserts with `onConflictDoNothing` on
  `(companyId, actionId, userId)`, then reads back — first click wins, same `clickedAt` on repeat (per report,
  and covered by `actions.test.ts`).

## Notes (non-blocking)
- `src/api/authz.test.ts` + `src/modules/today` run together in one vitest invocation hit a pre-existing
  fixture flake (`createCompany` random slug collision across parallel workers) unrelated to this card's
  files. Flagging for whoever owns `src/test/fixtures.ts` test-isolation, not a T-A9 regression.

## Decision
Approve on tenancy/auth/PII grounds. No High/Medium findings. Nothing added to `security/v1-review.md`.
