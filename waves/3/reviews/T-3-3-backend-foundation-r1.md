# Review of T-3-3 (round 1)

- Reviewer: backend-foundation on Fable (co-review)
- Author: backend-engineer (inventory) on Opus 5.5
- Verdict: approve

Scope of this co-review: the out-of-owned-paths seed hunk in `src/db/seed/index.ts`, plus my
usual lens on tenancy, RLS, migrations and the seed's realism/timing rules. The reviewer's file
(`T-3-3-reviewer-r1.md`) carries the full re-run of tsc/biome/vitest/build and the live push
exercise; I re-ran the pieces relevant to my flag and read the rest of the diff to confirm.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show --stat b8ac9d0` in `invai-backend-r33` (worktree at the commit) | 7 files, all inside the card's owned globs except the 5-line seed hunk, which the author self-flagged for me |
| `git show b8ac9d0 -- src/db/seed/index.ts` | the only production-code change outside `modules/{channels,inventory}` |
| `grep -n "recordListingsForCompany\|withSystem" src/db/seed/index.ts` | one import, one call: `const listingReport = await withSystem((tx) => recordListingsForCompany(tx, shopId), shopId);` right after the shop's orders are seeded, before ad-spend/alerts |
| `grep -rn "emit(" src/modules/channels/sku.ts` around `recordListingsForCompany`/`upsertListings` | **no `emit` call** in the backfill path — it's a pure DB upsert, unlike `recordListingsForItems` (called only from the `recordListingsJob` handler, which does emit `stock.availability_changed`) |
| `node_modules/.bin/tsc --noEmit -p .` in `invai-backend-r33` (same worktree/commit the primary reviewer set up; I read and re-checked rather than standing up a second copy) | clean |
| `TEST_DATABASE_URL=…invai_test_r33 node_modules/.bin/tsx src/db/migrate.ts` (shared with the primary reviewer's run) | `[migrate] up to date` — no new migration shipped, matches the card's schema note (`listings`/`listing_variants` already had `companyId` + `tenantPolicy` + RLS from an earlier wave) |
| `REDIS_URL=redis://localhost:6379/12 node_modules/.bin/vitest run src/modules/channels/listings.test.ts src/modules/inventory/availability.test.ts` (subset of the same 431-test run) | both files: all tests pass |
| `grep -n "B-106" invai-docs/waves/backlog.md` | B-106 is "seed collides with a running worker (`stock_levels` unique)" — a pre-existing, unrelated bug about `stock_levels`, not about `listings`/`listing_variants` |

## Is the seed hunk safe, and does it collide with the worker (B-106)?
No collision, for two independent reasons:
1. **It writes different tables than B-106.** B-106 is a unique-constraint race on `stock_levels`
   between the seed's own inserts and a live worker's inventory jobs. This hunk's only write is
   `recordListingsForCompany` → `listings`/`listing_variants`, via `ON CONFLICT DO UPDATE` on the
   exact unique indexes those tables already carry
   (`(companyId, connectionId, channelListingId)` and `(companyId, listingId, channelVariantId)`
   — checked against `db/schema/channels.ts:86-135`). An upsert against those keys cannot throw a
   unique violation the way a plain insert into `stock_levels` can; at worst a concurrent writer
   would just overwrite the same row again, which `upsertListings`'s `coalesce()`-based merge
   already tolerates by design (see its own test, "is idempotent: replaying the events and a
   second order add no rows").
2. **It can't be triggered by, or trigger, the worker at all.** The seed's order/order-item
   inserts (existing code, unchanged by this commit) go straight into the DB — I grepped the seed
   file for `emit(` and it never fires `order.imported` or `item.mapped`, so the worker's
   `recordListingsJob` never runs during a seed. And `recordListingsForCompany` itself doesn't
   call `emit` either, so the seed's backfill can't wake up `scheduleAvailabilitySync` or any
   other job. The seed's listings backfill is a self-contained, synchronous, idempotent read-then-upsert
   that shares no table and no queue path with a running worker.

The runbook's existing "worker stopped during seed" rule (B-106) still applies to the
`stock_levels` issue it was written for; this hunk doesn't add a new reason to need it, and
doesn't remove the existing one either.

## Acceptance criteria (my lens only)
| # | Met? | Evidence |
|---|---|---|
| 1 (seed creates listings) | Yes | Seed hunk calls the same `recordListingsForCompany` covered by `listings.test.ts`'s "backfills a company's listings from its orders (the seed path)" test; author's report shows a fresh seed logging `listings {"listings":149,"variants":536}` |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed, plus the one self-flagged, narrowly-scoped exception (`db/seed/index.ts`, 5 lines, additive-only, no schema/migration touched) — acceptable under the card's own "the seed creates them" criterion and CLAUDE.md's expectation that an owner flag out-of-path hunks for the relevant co-reviewer, which the author did.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior; scan-test-weakening (run by the primary reviewer) found nothing blocking; I independently confirm the seed-path test exists and passes.
- [x] Tenancy: `recordListingsForCompany` takes `companyId` and is called under `withSystem(..., shopId)` — the accepted seed exception (CLAUDE.md: `withSystem` is only for the outbox relay, cross-tenant jobs, and the seed). No new tables, so no new RLS/index surface to check.
- [x] Decisions recorded where needed: n/a.

## Optional notes (not blocking)
- Minor: the seed hunk runs `recordListingsForCompany` once per shop, after all of that shop's
  orders are inserted, which is the right place — any earlier and some order items wouldn't be
  mapped yet. No change requested.
