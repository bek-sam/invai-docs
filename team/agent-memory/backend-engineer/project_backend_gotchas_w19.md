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
