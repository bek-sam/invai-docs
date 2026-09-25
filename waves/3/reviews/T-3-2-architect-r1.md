# Review of T-3-2 (round 1)

- Reviewer: architect on Fable
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Scope of this co-review
The two open design questions the author flagged for me: (1) the extra `subject_id`/`occurred_at` columns on `carrier_webhook_events` beyond decision 0009's base shape, and (2) reusing the `tracking_push_failed` alert kind for stuck buy/void alerts. Also checked: does this stay inside my r1 wave-plan correction (`markInTransit(tx, ctx, shipmentId)`, no `at` param) and the agreed webhook-routing interface.

## Evidence I re-ran
Same worktree and commands as the primary reviewer's file (`tsc`, `biome`, `vitest run` — 380 passing; `rls-coverage.test.ts` + `authz.test.ts` green). I additionally read `invai-contracts/src/schemas/alerts.ts` and `invai-web/src` for alert-kind consumers, and `modules/shipping/service.ts`'s `markInTransit`/`markDelivered`/`transitionItem` (read-only for this card, confirmed untouched: `git show b648cfd --stat` lists no `service.ts` hunk).

## 1. `subject_id` and `occurred_at` on `carrier_webhook_events` — **approved**

My r1 wave-plan note said: if out-of-order detection needs the event's own timestamp, add `at` to `markInTransit` too (additive, default `new Date()`) rather than inventing a second entry point. The author didn't take that path, and I checked why that's actually the right call, not a deviation:

- `markInTransit`/`markDelivered` are forward-only by their own status checks (`s?.status !== "labeled"` etc.) regardless of any timestamp — so an `at` parameter on `markInTransit` would do nothing to prevent backward moves that these functions don't already prevent themselves.
- The actual gap the timestamp closes is narrower than I assumed when I wrote that note: it's the **finer `trackingStatus`** (`out_for_delivery`, `available_for_pickup`, etc.) written in `applyReading` *outside* `markInTransit`, guarded only by "still `in_transit`", not by any ordering check. An `at` param threaded through `markInTransit` wouldn't reach that line at all — the state that actually needs ordering protection lives in `jobs.ts`, which is this card's file, not `service.ts`'s.
- Storing `occurredAt` (and the `subject_id` it's compared per) on the event-dedupe row keeps the fix inside this card's owned paths and inside decision 0009's existing system-only-write, RLS-covered table, rather than expanding `service.ts` (not this card's to touch) or inventing a new column on `shipments` (also not this card's, and would need its own migration + backend-foundation sign-off for a table T-3-3/T-3-4 are also touching this wave).

This is additive to decision 0009's shape (two nullable columns, one new composite index), doesn't change the REVOKE/RLS pattern, and I verified live (via the reviewer's and backend-foundation's re-runs) that an older event is correctly ignored and a delivered shipment never regresses. **No new ADR needed** — this is a legitimate extension of 0009, not a new decision, and the author correctly didn't invent a `markInTransit(at)` entry point I'd have had to review for every other caller.

One ask, not a blocker: document this column pair's purpose (finer-status ordering, not the coarse state machine) in a short doc comment cross-reference from `service.ts`'s `markInTransit`, so a future reader of `service.ts` doesn't assume the coarse machine has no ordering protection at all when it in fact does, just not via this table. I'll take that as a one-line follow-up rather than blocking this card on it.

## 2. Reusing `tracking_push_failed` for stuck-intent alerts — **approved, with a required follow-up**

Checked `invai-contracts/src/schemas/alerts.ts`: `ALERT_KINDS` includes `tracking_push_failed` already, and — I grepped the whole backend — **this card is the first caller that ever raises an alert with that kind** (no pre-existing `raiseAlert(..., { kind: "tracking_push_failed" })` anywhere else in `modules/`). So there's no collision with a genuine "we tried to push tracking to the channel and gave up" alert; that alert doesn't exist yet in the code, only the enum value does. Checked `invai-web/src` for any per-kind branching (icon, label, routing) — found none; the UI renders `title`/`message`/`severity` generically, both of which this code sets correctly and specifically per intent (`"A label purchase needs a look"` vs `"A label void needs a look"` vs `"Tracking wasn't sent to the channel"`). `dedupeKey` (`stuck-intent-${kind}-${shipmentId}`) is disjoint per intent and per shipment, so there's no dedupe collision either.

Given that, reusing the kind is low-risk today and correctly labeled to the user. But it is contract debt: `tracking_push_failed` will end up describing three semantically different situations (a genuinely-failed tracking push, a stuck buy, a stuck void) once T-2-5's real push-failure path also starts raising it, distinguishable only by `data.intent`, which nothing in the contract documents or types. **I'm requiring `label_stuck` (or a more general `intent_stuck`) be added to `ALERT_KINDS` as a wave-4 follow-up**, additive per the contract's own rules (new enum value at the end), before this reuse becomes load-bearing for more than one wave. This is already on the wave doc's follow-up list with me as owner — I'm confirming it, not adding new scope to this card.

## Contract / consumer check
No `invai-contracts` changes in this diff (correctly — `service.ts`'s existing `Shipment`/state shapes are untouched, and no new procedure was added; the webhook route is a plain Hono route, not an oRPC procedure). `ITEM_TRANSITIONS`/`canTransition()` weren't touched, and `shipItems` is called through existing, unmodified helpers. No consumer (web/floor) needs anything from this card.

## Checks
- [x] Contract fit: no contract changes; correctly so.
- [x] State-machine correctness: forward-only at both the service layer (pre-existing) and the event-table layer (new), verified via the reviewer's and my own reading of `markInTransit`/`markDelivered`/`markException` and `processCarrierEvent`.
- [x] Permission choice: n/a, public webhook route, matches Shopify's pattern.
- [x] Tests exercise the behavior; scan-test-weakening reviewed, nothing blocking.
