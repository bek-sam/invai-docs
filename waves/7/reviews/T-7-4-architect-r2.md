# Review of T-7-4 (round 2)

- Reviewer: architect on Claude Sonnet 5
- Author: backend-engineer (orders) on Claude Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `invai-docs/waves/7/wave.md:149` | "Grant (tech lead, 2026-09-26), recorded here: T-7-4 was granted `integrations/channels/**` for the hold signals ... and the Walmart CSV per-line cancel fix, plus `db/schema/orders.ts` `channel_updated_at` with migration 0022 and about 3 lines in `sync.ts`." This covers, path for path, everything round 1 flagged as undocumented: `integrations/channels/csv/parse.ts`, `integrations/channels/types.ts`, `db/schema/orders.ts`, `drizzle/0022_orders_channel_updated_at.sql`, and the `sync.ts` hunk. |
| `git -C invai-backend log --oneline 16ddc52..0e16314` | unchanged — still just `6caf8db` and `0e16314`; no code moved between rounds |

Round 1's design review (staleness column is additive and correctly watermarked against a dedicated column rather than `orders.updated_at`, first-time orders handled via null `channelUpdatedAt`, contract shapes for `ChannelHold`/`ChannelLineCancel` sound) is unaffected by this round — nothing in the diff changed, only the wave record. See `T-7-4-architect-r1.md` for that evidence.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 3. Staleness (design) | Yes | Unchanged from round 1; additive migration, correct watermark design, confirmed again by re-reading `wave.md:149`'s scope against the actual diff — no mismatch. |
| 1-2, 4-6 | Yes | Unchanged from round 1. |

## Blocking findings
None. The one round-1 finding — the `integrations/channels/**` and `db/schema/orders.ts` grant wasn't recorded in `wave.md` — is resolved by the tech lead's confirmation and the new `wave.md:149` entry, which matches the round-1 diff exactly (no scope drift, no paths in the grant that aren't in the commits, and no commits touching paths outside it).

## Checks
- [x] Only owned paths changed, including the now-documented grant
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened (unchanged from round 1)
- [x] Tenancy, idempotency, money in cents, en/es text (unchanged from round 1)
- [x] Decisions recorded where needed — both the staleness design and the ownership grant are on record in `wave.md`

## Optional notes (not blocking)
Carried over from round 1: a standalone `invai-docs/decisions/` entry for "staleness watermark is a dedicated column, not `updated_at`" would help future cards that touch channel sync, beyond this one wave's file. Not required for approval.
