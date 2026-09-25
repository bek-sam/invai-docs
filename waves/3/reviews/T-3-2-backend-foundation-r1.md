# Review of T-3-2 (round 1)

- Reviewer: backend-foundation on Fable
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Scope of this co-review
Migration `0013_carriers_webhook_events`, the new schema file `db/schema/carriers.ts`, the one-line export in `db/schema/index.ts`, and the two-line `env.ts` grant (`EASYPOST_WEBHOOK_SECRET`) — the areas that are normally mine.

## Evidence I re-ran

| Command | Result |
|---|---|
| `tsc --noEmit`, `biome check .` (worktree @ `b648cfd`) | clean |
| `vitest run` (`invai_test_r32`) | 53 files, 380 tests passed |
| `tsx src/db/migrate.ts` against a fresh copy (`invai_r32_copy`, `createdb -T invai`) | applied `0013_carriers_webhook_events` cleanly on top of the live dev DB's current state (which was one migration behind — see the reviewer's file, not a defect here) |
| `\dp carrier_webhook_events` | `invai=arwdDxtm/invai` + `invai_app=r/invai` — matches `webhook_deliveries`'s grants (migration 0007) exactly |
| `psql ... "select 1 from information_schema.table_constraints where table_name='carrier_webhook_events'"` (read) | unique `(provider, event_id)`, RLS policy present, FK to `companies.id` cascade |

## `env.ts`
```diff
+    /** EasyPost webhook HMAC secret (`X-Hmac-Signature`); unset uses the mock dev secret. */
+    EASYPOST_WEBHOOK_SECRET: secret(z.string()),
```
Correct use of the `secret()` helper (trims, blank-counts-as-unset). Not added to `PRODUCTION_KEYS` — the author flagged this explicitly as an open decision for me. **My call:** leave it out of `PRODUCTION_KEYS` for now. Making it required would hard-block production boot for any shop before the owner configures a real EasyPost webhook, and the daily poll (`shipping.trackerPollSweep`) covers tracking without it, just less promptly (up to 3 days late instead of real-time). I'll track "decide before the owner's first real EasyPost run" as a follow-up rather than a blocking change here — consistent with the wave doc's own open item.

## `db/schema/index.ts`
```diff
 export * from "./billing";
+export * from "./carriers";
 export * from "./catalog";
```
This is my path, not on T-3-2's owned-path list. I'm approving it: it's the same one-line, alphabetically-placed export every module's schema file needs (`drizzle.config.ts` only reads `index.ts`), it's mechanical, it was transparently reported ("Blocked by other owners" section of the report), and T-3-1's own commit in this same wave (`5a89ba8`) did the identical thing for its own new schema file. I'd rather this pattern be explicit than have every module owner either ask permission for a one-line export or work around it — I'll add a line to `src/modules/README.md` making this an allowed exception (new schema file → its own index export, same commit) so future cards don't have to re-litigate it.

## `carriers.ts` / migration 0013 — decision 0009 conformance
Checked line by line against `webhook_deliveries` (migration 0007, decision 0009):
- nullable `company_id`, set once routed — ✓, `companyId: uuid().references(() => companies.id, { onDelete: "cascade" })`, no `.notNull()`
- `tenantPolicy("carrier_webhook_events")` + `.enableRLS()` — ✓
- unique on `(provider, event_id)` — ✓ `uniqueIndex().on(t.provider, t.eventId)`
- `REVOKE INSERT, UPDATE, DELETE ON carrier_webhook_events FROM invai_app` in the migration, with the same comment style as 0007's — ✓, verified live above
- retention purge — ✓, 7 days (`CARRIER_WEBHOOK_EVENT_RETENTION_MS`), a daily job (`purgeCarrierWebhookEventsJob`, scheduled `55 4 * * *`), same shape as `purgeWebhookDeliveries`

**The two extra columns (`subject_id`, `occurred_at`) — my sign-off as backend-foundation (the report asked both me and the architect to confirm):** I looked for whether this belongs on `shipments` instead (a `channelUpdatedAt`-style column, which is literally what backlog item B-12 calls for generically). It would be architecturally cleaner long-term, but `shipments` is `service.ts`'s and this card is explicitly read-only there. Storing the carrier's last-applied scan time on the *event* table, keyed by `(provider, subject_id)`, is a reasonable place for it given that constraint: it's additive to a table this card already owns, doesn't touch RLS or the REVOKE (both unchanged from 0009's shape), and the composite index (`provider, subject_id, occurred_at`) is properly `company_id`-adjacent for the lookups that need it (the "newer event" check runs after the shipment's `company_id` is already known, under its row lock — it doesn't need to be `company_id`-led itself). I'd want B-12's general `channelUpdatedAt` column done on `shipments` eventually so other channels get the same guarantee without a side table, but that's a reasonable follow-up, not a blocker on this card.

One thing I checked closely because it's exactly my kind of bug: `finishCarrierEvent` (which writes to `carrier_webhook_events`) uses `withSystem`, which opens its own connection/transaction, called *from inside* the `withTenant` transaction in `processCarrierEvent` that applies the shipment state change. This is unavoidable — `invai_app` (the role `withTenant` connects as) has no write grant on this table by design — but it means the dedupe/audit record can commit independently of, and before, the state change it describes. I traced the crash-window scenario (process death between the two commits) and agree with the reviewer's file: it self-heals on BullMQ retry (5 attempts, exponential backoff) and the worst case is a *correctly* dropped stale event, never a wrong or backward state. Still, this is a pattern other system-only tables will hit too (`webhook_deliveries` already has the same shape), so I'll add a paragraph to `src/modules/README.md` documenting it rather than treating it as new.

## Checks
- [x] Migration reviewed and safe: additive table, no lock on existing tables, `CREATE TABLE` + `ENABLE ROW LEVEL SECURITY` + indexes + one `REVOKE` — no `zero-downtime-migration` expand/contract concerns since nothing existing changes.
- [x] `company_id` + RLS + a `company_id`-leading index present (`(company_id, received_at)`) alongside the dedupe and lookup indexes.
- [x] `pnpm test src/db/rls-coverage.test.ts src/api/authz.test.ts` green (also re-run above).
- [x] `.env.example` — checked, not touched by this diff; confirmed `EASYPOST_WEBHOOK_SECRET` doesn't need an entry there since it's optional and commented-out entries follow the same convention as other optional secrets (e.g. `SHOPIFY_API_SECRET`). Minor: could add a commented line for discoverability, not blocking.
