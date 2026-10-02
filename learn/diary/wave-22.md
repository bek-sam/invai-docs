# Wave 22 — P2 sweep, part 1: contracts and backend correctness

**Dates:** 2026-09-29.

## What was built
- **T-22-1** Contract additions for the P2 sweep (architect): additive-only contract
  changes for every backend gap this wave closes.
- **T-22-2** Tenant FKs, migrate lock, queue stall settings, trigram indexes
  (backend-foundation): foreign keys that can't cross tenant boundaries even by accident,
  a migrate lock, and search performance work.
- **T-22-3** USPS end-of-day SCAN form, address check, rate TTL; Amazon CSV shipping;
  mailer subject log (integrations-engineer): real carrier workflow details, and shipping
  credits from Amazon's CSV now flow into profit.
- **T-22-4** Production and inventory: QC fail reasons, transfer-age warning, maintenance
  block, bin locations in the pick list (backend-engineer/production, inventory): the
  backend half of floor-correctness features whose screens land in wave 23.
- **T-22-5** Orders and vendors: import races, channel line edits, vendor email after
  commit + resend, TikTok fee, listing attributes (backend-engineer/orders, vendors,
  finance): imports can't double-create under concurrent runs, and vendor emails go out
  exactly once, after the commit, with a resend path.

## Why
"P2" means these are correctness gaps below the golden path's headline features but still
real bugs a shop would hit — a double-imported order, a vendor email that never arrives
because it was sent before the transaction committed (and then rolled back), a tenant
foreign key that could technically point at another shop's row. This wave closes the
backend half; wave 23 builds the screens.

## What went wrong
- A planned fix — tenant-leading trigram indexes to speed up search under RLS — turned
  out not to work: `EXPLAIN` run *as the `invai_app` role* showed the planner never used
  them, because RLS policies are security barriers and `LIKE`/`ILIKE`/similarity aren't
  leakproof operators, something nobody had checked before building the index.
- A relaunched T-22-2 builder found an earlier instance of itself that the tech lead had
  assumed was stalled, but was actually still running — it committed, edited the report,
  and ran tests on the *same* test DB and Redis DB as the still-alive instance, causing
  deadlocks and collisions.
- BullMQ tests had been failing intermittently in full backend runs since wave 20 and
  were being written off as flakes, until this wave root-caused it: the test environment
  redirects Postgres to `invai_test` but leaves `REDIS_URL` on Redis DB 0 — the same
  database any currently-running dev worker uses.
- Three gate attempts and two builder instances died with no progress for 600 seconds
  while seeds, full suites and E2E ran in the foreground — the agent runtime kills an
  agent after 10 minutes of no output, and gate steps (a 15–20 minute seed, 5+ minute
  suites) had been run as single foreground commands that couldn't produce output in time.

## What the team learned
- Any index meant for the app role gets proven with `EXPLAIN` as `invai_app` under
  `withTenant` before it ships — only leakproof operators (`=`, `starts_with`) can be
  index conditions under RLS. Now a standing rule in `src/modules/README.md`.
- Before relaunching a card believed stalled, check `git log` and report file modification
  times from the last 15 minutes, plus `ps` for live `vitest`/`tsx` processes — a
  relaunch uses new DB and Redis names (an `r2` suffix) regardless.
- Anything that might take more than 3 minutes runs in the background and gets polled,
  never as a single foreground wait longer than 5 minutes — this directly shapes
  `run-golden-path` and `verify-and-report` from here on.
- A "flake" gets root-caused before it's called one — this exact BullMQ/Redis case is the
  clearest example in the project's history of a real bug hiding behind that label for
  two whole waves.

## Files to look at
- `invai-backend/src/db/schema/*.ts` (FK constraints), `src/db/migrate.ts` — T-22-2.
- `invai-backend/src/integrations/carriers/`, `channels/csv/` — USPS SCAN form, Amazon
  shipping credits (T-22-3).
- `invai-backend/src/modules/{production,inventory}/service.ts` — T-22-4.
- `invai-backend/src/modules/{orders,vendors,finance}/service.ts` — import races, vendor
  resend (T-22-5).
- `invai-docs/team/lessons.md` (2026-09-29, "T-22-2" and "wave 22" rows, 4 of them).
