# Review of T-3-3 (round 1)

- Reviewer: architect on Fable (co-review)
- Author: backend-engineer (inventory) on Opus 5.5
- Verdict: approve

Scope of this co-review: contract fit (`stock.changed` payload, `setAvailability` interface T-3-1
defined), decision 0003 (opt-in) as a product/marketplace-policy rule, and cross-module design
(inventory ↔ channels boundary). The reviewer's file (`T-3-3-reviewer-r1.md`) carries the full
re-run of tsc/biome/vitest/build and the live opt-in/push exercise; I re-checked the contract
surface directly.

## Evidence I re-ran
| Command | Result |
|---|---|
| `grep -n "stock.changed" invai-contracts/src/realtime.ts` | `"stock.changed": z.object({ blankVariantId: Id, locationId: Id, available: z.number().int() })` |
| `git show b8ac9d0 -- src/modules/inventory/ledger.ts` | the new `stockChanged`/`afterCommit` publish call sends exactly `{ blankVariantId, locationId, available }` — matches the schema field-for-field, no extra or missing keys, `available` is `after.available` from the same `stockLevels` row the contract expects an `int` for |
| `grep -n "setAvailability" src/integrations/channels/types.ts` | `setAvailability(conn, updates: (AvailabilityUpdate \| LegacyAvailabilityUpdate)[], opts?: SetAvailabilityOptions): Promise<SetAvailabilityResult>` — this is T-3-1's committed interface (`563287b`), and T-3-3's call site (`availability.ts`'s `pushAvailability`) passes `{ listingVariantId, channelSku, available }` plus `{ idempotencyKey }`, matching `AvailabilityUpdate`/`SetAvailabilityOptions` exactly, not the deprecated legacy `{channelSku, quantity}` shape |
| `git -C invai-backend log --oneline` (in the worktree) | confirms `b8ac9d0`'s parent is `97651a0` (T-3-4) and T-3-1's `563287b` is in history before it — the card's stated dependency ("starts after T-3-1's `setAvailability` fix") is respected |
| Read `invai-docs/decisions/0003-stock-push-opt-in.md` against `canPushAvailability` in `availability.ts` | the decision's gate ("pushes only to connections where the shop turned on `pushAvailability`") is enforced, and re-enforced a second time inside `pushAvailability` itself right before the channel call — not just at planning time |
| Read `invai-docs/waves/3/reports/T-3-1-report.md`'s "Built" section against this diff | the `setAvailability` result shape (`{ updated, results: [{ listingVariantId, status, available, message }] }`) is consumed correctly in `pushAvailability`: `status: "set"` rows get `markAvailabilityPushed`, `not_found`/`failed` rows are counted but never marked pushed |

## Contract-fit findings
- **`stock.changed` matches the contract exactly** (field names, types, one event per
  `blankVariantId`+`locationId` pair, sent after commit only) — this closes the realtime half of
  B-104 as the card claims. No contract change was needed and none was made.
- **No new contract procedure, schema, or enum was touched.** This card is entirely inside
  `invai-backend`; `invai-contracts` is unchanged (`git show --stat b8ac9d0` touches only
  `invai-backend/**`). That's correct — `AVAILABILITY_DEBOUNCE_MS`, the push job shapes, and the
  idempotency key are all backend-internal, not contract surface.
- **The `setAvailability` interface is used as T-3-1 designed it**, including passing a stored
  `idempotencyKey` per push intent (the interface's doc comment specifically asked T-3-3 to do
  this "so a retry after a crash reuses it" — confirmed in `jobs.ts`'s `pushAvailabilityJob`,
  whose `idempotencyKey` lives in the job's persisted input, not regenerated per attempt).
- **No breaking or additive contract changes were skipped that should have been made here.** The
  wave plan's contract-stub section (in `wave.md`) only calls for changes to `ImportReport` and
  `BatchBuyResult` for T-3-4; nothing for T-3-3.

## Cross-module design
- Inventory no longer writes the `channels` tables directly (`listings`/`listingVariants`); all
  reads and the one write path (`markAvailabilityPushed`) go through `channels/sku.ts`'s exported
  helpers (`listPushTargets`, `lastPushedQuantities`, `markAvailabilityPushed`). This is the right
  boundary — `channels` owns the listing rows, `inventory` owns the push scheduling — and matches
  how the card described the split.
- Listing writes happen from jobs subscribed to `order.imported`/`item.mapped`, not from inside
  `orders/import.ts` or `orders/mapping.ts` (T-3-4's/orders owner's files), consistent with the
  card's "not touching T-3-4's files" note and with the outbox-driven pattern the rest of the
  codebase uses for cross-module reactions.

## Acceptance criteria (my lens only)
| # | Met? | Evidence |
|---|---|---|
| 3 (opt-in per decision 0003) | Yes | Gate checked in `canPushAvailability`, applied at both plan and push time; live exercise (see reviewer's file) shows a toggled-off connection producing zero pushes and a presser blocked from toggling it at all |
| 4 (`stock.changed`) | Yes | Payload matches `invai-contracts/src/realtime.ts:65` exactly |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — no `invai-contracts/**` files touched.
- [x] Nothing outside scope.
- [x] Tests exercise the contract-facing behavior (`stock.changed` payload shape, `setAvailability`
  call shape) — covered in `availability.test.ts`.
- [x] Tenancy / idempotency — deferred to the primary reviewer's and backend-foundation's files;
  nothing contract-specific to add.
- [x] Decisions recorded where needed: decision 0003 is implemented, not reopened; no new ADR
  needed for this card.

## Optional notes (not blocking)
- The author's known-gap note ("turning the opt-in on doesn't push right away") is a real product
  question (should flipping the toggle emit `stock.availability_changed` immediately, or is an
  hourly reconcile enough?) but it's a design choice for a future card, not a defect in this one —
  decision 0003 only requires that push not happen *without* opt-in, not that it happen
  *instantly* on opt-in.
