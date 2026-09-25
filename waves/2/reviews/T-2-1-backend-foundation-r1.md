# Review of T-2-1 (round 1)

- Reviewer: backend-foundation on Fable
- Author: backend-engineer (billing) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
Same worktree/setup as the primary reviewer (`5d80c52`, `invai_test_r21`, `node_modules` symlinked).

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` | exit 0 |
| `tsx src/db/migrate.ts` against fresh `invai_test_r21` | "up to date" — `0009_billing_stripe`,
  `0010_billing_webhook_events_system_writes` (plus 0011/0012 from the sibling cards in the parent
  chain) apply cleanly from empty |
| `./node_modules/.bin/vitest run src/db/rls-coverage.test.ts` | 6/7 passed; the 1 failure
  (`two_factors`) traces to T-2-3's `6ff0890`, a parent commit not owned by this card. `SELECT * FROM
  pg_policies WHERE tablename = 'billing_webhook_events'` on `invai_test_r21` confirms the
  `billing_webhook_events_tenant` policy exists and RLS is enabled — this card's own table passes
  coverage |
| `docker exec ... psql -d invai_test_r21 -c "\d billing_webhook_events"` | unique index on
  `stripe_event_id`, FK to `companies(id)` `ON DELETE CASCADE`, indexes on `received_at` and
  `(company_id, received_at)` — leads with `company_id` per convention |
| `./node_modules/.bin/vitest run src/modules/billing` | 31/31 passed |

## Migration review (`fadfa26`, drizzle 0009/0010)
- **Schema conventions:** `billing_webhook_events` is `snake_case`, has `companyId` (nullable, by
  design — an event that names no InvAI company), `tenantPolicy("billing_webhook_events")`, and
  `.enableRLS()`. This exactly follows decision 0009's `webhook_deliveries` shape, which the card and
  the architect's plan review both call for, and correctly does **not** reuse `webhook_deliveries`
  itself (that table's `channel` column is a `CHANNELS`-enum check constraint; adding `stripe` there
  would have forced `stripe` handling into every marketplace-channel switch — the exact class of
  breakage `add-tenant-table`/exhaustive-switch discipline exists to prevent). New, dedicated table is
  the right call.
- **System-only writes:** migration 0010 does one targeted `REVOKE INSERT, UPDATE, DELETE ON
  billing_webhook_events FROM invai_app`, with a one-line comment stating why (no request path — bug
  or otherwise — can pre-claim or suppress a Stripe event id). Matches decision 0009's pattern exactly.
  Verified live in `stripe.test.ts`: an `invai_app`-role insert attempt `rejects.toThrow()`.
- **Indexes:** unique on `stripe_event_id` (the dedupe key), plus `(company_id, received_at)` leading
  with `company_id` — correct per the tenant-table convention, and useful for the nightly purge query
  and any future "this company's billing events" read.
- **No hand-edited migration.** `0009`/`0010` are additive-only (`ALTER TABLE ADD COLUMN`,
  `CREATE TABLE`, `REVOKE`) — no `DROP`/rewrite of an already-applied migration. Zero-downtime shape is
  fine for a brand-new table and additive columns (`cancel_at_period_end` with a `DEFAULT false NOT
  NULL`, `stripe_event_at` nullable) — no backfill needed, no `lock_timeout` concern beyond the
  standard `ADD COLUMN ... DEFAULT` fast-path Postgres already handles.
- **`SUBSCRIPTION_STATUSES` gains `trial_expired` with no migration.** Confirmed `enumText()`
  (`db/schema/_shared.ts:66`) is TS-only typing on a `text()` column — no Postgres `CHECK` constraint
  exists for this enum, so the claim that no migration is needed for a new status value is correct
  (verified by reading `_shared.ts` directly, not taking the report's word for it).
- **Migration journal:** `_journal.json` only gained 0009 and 0010 from this card's commits; no
  collision with T-2-3's/T-2-5's later entries (0011/0012) — sequential, no hand-editing of an entry
  another card had already committed.

## Patterns followed
- `db` client conventions: `withSystem` used only where there's no tenant session (the webhook has no
  request-scoped company yet when the event arrives) or the work is cross-tenant (`expireTrials`,
  `ensurePlanCatalog`, the purge job) — each with a code comment, matching the "MUST NOT use
  `withSystem` in a request path without a written reason" rule. `checkout`/`portal`/`changePlan`
  correctly use `withTenant(ctx.companyId, ...)`.
- `assertWithinPlan`'s three call sites added by this card (`tenancy/service.ts` invite,
  `channels/service.ts` connect ×2) are minimal, single-purpose hunks inside functions this card was
  granted, not rewrites of surrounding logic.
- Jobs: `expireTrialsJob`/`purgeBillingWebhookEventsJob` go through `defineJob`/`queues.reports`,
  scheduled via `upsertJobScheduler` (idempotent registration), consistent with the existing job
  patterns elsewhere in the codebase.

## Acceptance criteria (migration-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| 2 webhook dedupe table | Yes | New `billing_webhook_events`, correct RLS/system-write shape, verified live |
| Trial expiry schema | Yes | `trial_expired` added to a TS-only enum, no migration needed, confirmed by reading `_shared.ts` |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`db/schema/billing.ts` + its migration only touched by schema changes)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scan found no weakening
- [x] Tenancy (`company_id` + RLS + leading index on the new table; `withSystem` reasoned everywhere
      it's used), idempotency, money in cents, migrations additive/non-destructive
- [x] Decisions recorded where needed (architect's plan review documents the
      `webhook_deliveries`-vs-own-table decision)

## Optional notes (not blocking)
- `billing_webhook_events.companyId` has no index-leading requirement issue since it's nullable by
  design, but a future query that scans "all unresolved events" (`company_id IS NULL`) would want to
  confirm the partial-null case is cheap under the current `(company_id, received_at)` index — fine at
  today's volume, worth remembering if event volume grows.
