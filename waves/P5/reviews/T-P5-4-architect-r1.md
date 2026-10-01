# Review: T-P5-4 Backend fills alert params and timeline reason codes
Reviewer: architect (co-reviewer, contract fit) on Opus 5.5. Author: backend-engineer on Sonnet 5.
Round: 1 (covers cdeb3e3 + round-2 fix 471355a, reviewed together).

## Verdict: approve

## Scope checked (against R1 only)
- No file under `invai-contracts/**` touched by either commit — confirmed by `git show --stat`. Additive-only rule intact.
- `AlertInput`/`raiseAlert`/`toAlert` in `today/service.ts`: `messageCode`+`params` nested at `data.messageCode`/`data.params`, never top-level — no collision with `available`, `intent`, `deliveryId`, `reorderPoint` etc. already in `data`. `toAlert` returns both only when `AlertMessageCode.safeParse` and `AlertParams.safeParse` both succeed; round-2 test proves a known code with invalid params (bad `sheetStatus` enum) drops both fields, not just an unknown code.
- Each `messageCode`'s `params` keys match `ALERT_MESSAGE_PARAM_KEYS` exactly: order_at_risk (orderNo, shipBy, timeZone, hours), order_overdue (orderNo, shipBy, timeZone), sync_broken (connectionName), sheet_stuck (sheetName, hours, sheetStatus), stock_low (blankName, available, reorderPoint, incoming), plan_limit_near (usedPct, used, limit, planName) vs plan_limit_reached (used, limit, planName, no usedPct), label_buy_stuck/label_void_stuck/tracking_push_stuck ({}), po_stuck_submitting (poNo, supplierName), webhook_stuck (channel), vendor_email_unconfirmed/vendor_email_failed (sheetName, vendorName). Checked each call site's diff (today/service.ts, shipping/jobs.ts, inventory/jobs.ts, channels/jobs.ts, vendors/delivery.ts) against the ruling's table — all match.
- Round-2 fixes correctly address the two Spanish-leak risks the ruling implies ("product, shop and supplier words only"): `po_stuck_submitting.supplierName` now maps the stored enum code to a display name (S&S Activewear/SanMar/Other) instead of the raw code; `vendor_email_*`'s `vendorName` is omitted entirely (not sent as English "the vendor") when the join misses. `title`/`message` English prose is correctly left untouched in both cases — the fallback stays fallback.
- `orders/service.ts` `reasonCodeFor`: rule order matches the ruling exactly — held/cancelled-by-target-state first (correctly resolves the `buyer_request`/`out_of_stock`/`other` overlap), then the exact-string table (all 17 strings from the ruling present, including the three seed/scan ones with spaces), then `on_sheet`/`sheet_received`/`reprint` regexes, else `{}`. `reprint` with an unknown reason value correctly returns the code alone (no `reasonParams`), matching "otherwise the code goes out without the param." Spread only onto `tRows` (`kind: "state_changed"`) — confirmed by grep, no audit/note rows get a reason.
- All codes referenced (`EXACT_REASON_CODES` values, `on_sheet`, `sheet_received`, `reprint`, `held`, `cancelled`) exist in `TIMELINE_REASON_CODES`; `TimelineReasonParams` keys (`sheetName`, `reprintReason`, `holdReason`, `cancelReason`) match what's set.
- No exhaustive switch added over `ALERT_MESSAGE_CODES` or `TIMELINE_REASON_CODES`/`AlertMessageCode` in the diff — lookups are `Record`/`Set` reads with fallthrough to `{}`/English, consistent with the A2 lesson.
- Producer list from the ruling (import.ts, mapping.ts, service.ts, personalization/service.ts, production/floor.ts, sheets.ts, shipping/service.ts, seed/builder.ts) is untouched — confirmed no changes to those files; this card only reads at timeline-build time as specified.

## Evidence I re-ran
None — read-only diff review per the task; nothing here looked off enough to warrant a targeted test run. Contract `pnpm test` was already green per T-P5-3's own gate and this card adds no contract changes.

## Notes (non-blocking)
- `inventory/jobs.ts`'s new `SUPPLIER_DISPLAY_NAMES` duplicates a name map that likely exists in `inventory/service.ts`; acceptable per the card's owned-paths fence (service.ts is read-only here) and flagged honestly in the report.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
