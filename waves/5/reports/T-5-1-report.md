# Report: T-5-1 Order detail actions, shipment section, address fix
Author: web-engineer + backend-engineer (orders) on Opus 5.5

**Commits (not pushed):** backend `a673b7b` (on `d22b6ac`), web `bca872f` (on T-5-2's `a2566b2`).

## Intake
- Card T-5-1, scope `product/scope.md#mvp-in` items 1 and 7, backlog B-84. Risk flag `ui` → product-designer co-review; architect co-review for `updateAddress`.
- Owned paths: invai-web `features/orders/**`, `routes/_app/orders/**`, this card's i18n keys; invai-backend `modules/orders/**` (`updateAddress` only).
- Plan-review changes applied: gate on shipment label status, format-only validation, reuse import's `buyerPii` upsert. B-62 was already done, so it wasn't touched.
- Mid-task requests:
  - The tech lead passed on T-5-3's view keys (`due_today`, `overdue`, `blocked`). They are used exactly.
  - Token budget: 6 screenshots, unit tests plus my own flow, no golden-path suites.

## Built
**Backend** (`modules/orders/`)
- `service.ts` `updateAddress`:
  - Locks the order row, the same lock `shipping.rates` takes, so a rate or buy can't slip between the check and the write.
  - Refuses `ADDRESS_LOCKED` (409) if any shipment is in a live-label state, or while a buy or void is in flight.
  - Refuses cancelled, shipped and delivered orders.
  - Format check: street, city, and a ZIP matching `^\d{5}(-\d{4})?$`. A failure returns `ADDRESS_INVALID` (422).
  - Upserts `buyer_pii`. The form has no email field, so the channel's email is kept.
  - Clears `address_invalid` flags.
  - Drops stale rate quotes through `guardShipmentsForItems`.
  - Writes the `order.address_updated` audit (no PII), which the timeline shows as kind `address_updated`, and emits `order.updated`.
  - Calls `releaseOrder` when the hold reason is `address_check`. Otherwise there is no state change.
  - Idempotent: sending the same address again writes and audits nothing.
- `pii.ts` (new): `upsertBuyerPii`, now shared by `import.ts`'s re-import branch (same comparison fields as before) and `updateAddress`.
- `router.ts`: the stub is removed.
- `address.test.ts`: 9 tests:
  - release on an `address_check` hold;
  - edit with no hold;
  - a hold for another reason is kept;
  - idempotent retry;
  - `ADDRESS_INVALID`;
  - `ADDRESS_LOCKED` for labeled, in_transit, buying and voiding, then allowed after a void;
  - stale quotes dropped;
  - cross-tenant request returns `NOT_FOUND`;
  - through the router: presser is refused (`FORBIDDEN`), office succeeds.

**Web**
- `features/orders/order-actions.tsx` (new):
  - Per-unit rush toggle with an undo toast.
  - Flag dialog. Flags show translated labels from their codes, with a clear (×) button.
  - Artwork dialog for non-personalized `needs_artwork` units: pick a design placement, or upload a file.
  - Order tags: add, and remove with undo.
  - `ShipmentSection`:
    - carrier and service, tracking link, label PDF, cost (postage + label fee);
    - progress steps: label bought, tracking sent (or "add it on the channel"), with the carrier, delivered;
    - Void with a `ConfirmDialog` that explains `VOID_REJECTED`, busy and refund-pending.
  - `AddressSection` and its form:
    - opens by default on an `address_check` hold;
    - hidden while a live label exists, with "void the label first" copy;
    - client-side checks use the same rules as the server;
    - `ADDRESS_LOCKED` and `ADDRESS_INVALID` errors are shown in plain words;
    - the copy doesn't imply a carrier check.
- `order-detail.tsx`: wires the new components in. The inline English flag messages are replaced.
- `views.ts`:
  - New views: `due_today` (uses `me.org.timezone`, DST-safe), `overdue`, `blocked`, `in_production` (in_production + ready_to_ship), `shipped`, `cancelled`.
  - `tabCount` fix: Needs mapping, Needs artwork and Blocked are now counted with `counts({ itemState })`. Before, both item-state tabs showed `needs_attention`.
- `routes/_app/orders/index.tsx`:
  - filters for placed date range, tag and channel, plus "Clear filters";
  - bulk Cancel through `BulkCancelDialog` (in `dialogs.tsx`), which lists per-order failures;
  - Export CSV (`export.ts`): pages through the current view, 200 per request, up to 5,000 rows. It includes the buyer name but no address. Formula-like cells are neutralized.
- `orders-table.tsx`: phone rows no longer show a red ship-by badge on finished orders, matching desktop.
- i18n: 120 keys in en and es, plus 6 view labels in `i18n-extra-en.json`, with the Spanish in `i18n-es.json`.
  - I didn't run `pnpm i18n` in any tree. I generated the entries in a scratch copy, diffed them against a HEAD-generated baseline, and applied only my hunks.
  - The committed diff is additions only.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Unit actions: rush, flag, artwork, tags; flag labels translated | Yes | Browser: artwork from a design moved the unit from needs_artwork to ready, rush with undo, a "Needs a look" flag with a note, tag "gift". See `en-15-unit-actions-done.png`. |
| 2 Shipment section, void with confirm | Yes | Browser: void confirm, then voided (`es-04-void-confirm.png`, `en-12-after-void-released.png`). |
| 3 Address hold: edit, format-only check, release, `ADDRESS_LOCKED` | Yes | curl results under "Exercised for real". Browser: bad ZIP gets a field error; a good address releases the hold (`es-02-address-hold-form.png`). Locked, then void, then edit, then released (`en-12`). |
| 4 Tab counts, new views, filters, bulk cancel, CSV | Yes | Tabs: Blocked 9 = Needs mapping 7 + Needs artwork 2; Ready 31. The Ready export had 31 rows plus a header. Bulk-cancelled 2 orders (`en-03-bulk-cancel-confirm.png`). |
| 5 en/es, 390 px, keyboard, loading/empty/error | Mostly | See the notes below. |

Notes on criterion 5:
- Screenshots were taken in en and es, light and dark, at 1440 and 390 px.
- Horizontal overflow was 0 px at 390 on the list and on detail (`en-390-01-orders-list.png`).
- Every control is a native button, input or select with a label.
- Loading uses skeletons and `SkeletonRows`, empty uses `EmptyState` (checked with a no-match tag filter), and errors use `ErrorState`. I didn't capture the loading state on screen.
- The Playwright run found 0 console errors and 0 failed requests.

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| backend @ `a673b7b` | `tsc --noEmit`; `biome check` | clean (T-5-3's `d22b6ac` already made tenancy typecheck) |
| backend @ `a673b7b` | `vitest run src/modules/orders src/modules/shipping` | 10 files, 78 passed |
| backend (worktree, before commit) | full `vitest run` | 453/456. The 3 failures were `channels/security.test.ts` ("Shopify connection link has expired") and `files/service.test.ts` (presign 403). The run took 17 minutes under shared load; both files pass alone. |
| web @ `bca872f` | `tsc`, `biome check .`, `vitest run`, `vite build` | clean; 70 tests passed; built |

## Exercised for real
Setup: API and worker on :3110, Redis db 1, DB copy `invai_t51_copy`, web on :5113, my own imaging on :8110. Mock labels need imaging, and :8000 wasn't running.

curl results, as office unless noted:
- Hold for `address_check` → 200 `on_hold`.
- PATCH with ZIP `857` → 422 `ADDRESS_INVALID`.
- PATCH with a valid address → 200: status `new`, no hold, items back to their held-from state.
- As presser → 403 `FORBIDDEN` (`orders.manage`).
- On a labeled order → 409 `ADDRESS_LOCKED`. Void → `voided`. The same PATCH then → 200. The timeline shows `address_updated | Ship-to address updated`, and the shipment row shows `voided`.

## Decisions
- **Gate is stricter than the plan.** It also refuses shipments in the `buying` and `voiding` states: a label for the old address may be about to exist.
- **Row lock:** locking the order row serializes the edit with `rateOrder`.
- **City is required too.** Rating and buying (`addressValid`) require a city, so releasing a hold without one would only fail later.
- **Stale quotes are dropped** by reusing shipping's public `guardShipmentsForItems(..., "cancel")`. Every labeled or in-flight shipment has already been refused, so only pending or rated quotes are reset.
- **Email kept:** the form carries no email, so the channel's stays.
- **In production** includes `ready_to_ship` orders, so packed orders don't disappear from every view but All.

## Known gaps and follow-ups
- Shipping owner:
  - Add an explicit "address changed" guard action, instead of reusing "cancel".
  - Consider re-checking at buy time that the address hasn't changed since rating.
- Pre-existing, not in my paths:
  - `ShipByBadge` relative time is English in es ("1 hour ago", `invai-ui`, B-93).
  - Timeline state messages are English server text.
  - Spanish uses "Etiqueta" for both order tags and shipping labels (consistent with the existing catalog; product-designer to decide).
- `es-04-void-confirm.png` was taken before I removed a row that showed the server's English push note. That row is no longer in the UI.

## Blocked by other owners
- None.

## Processes and data
- Stopped: my API, worker, web (:5113) and imaging (:8110).
- Dropped `invai_t51_copy` and `invai_test_t51`; flushed Valkey db 1.
- Removed worktrees `../invai-backend-t51` and `../invai-web-t51`, and the scratch files in `/tmp`.
- The shared dev DB was untouched.
- Kept 6 screenshots in `reports/T-5-1/`.
