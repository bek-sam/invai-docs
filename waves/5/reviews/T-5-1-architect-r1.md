# Review of T-5-1 (round 1)

- Reviewer: architect (co-review, for `orders.updateAddress`) on Sonnet 5
- Author: web-engineer + backend-engineer (orders) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend diff a673b7b^ a673b7b -- src/modules/orders/service.ts src/modules/orders/router.ts src/modules/orders/pii.ts src/modules/orders/import.ts` | read in full |
| `git -C invai-backend diff a673b7b^ a673b7b -- src/modules/orders/address.test.ts` | read in full (9 tests) |
| `sed -n '1,40p' invai-backend/src/db/client.ts` | confirms `withTenant`/`withSystem` split and the RLS-by-default pattern this function follows |
| Backend `tsc --noEmit`, `biome check .`, `vitest run src/modules/orders src/modules/shipping` (own worktree/DB, shared with the primary reviewer's run) | clean; 78/78 passed |
| curl against my own API instance (:3191, DB copy) — see the primary reviewer's file for the full transcript; I focused my own re-run on the gate-state matrix | `buying` → `LOCKED`; `labeled` → `LOCKED`; voided → `200`; presser → `FORBIDDEN` |

## Contract conformance (`wave.md` §"Contract stubs (exact)", section 1)
| Spec requirement | Met? | Evidence |
|---|---|---|
| Gate on shipment `status` in the exact `LIVE_LABEL` set `shipping/service.ts:79`, not `orders.status` | Yes, and stricter | `service.ts`'s `ADDRESS_LOCK_STATES` = `["labeled","in_transit","delivered","exception","returned","buying","voiding"]` — the base 5 plus `buying`/`voiding`. The report documents this as a deliberate widening ("a label for the old address may be about to exist"), which is the right call: a bare `LIVE_LABEL` check would let an edit race an in-flight buy. Order life-cycle statuses (`cancelled`/`shipped`/`delivered`) are refused separately and explicitly, not used as the label proxy — matches "don't gate on `orders.status`." |
| Format-only validation, reusing `shipping/service.ts:482`'s heuristic | Yes | Same `street1` non-empty + `/^\d{5}(-\d{4})?$/` zip test. `city` was additionally required — the report justifies this ("rating and buying require a city, so releasing a hold without one would only fail later") and it's a strictly narrower, not a stricter-than-spec unannounced rule: the card's evidence doesn't forbid tightening the check where the alternative is a guaranteed later failure. |
| `ADDRESS_INVALID` (422) reusing `ADDRESS_LOCKED`'s error shape | Yes | `ORPCError("ADDRESS_INVALID", { status: 422, message, data: { detail } })` — same shape as the contract's `ADDRESS_LOCKED` (`status` + `message`), an `ORPCError` instance local to `orders`, not importing shipping's `ADDRESS_INVALID` type directly (which would be a layering violation) — a fresh definition with matching semantics per the stub's instruction ("just a new instance in `orders`"). |
| `buyerPii` upsert reusing `import.ts:283-360`'s logic | Yes | Extracted into `pii.ts`'s `upsertBuyerPii`, parameterized by which fields count as "changed" (`IMPORT_ADDRESS_FIELDS` for the channel re-import path, `ALL_ADDRESS_FIELDS` for the office edit, since the edit form also carries `company`/`country`/`phone` that a channel diff doesn't compare). `import.ts`'s own behavior is preserved byte-for-byte (same field list, same insert/update branching) — confirmed by reading the diff: `import.ts`'s call site is a mechanical extraction, not a behavior change. |
| Release the `address_check` hold via the existing `releaseOrder` path; otherwise just record the change | Yes | `if (order.holdReason === "address_check") return releaseOrder(...)`; otherwise falls through to `publishOrder` + `getOrder`, matching "no state change" for the not-yet-labeled/no-hold case. |
| Permission `orders.manage` | Yes | Router handler is plain `authed.orders.updateAddress`, and `orders.manage` is required per the proc's contract declaration; `address.test.ts`'s router-level test confirms presser `FORBIDDEN` / office success, re-confirmed by my own curl run. |
| `TIMELINE_KINDS` gains `address_updated`, appended (additive) | Yes | Contract's enum has it last, as specified; `AUDIT_KIND["order.address_updated"] = "address_updated"` wires it in without touching any existing mapping. |

## Architecture checklist
- **Idempotency:** `upsertBuyerPii` returns `null` when nothing differs, and `updateAddress` short-circuits the audit/outbox-emit/stale-quote-drop on that `null` — a same-address retry is a true no-op past the row lock, matching the platform rule that side effects are idempotent. Verified by `address.test.ts`'s idempotency test (one audit row after two identical PATCHes) and, independently, by two identical curl PATCHes producing an unchanged `updatedAt`.
- **Transactional discipline:** the row lock (`for("update")` on `orders`) is taken first and everything else — the shipment-state check, the PII upsert, the flag clear, `guardShipmentsForItems`, the audit write, the outbox emit — happens inside the same `tx`, so a concurrent `shipping.rates`/`buy` either sees the lock and waits or the whole edit rolls back together. No side effect (the audit write, the `order.updated` emit) happens outside a transaction boundary that could partially apply.
- **Reuse of `guardShipmentsForItems`:** calling shipping's existing `"cancel"` guard to drop stale quotes is a reasonable reuse rather than a new code path, and it's provably safe here specifically because every `LIVE_LABEL`/`buying`/`voiding` shipment was already refused above — so the guard can only ever see `pending`/`rated` shipments at this point, which is exactly the "drop it, nothing was committed to a carrier" case the report claims. I re-derived this from the code rather than taking the report's word for it: `ADDRESS_LOCK_STATES` and shipping's `guardShipmentsForItems("cancel")` refusal set were cross-checked and are consistent — a shipment state that would make the guard *reject* the cancel is always a state `updateAddress` already turned away.
- **Scope of the `pii.ts` extraction:** touching `import.ts` is within the card's grant (`modules/orders/**`) and is the specific reuse the wave-level contract stub calls for, not incidental scope creep. The diff is a pure extraction (same comparison fields, same insert/update branching) with no behavior change to the channel-import path — I'd have blocked a substantive change to `import.ts` under a card scoped "`updateAddress` only," but this isn't one.
- **No PII leakage into the audit trail:** `audit(...)`'s `summary` is the fixed string `"Ship-to address updated"`, never interpolating the new address; the timeline test asserts the rendered message doesn't contain the street text. Consistent with "no PII in logs, prompts or analytics."

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope — the `import.ts` touch is the specified reuse, not scope creep (see above)
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — no new tables; tenancy is RLS-by-convention via `withTenant`, consistent with the rest of `modules/orders/service.ts`; idempotency verified above; no money fields touched by this card
- [x] Decisions recorded where needed — the stricter gate, the `city` requirement and the stale-quote-drop reuse are all called out in the report's "Decisions" section with reasoning, and I independently verified each is sound rather than just documented

## Optional notes (not blocking)
- The report's own follow-up — an explicit "address changed" shipment guard action instead of reusing `"cancel"`, plus a re-check of the address at buy time — is the right next step for the shipping owner. Reusing `"cancel"` today is safe (see the state-cross-check above) but semantically borrowed; worth its own guard action so the shipping module's state machine doesn't have to reason about why an address edit can trigger a "cancel"-shaped effect.
- `updateAddress`'s raw `sql.join` for the `ADDRESS_LOCK_STATES` `IN (...)` clause is parameterized correctly (`sql`${st}`` per element, not string interpolation), so there's no injection risk — noting only because it's the one hand-rolled SQL fragment in an otherwise Drizzle-query function.
