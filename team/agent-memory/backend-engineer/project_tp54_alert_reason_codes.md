---
name: project_tp54_alert_reason_codes
description: T-P5-4 (2026-10-01) — alerts.data nested messageCode/params pattern, timeline reasonCode derivation, and how to prove it on seed data.
metadata:
  type: project
---

Built B-224/B-238 (today's alerts + orders timeline i18n codes), contract 0.11.0 (`invai-contracts` d6d038b).

- Pattern worth reusing: when a Zod-typed "extra" field must ride inside an existing untyped
  jsonb `data` column without a migration, nest it under its own key (`data.messageCode`,
  `data.params`) rather than merging at the top level — avoids collisions with the kind's
  existing ad-hoc keys (`available`, `intent`, `deliveryId`...). The read side (`toAlert`)
  must re-validate with the *current* build's schema (`AlertMessageCode.safeParse` then
  `AlertParams.safeParse`) before surfacing either field, so a future/unknown code written by
  an older or newer build silently falls back to the plain English `title`/`message` instead of
  crashing or leaking a bad shape.
- `reasonCodeFor(to, reason)` in `orders/service.ts` derives `TimelineEntry.reasonCode` from the
  already-stored free-text `item_transitions.reason` at *read* time — zero producer changes, zero
  migration. Rule order matters: check the target state (`on_hold`/`cancelled`) before exact
  strings, because reasons like `buyer_request`/`out_of_stock` appear in both HOLD_REASONS and
  CANCEL_REASONS.
- Proved both end-to-end on the real seed (no custom fixtures needed): `GET /api/v1/alerts`
  already had order_at_risk/order_overdue rows with live params; a direct
  `docker exec local-postgres-1 psql ... order_item_transitions where reason like 'on sheet%'`
  found a real on_sheet/sheet_received pair to hit via `GET /api/v1/orders/<id>/timeline`. Cheaper
  than building fixtures for sync_broken/sheet_stuck/stock_low/plan_limit in tests — for those I
  used a generic `raiseAlert`/`toAlert` round-trip test over all 14 `ALERT_MESSAGE_CODES` instead
  of standing up gang_sheets/blank_variants/billing fixtures per kind.
- `PRESSER` role has `orders.read` but not `alerts.read` — so "the office procedure is refused"
  for a presser means the *alerts* list (403), not the order timeline (200 for presser too).
