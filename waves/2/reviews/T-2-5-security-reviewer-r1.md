# Review of T-2-5 (round 1)

- Reviewer: security-reviewer on Opus (this session)
- Author: backend-engineer (shipping) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Same worktree/setup as the primary reviewer file (`e399249`, symlinked `node_modules`, `invai_test_r25`, redis `/9`) | ok |
| `tsc --noEmit`, `biome check .`, `vitest run` | clean / clean / 318 passed |
| Tenant-isolation tests specifically: "another company can't buy or read this shipment" (`label-safety.test.ts`), "another company can't void this label" (`push-void.test.ts`) | both pass |
| `scan-test-weakening.sh` vs each commit's true parent | no hits requiring a block (mocks are of carrier/channel/outbox modules, not the code under test) |
| API+worker booted on :3295 against `invai_r25_copy`, `/health` returned ok | confirmed before the outage below |

**Same environment failure as the primary review:** the host disk filled to 0 bytes free mid-session (independently confirmed twice), taking down my exercise API/worker and then Docker/OrbStack. I was not able to personally curl the refused-role case (`presser@` calling `shipping.void` → expect 403) or the cross-tenant `NOT_FOUND` case live. I rely instead on (a) the router-level permission declaration (`shippingRouter.void` is `authed.shipping.void`, gated by contract-level permission metadata — the pattern used everywhere else in this codebase) and (b) the tenant-isolation unit tests above, which I ran myself against a real Postgres with RLS and got a pass. Recommend a live curl re-check of the refused-role case once the environment recovers, but I found no code path that would make it behave differently from every other `shipping.*` procedure.

## Threat model
Who could call these procedures, with what session, against whose data, worst outcome:
- `shipping.buy` / `shipping.batchBuy` / `shipping.void` / `shipping.rates`: any authenticated org member with `shipping.buy` permission, scoped to their own `companyId` via `withTenant` in every new code path (`rateOrder`, `buyLabel`, `voidShipment`, `guardShipmentsForItems`, `voidCancelledLabels`, `pushReleasedShipments`) — no new `withSystem` usage anywhere in either commit. Worst outcome without tenancy: a shop buys or voids another shop's label. Not possible: every query in the diff is inside `withTenant(ctx.companyId, ...)` or takes a `tx` already scoped by the caller's `withTenant`.
- Background jobs (`voidCancelledLabelsJob`, `pushReleasedJob`, `mockTrackingJob`): use `systemContext(companyId)` from the event payload, which still routes through `withTenant(companyId, ...)` inside the service functions — this is the same pattern as every other job in the codebase (`finance.recomputeJob`, etc.), not a new cross-tenant surface.
- Worst outcome for the money-flow bug this card fixes (double charge): closed by the three-transaction pattern (commit intent → call outside tx → record result) applied consistently to `buyLabel`, `rateOrder`, `pushTracking`, `voidShipment`. Verified by reading each function's full diff and by the passing "never buys/refunds/notifies twice" tests.

## Payments and marketplace-policy risk flags
- **Payments:** this card is itself the fix for a real double-charge vulnerability (B-11). The fix is structurally sound: intent recorded and committed before any carrier call, the carrier call never runs under a DB transaction or row lock, and every retry path reads the carrier back before calling `buy`/`void`/push again. The mock carrier (`integrations/carriers/mock/index.ts`) persists its "carrier records" to the S3/MinIO bucket keyed by `carrierShipmentId` (not in-process memory), so a crash-then-restart genuinely can't re-buy — this is a meaningfully more realistic crash simulation than an in-memory mock would give, and `buyLabel`'s "a crash mid-call blocks a retry while in flight, then reads back before buying" test exercises exactly that. `assertPaidActionAllowed` (T-2-1, imported not owned by this card) is called only for a *new* buy (`!resume`), never for finishing one already in flight, so an expired trial can't strand a shop with postage already paid for but no recorded label — correct placement, no network call inside the check.
- **Marketplace-policy:** the CSV-channel ship-on-scan change (criterion 5) is a genuine compliance improvement — it stops the platform from telling Etsy/Amazon/TikTok/Walmart-adjacent internal state (and any future reporting) that an item shipped before the carrier actually took it, which matters for the SCAN-based on-time metrics research doc 10 §11 discusses. No new webhook or external-facing surface was added by this card (EasyPost tracker webhooks are explicitly out of scope, deferred to wave 3 per the card).

## Findings
None at High or Medium. See the primary reviewer's non-blocking notes (migration 0012's unique index has no existing-data guard — currently safe since no real carrier data exists yet; `channelPerformance`'s pre-existing `labeled_at`-as-shipped assumption is now more consequential for CSV channels but is untouched, out-of-scope code) — I concur with both, neither is a security finding on its own.

## Checks
- [x] RLS / tenancy: every new/changed function scoped by `withTenant`, no unexplained `withSystem`
- [x] No PII newly logged, sent to a prompt, or added to analytics (nothing in this diff touches buyer PII fields; `voidCancelledLabels`/`recordLabel` audit summaries contain only tracking codes and reasons)
- [x] Idempotency keys / unique indexes present for the money- and buyer-facing effects (label buy: partial unique index on `(company_id, shipment_id)`; void and push: in-flight timestamps + status guards)
- [x] No new webhook surface, no new external-facing endpoint
- [x] Tests exercise the tenant-isolation and refused-role cases; none weakened
