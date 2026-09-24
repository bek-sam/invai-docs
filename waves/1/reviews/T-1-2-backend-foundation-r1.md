# Review of T-1-2 (round 1)

- Reviewer: backend-foundation on Fable
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

Co-review scope: the new `webhook_deliveries` table and migrations 0006/0007 (mandatory backend-foundation
co-review for any new table or migration), plus a general pass over `withTenant`/`withSystem` usage in the
touched files. Commit reviewed: `90657ac` only, in a clean worktree at that commit (parent `34ed022`). Own
test DB `invai_test_r12`, own Redis DB 12, API/worker on port 3192. Worktree, DB and Redis DB removed
afterward; no processes left running.

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit && biome check . && vitest run` (clean worktree, `invai_test_r12`) | typecheck clean; `Checked 191 files … No fixes applied`; `184 passed (184)` |
| `tsup` | `Build success` |
| `tsx src/db/migrate.ts` against a **freshly created** `invai_test_r12` (drop/create, no prior state) | `[migrate] up to date` — 0006 and 0007 apply cleanly on an empty DB, in order, no manual intervention |
| Read `drizzle/0006_webhooks_deliveries.sql`, `0007_webhooks_deliveries_system_writes.sql`, and `drizzle/meta/_journal.json` | see "Migration review" below |
| `pnpm test src/db/rls-coverage.test.ts src/api/authz.test.ts` (part of the full run above) | green; the new table needed no exemption from the coverage test because it carries `company_id` + a real tenant policy |
| Live: `INSERT` into `webhook_deliveries` as `invai_app` | `permission denied for table webhook_deliveries` — migration 0007's revoke is in effect |
| Live: `withSystem` write path exercised end-to-end (webhook → insert → worker updates status) | delivery row went `received` → `processed` with `company_id` filled in by the worker, exactly as designed |

## Migration review (0006, 0007)
- **0006** (`drizzle-kit generate`d): `CREATE TABLE webhook_deliveries` with `id`, nullable `company_id` (FK to
  `companies.id ON DELETE CASCADE`), `channel`, `delivery_id`, `status` (`default 'received'`), `received_at`
  (`default now()`), `processed_at`, `detail`; a unique btree index on `(channel, delivery_id)`; two more
  indexes (`received_at`, `(company_id, received_at)`) for the purge and per-shop health reads; RLS enabled;
  the tenant policy created. This is a **pure `CREATE TABLE`** — it touches no existing table, needs no lock on
  anything else, and has no backfill step. Zero-downtime by construction; there's nothing to sequence across
  deploys here (`zero-downtime-migration` is about *changing* live tables, and there is no existing table being
  changed).
- **0007** (hand-written `--custom`, per `add-tenant-table`'s pattern for `plans`/`trademark_marks`): a single
  `REVOKE INSERT, UPDATE, DELETE ON webhook_deliveries FROM invai_app`. No data movement, effectively
  instantaneous, no lock contention with running queries (a `REVOKE` doesn't need to wait for readers).
- **Reversibility:** both are safely reversible if ever needed — 0007 by re-`GRANT`ing (trivial, no data
  impact), 0006 by `DROP TABLE` (the table holds no data any other table depends on; the FK is *from*
  `webhook_deliveries` to `companies`, not the other way, so dropping it cannot cascade into anything else).
  Neither migration hand-edits a prior migration, and the journal (`meta/_journal.json`) only appends entries
  6–7, matching the "generated, then one custom SQL file" pattern used elsewhere (`plans`).
- **No journal collision:** the author's report notes T-1-3 generated entry 8 on top of this snapshot with no
  conflict; I confirmed entry 8 is absent from this commit's journal (it belongs to T-1-3's own commit), so
  `90657ac` is self-contained and applies cleanly on its own, which I verified by migrating a completely fresh
  database with only this commit's migrations.

**Verdict on 0006/0007: correct and reversible-safe.** No concerns.

## Tenancy design of `webhook_deliveries`
Nullable `company_id` + `tenantPolicy()` + `.enableRLS()` + revoked app-role writes, all writes via
`withSystem`. This is a deliberate departure from the architect's round-1 recommendation (a plain global
table with no `company_id`/RLS at all), made because `rls-coverage.test.ts` — which backend-foundation does
not own but whose invariant ("every `company_id` table has RLS, no exceptions") I care about protecting —
would otherwise have needed a carve-out mid-wave, touching another role's owned file.

Judging it on the merits against `add-tenant-table` and the patterns I maintain:
- `company_id` present, `tenantPolicy()` applied, `.enableRLS()` set, index leads with `company_id`
  (`(company_id, received_at)`) — matches the standard shape exactly.
- The one real deviation from a normal tenant table is that `company_id` is nullable and the app role has no
  write grant at all (normal tenant tables are written by request code under `withTenant`; this one is written
  only by `withSystem`, like the outbox relay or the seed). That's an unusual combination, but it's the
  correct one for data that exists *before* a tenant is known (webhooks arrive pre-auth) — it's the same shape
  problem the outbox and cross-tenant jobs already have, just applied to a table instead of a relay.
- I don't see a cleaner alternative that satisfies both "no coverage-test carve-out" and "no cross-tenant
  suppression attack surface" at once. The global-table alternative the architect proposed is also fine in the
  abstract, but would require touching `rls-coverage.test.ts` (security-reviewer's file) to add an allowance
  list — more cross-cutting than what was actually needed here.
- This should still be written up as a real `decisions/` entry, not just left in the task report — it's
  exactly the kind of "which shape does a pre-tenant table take" call that later module engineers will want a
  citable answer for instead of re-deriving it. Not blocking this round.

## `withSystem` usage audit (this commit only)
`grep -n "withSystem(" src/modules/channels/sync.ts`: `recordWebhookDelivery`, `forgetWebhookDelivery`,
`finishWebhookDelivery`, `purgeWebhookDeliveries`, the shop lookup in `handleWebhook`, and both steps of the
OAuth state consume/complete. Every one of these is either (a) writing/reading `webhook_deliveries` before any
tenant is known, (b) a cross-tenant lookup by shop id to find which company a webhook belongs to, or (c) the
OAuth pending-connection scan, which by definition runs before the connection is tied to a session — all
squarely inside the allowed uses (`outbox relay, cross-tenant jobs and the seed` plus the established
vendor/billing pattern). No new `withSystem` call in this commit lacks a reason, and each sits right next to
the comment explaining it. `withTenant` is used correctly for the tenant-scoped part of `handleWebhook` (the
actual order import, once a connection is matched).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 3. Persisted table, unique per channel+id, ≥30h retention + purge, replay → 200 no-op, tenancy explained | yes | see migration review and tenancy design above; purge tests pass (7-day retention, well past the "≥30h" floor) |
| (1, 2, 4, 5 are outside this co-review's focus; see `reviewer` and `security-reviewer`'s files — I independently reproduced the pass/fail results for all five during evidence gathering and found no discrepancy) | yes | |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (this commit doesn't touch any backend-foundation-owned path directly, which is
  correct — the card explicitly grants the author `modules/channels/sync.ts` and `jobs.ts` for the named
  functions only, per the architect's round-1 fix; I confirmed the diff doesn't spill into `src/db/client.ts`,
  `src/env.ts`, or any other backend-foundation file)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened (see `reviewer`'s scan-tool output, correctly scoped to
  `34ed022..90657ac`)
- [x] Tenancy: `company_id` + tenant policy + RLS + index leading with `company_id`, `rls-coverage.test.ts`
  green, every `withSystem` call justified
- [x] Idempotency: unique-index dedupe verified live under real concurrency; the purge is safe to run daily
  and re-run (delete-only, no state to corrupt)
- [x] Decisions recorded — see the note above; recommend a formal `decisions/` entry before wave 2

## Optional notes (not blocking)
1. Same as the other two reviews: record the `webhook_deliveries` tenancy-shape choice in
   `invai-docs/decisions/` so it's citable precedent rather than only living in this task's report.
2. Worth a cheap follow-up (flagged by security-reviewer too): `forgetWebhookDelivery` assumes an
   `enqueue()` rejection means nothing was queued. A future hardening pass could check the job's actual
   presence in Redis before deleting the delivery row, closing the narrow window where a delivery row can be
   left permanently stuck at `received`.
