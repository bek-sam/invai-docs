---
name: backend-gotchas-w19
description: Non-obvious invai-backend traps found on T-19-3 (drizzle composite FK order, finance net/margin units, frozen test clocks vs DB now()).
metadata:
  type: project
---

- 2026-09-27 T-19-3: drizzle-kit 0.31 emits composite `foreignKey()` constraints BEFORE the `uniqueIndex()` they reference, so the migration fails. Make FK-target keys `unique("name").on(...)` (inline in CREATE TABLE).
  **Why:** caught by reading the generated SQL; nothing else would have flagged it until migrate.
  **How to apply:** any new tenant table with S-26 composite FKs; always read the generated SQL order.
- 2026-09-27 T-19-3: finance `getProfit` net = revenue minus cost buckets (ignores `profit_lines.net_cents`); its `marginPct` is a 0..1 ratio despite the name. Assert against `getProfit`, not fixture cents.
- 2026-09-27 T-19-3: `vi.useFakeTimers({toFake:["Date"]})` doesn't move Postgres `now()`; time-dependent queries (overdue, schedules) must take an explicit `at` param. The shared dev DB may get your uncommitted migration applied by another agent's `db:migrate` (shared tree): don't regenerate a migration after it exists on disk for long.
- 2026-09-28 T-19-3 round 2: backend `render.ts` email templates and web's copy files (e.g. `recommendation-copy.ts`) independently hardcode the same market-rule wording (R1..R5) with no shared source. A `value || fallback` where both sides can be empty string ("") silently renders a blank placeholder. When fixing one side's empty-placeholder bug, grep the other side (web, read-only) for the same rule's fallback text and copy it verbatim (including the Spanish, found in `invai-web/src/i18n/es.ts`) instead of inventing new wording.
- 2026-09-28 T-20-1: `createdb -T invai` fails while the shared API holds a session; copy the dev DB with `docker exec local-postgres-1 sh -c 'pg_dump -U invai invai | psql -q -U invai <copy>'` (grants come along). Market recompute won't replace same-day R1 rows (dedupe), so delete them in your copy to see new rule output.
- 2026-09-28 T-20-1: `es-US` formats "6.9" and "27 sept"; approved Spanish copy wants "+6,9 pts" (locale `es`) and "27 sep" (`es-MX`). R1 "peak under way" = `peakMonth` set and `actByDate` absent; web `recommendation-copy.ts` doesn't know that yet.
- 2026-09-29 T-22-4: since T-22-2's composite FKs, any insert carrying a client-sent id of another tenant's row (e.g. `scans.station_id` from ScanInput) fails as a raw FK violation (500). Check the id under `withTenant` first and throw `notFound` (done in `production/floor.ts scan()`); grep other client-id inserts for the same.
- 2026-09-29 T-22-4: the shared dev DB gets a newly committed migration applied by other agents' `db:migrate` within minutes; a pg_dump copy then says "up to date". Seed floor units mostly sit on `sent` sheets with no printed/received time (transfer age null in demo).
- 2026-09-29 T-22-4: full `pnpm test` in a shared tree can fail on another card's half-edited files (T-22-5 `fees.test.ts`); check `git status` for foreign modified paths before blaming your change.
- 2026-09-29 T-22-5: killing a `tsx`/`tsx watch` PID (esp. `kill -9`) orphans the node child, which keeps consuming jobs; start exercise processes with `node --import tsx src/...` so `$!` is the real PID, and check `lsof -nP -R -iTCP:6379` for PPID 1 leftovers.
- 2026-09-29 T-22-5: the agent scratchpad dir is shared by all agents in the session; put your files in a per-card subdir. `emit()` accepts internal (non-contract) event names; precedent `sheet.regenerate_requested`.
- 2026-09-29 T-22-5: SMTP has no read-back, so vendor sheet delivery is at-most-once for an uncertain attempt (`vendor_sheet_deliveries` status `unknown`); don't "fix" it into auto-resend.
- 2026-09-29 T-22-5 r2: the Today 5-min sweep (`today/service.ts` resolveStale) auto-resolves any open alert of kinds order_at_risk/order_overdue/sync_broken/sheet_stuck/stock_low/plan_limit_reached whose dedupe key it didn't raise; a module's own alert must use a non-swept kind (precedent `tracking_push_failed`). Any "outcome unknown/failed" state must raise an alert or it's a silent loss.
- 2026-09-29 T-22-5 r2: prove a lock/guard with a mutation run (remove it, test must go red); ON CONFLICT alone keeps "parallel create" tests green, so lock tests need a gated same-key update race.
- 2026-09-30 T-A3: the oRPC router's parsed `CostSettingsInput` (`.partial()`) carries EVERY key, undefined ones included; a service test calling with `{onlyKey}` hides it. Guard on values (`v !== undefined`), not `Object.keys`, and add a router-level `call()` test for "only X changed" logic.
- 2026-09-30 T-A3: metric SQL parity tests can run the data-analyst's `invai-docs/metrics/sql/*.sql` as written (replace `:'var'`, filter rows by the test company's slug via `withSystem`); see `analytics/finance-testkit.ts runMetricSql`.
