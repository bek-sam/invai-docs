# T-4-4: Pack station uses pack-complete; floor polish

| Field | Value |
|---|---|
| Scope ref | `product/scope.md#mvp-in` item 5 |
| Backlog | B-94 (floor), B-105 (without the camera scanner), B-33 (floor) |
| Owner | floor-engineer |
| Reviewer | reviewer; co-reviewers product-designer, qa-engineer |
| Risk flags | ui, floor-correctness |
| Model | opus |

## Depends on
- T-4-1 (`production.packOrder`, `wrong_style`).

## Owned paths
- `invai-floor/src/stations/{Pack,Press,Qc,Pick}Station.tsx`, `src/components/ProblemDialog.tsx`, `src/scan/result.ts`, `vite.config.ts`, `index.html`, `public/**`
- `invai-floor/src/i18n/**`
- `invai-ui/src/floor/station-header.tsx` (the Online/Offline strings only)
- `invai-floor/e2e/floor.spec.ts`, qa-engineer co-review

## Acceptance criteria
1. **Pack station:**
   - "Mark packed" calls `packOrder({ orderId, idempotencyKey })` (field renamed from `clientKey` — see wave.md). If units are missing, it lists them (unit, state) and blocks with the `PACK_INCOMPLETE`/`missing[]` data, replacing `PackStation.tsx`'s current client-only completeness check (today `finish()` never calls any pack-complete procedure at all — this card is what wires it up for real).
   - "Pack anyway" is only for permitted roles (checked via `ctx.permissions` server-side, but the button itself should also hide/disable for roles without `production.override` so packers don't see a button that always 403s), needs a reason, and calls `packOrder({ ..., override: { reason } })`.
   - Pack progress survives a reload: it's persisted in IndexedDB and cleared on completion.
   - The service worker never reloads mid-pack: prompt instead of auto-update.
2. **Problem dialog:** offers all 12 reprint reasons in en and es.
3. **QC and press truth:** they show "Sent" or "Queued" truthfully, and a server rejection shows the translated reason, not the success title. A problem without an item id isn't dropped silently.
4. **No English leaks:** station header Online/Offline, server messages, `String(err)` and `BIN_OCCUPIED` are all translated through codes.
5. **`wrong_style`:** already has its own mismatch message end to end (contract enum, `matcher.ts`, `i18n/en.ts:118`, `i18n/es.ts:120`, and the generic `t(\`floor.mismatch.${result.mismatch}\`)` lookup pattern already used in `PackStation.tsx`). Treat this as a regression check while touching these files, not new work.
6. **PWA:** PNG and apple-touch icons, and `<html lang>` set from the device language at startup.
7. **E2E:** `floor.spec.ts` covers pack with a missing unit (blocked) and then complete.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in floor (and ui).
- Floor E2E on your copy.
- Screenshots in en and es.

## Change after T-4-1 (decision 0010)
- "Pack anyway" is now **"Hand to lead"**. It calls `packOrder` with `override: { reason }` (owner and admin only). A response with `packed: false` plus `override` means the order was handed over: show a translated "Handed to lead" state, and clear the station. The order is not packed and won't ship until the missing units are packed.
