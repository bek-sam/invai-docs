# Review of T-7-4 (round 1)

- Reviewer: architect on Claude Sonnet 5
- Author: backend-engineer (orders) on Claude Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend-review-t74 log --oneline 16ddc52..0e16314`, `git diff --stat 16ddc52..0e16314` | 13 files, +13658/-76 (dominated by the generated `drizzle/meta/0022_snapshot.json`) |
| `node_modules/.bin/tsc --noEmit` (contracts pinned to `00bd3b3` in a side worktree, see reviewer-r1) | clean |
| `node_modules/.bin/biome check .` | clean |
| `node_modules/.bin/vitest run` | 79 files / 567 tests passed |
| Read `drizzle/0022_orders_channel_updated_at.sql`, `db/schema/orders.ts` diff | one nullable column, no backfill, no default |
| Read `wave.md` §"Contract stubs", §"Clarifications", §"Build log and follow-ups" against the diff | see finding below |

## Acceptance criteria (design-level)
| # | Met? | Evidence |
|---|---|---|
| 3. Staleness | Yes, and it's the better design | Round 0 compared against audit rows (`data.sourceUpdatedAt` on `order.imported`/`order.synced`); round 1 replaced that with a real column, `orders.channel_updated_at`, per `wave.md:148`'s recorded approval ("newest channel timestamp applied", not `orders.updated_at`). This is the right call: `orders.updated_at` moves on every floor scan via `$onUpdate`, which would have permanently wedged staleness detection the first time a scan raced a channel edit. The column is additive (`ALTER TABLE orders ADD COLUMN channel_updated_at timestamptz`, nullable, no default) — safe on the live table, no migration-time lock beyond the metadata change, no backfill needed since null correctly means "nothing applied yet / channel sends no timestamp." |
| First-time orders | Yes | `createOrder` sets `channelUpdatedAt` from `n.sourceUpdatedAt` at insert; `updateExisting`'s staleness guard only fires when `o.channelUpdatedAt` is truthy, so an order created before this column existed (or via a source with no timestamp) never false-positives as "stale" — it just adopts the first timestamp it sees. |
| Contract shapes | Yes | `NormalizedOrder.sourceUpdatedAt` and `ITEM_FLAG_CODES.channel_edit_after_press` landed in `invai-contracts` at `7bb2bb1` per the wave stub, exactly as specified (nullable `Timestamp`, one new enum value, additive). No further contracts change was needed for T-7-4 itself. |

## Blocking findings
1. **Ownership: `integrations/channels/csv/parse.ts` and `integrations/channels/types.ts` are outside T-7-4's owned paths, and the wave doc explicitly assigned that territory to T-7-1.** `wave.md:131` says, in my own words from the plan review: "`invai-contracts` needs a grant to T-7-4 ... Populating `sourceUpdatedAt` also touches every channel adapter's `normalize()` ... that's `integrations/channels/**`, T-7-1's territory this wave, not T-7-4's." Round 1 has T-7-4 adding `ChannelHold`/`ChannelLineCancel` to `integrations/channels/types.ts` and wiring TikTok/Amazon/Walmart detection directly into `csv/parse.ts` — the same file class the clarification steered away from T-7-4. I traced T-7-1's own commit (`24b6790`) and confirmed it never touched `csv/parse.ts` for this purpose (only the export builders), so there's no live collision in the current tree — but there's also no `wave.md` line recording that I (architect) or the tech lead granted this specific extension, unlike the parallel case for T-7-2 which got an explicit build-log entry (`wave.md:143`). As the architect who wrote that clarification, I'd have granted this on request — sequencing it after T-7-4's own report explicitly flagged the blocker ("Blocked on a grant... nothing produces the holds signal yet") makes sense, since T-7-1 had already finished its wave-7 slice and waiting on a second pass from that agent would have blocked the wave. But the record needs to show that, not just the builder's say-so. **Ask:** tech lead adds the grant line to `wave.md`'s T-7-4 build log (mirroring `wave.md:143`'s wording for T-7-2), or this gets kicked back to be re-scoped through T-7-1.
   - This is not a design or correctness objection to the change itself — the shapes (`ChannelHold`, `ChannelLineCancel`) are sound and match what the wave stub anticipated for this kind of signal.

## Checks
- [x] Only owned paths changed — no, per blocking finding 1 (procedural, not functional)
- [x] Nothing outside scope — the `db/schema/orders.ts` + migration grant (staleness column) is documented (`wave.md:148`); the CSV-parser grant is not
- [x] Tests exercise the behavior, none weakened (per reviewer-r1's scan-test-weakening.sh run: no hits)
- [x] Tenancy — no new table; existing RLS on `orders` covers the new column. Idempotency — `channel_updated_at` staleness check + `cancelLineFromChannel`/`holdFromChannel`'s "seen" lookups are all idempotent by construction (checked, didn't just take the report's word).
- [x] Decisions recorded where needed — staleness design is recorded; the CSV-parser grant is the one gap (finding 1)

## Optional notes (not blocking)
- Worth a follow-up decision doc entry (`invai-docs/decisions/`) for "staleness compares against a dedicated `channel_updated_at` column, not `updated_at`" — it's recorded in `wave.md` but this is exactly the kind of design call (`$onUpdate` columns are unsafe as staleness watermarks) that should be discoverable outside one wave's file if another card touches channel sync later.
- `db/schema/orders.ts`'s comment on `channelUpdatedAt` is clear and will save the next person from re-deriving why `updated_at` wasn't reused.
