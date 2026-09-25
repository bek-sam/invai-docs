# Review of T-5-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer + backend-engineer (orders) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend diff --stat a673b7b^ a673b7b` | 5 files, all under `modules/orders/**` |
| `git -C invai-web diff --stat bca872f^ bca872f` | 12 files, all under `features/orders/**`, `routes/_app/orders/**` or i18n |
| backend worktree @ `a673b7b`: `tsc --noEmit` | clean |
| backend worktree @ `a673b7b`: `biome check .` | clean (244 files) |
| backend worktree: `vitest run src/modules/orders src/modules/shipping` (own test DB `invai_test_t51r`) | 10 files, 78 passed |
| backend worktree: `vitest run src/modules/channels/security.test.ts src/modules/files/service.test.ts` (isolated rerun) | 2 files, 9 passed — confirms the report's flaky-under-load claim, not a real regression |
| web worktree @ `bca872f`: `tsc --noEmit` | clean |
| web worktree: `biome check .` | clean (126 files) |
| web worktree: `vitest run` | 11 files, 70 passed |
| web worktree: `vite build` | built, no errors (only a pre-existing >500kB chunk warning) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits found, but all trace to other commits sharing the branch (T-5-3's `d22b6ac`), not `a673b7b` — confirmed with `git diff a673b7b^ a673b7b -- address.test.ts` |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` | one hit (`todayRange(..., "Not/AZone")`), confirmed part of `bca872f`'s own `views.test.ts` — a legitimate new assertion (invalid-timezone fallback doesn't throw), not a weakening |
| Browser pass on API :3191 / web :5191, `REDIS_URL=/9`, DB copy `invai_t51r_copy` then `drizzle-kit migrate` | see below — done via curl against the API, not the browser UI (see note) |

**Note on the browser pass:** Chrome (via the claude-in-chrome extension) is a single resource shared with a concurrent co-review already running against port 5192; my navigation attempts repeatedly landed on or disrupted that other session's tab instead of a stable tab of my own. To avoid interfering with someone else's live review, I exercised every required flow with curl against my own API instance (:3191, signed in as `office@desertbloom.test` / `presser@desertbloom.test`, DB copy `invai_t51r_copy`) instead of the browser UI, and cross-checked against 3 of the author's screenshots (`es-02-address-hold-form.png`, `es-04-void-confirm.png`, `en-03-bulk-cancel-confirm.png`).
- Address hold → bad ZIP `787` → `422 ADDRESS_INVALID` → good address → `200`, hold released, timeline shows `address_updated` then `released`, audit message has no street text.
- Order with shipment `status=buying` → PATCH → `409 ADDRESS_LOCKED`. Same order `status=labeled` → `409 ADDRESS_LOCKED`. Voided the shipment → PATCH → `200`.
- `POST /order-items/{id}/rush {rush:true}` → `isRush:true`. `POST /order-items/{id}/flags {code:"manual_review"}` → flag added with the translated message ("manual review"), not my raw input — matches "flag messages are translated from codes."
- Bulk cancel: two `POST /orders/{id}/cancel` calls (the web's `BulkCancelDialog` loops `Promise.allSettled` over the single-cancel endpoint, confirmed in `dialogs.tsx`) both returned `200`; `orders.counts` cancelled count went 8→10.
- CSV export: no dedicated endpoint; `ordersCsv()` builds the file client-side from `orders.list` data, restricted to `order_no, channel, status, placed_at, ship_by, rush, at_risk, overdue, buyer, items, total_usd, tags, hold_reason` — no address, phone or email.
- Refused case: presser role, same PATCH → `403 FORBIDDEN` ("Missing permission orders.manage").

Processes stopped, `invai_test_t51r` and `invai_t51r_copy` dropped, Redis db 9 flushed, both review worktrees removed.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Unit actions: rush, flag, artwork, tags; flag labels translated | Yes | curl: rush toggle and flag confirmed above; artwork/tags dialogs read in `order-actions.tsx`, gated on `orders.manage`/`orders.map`; screenshot `en-15-unit-actions-done.png` (author's report) not independently re-viewed but code matches. |
| 2 Shipment section, void with confirm | Yes | `es-04-void-confirm.png` viewed: confirm dialog explains the refund and "don't ship" warning before voiding. Void call re-run via curl, succeeded. |
| 3 Address hold: edit, format-only check, release, `ADDRESS_LOCKED` | Yes | Re-run above (422/200/409/200 sequence). `es-02-address-hold-form.png` viewed: form matches server's fields, copy doesn't imply a carrier check ("La paquetería revisa la dirección cuando compras la etiqueta"). |
| 4 Tab counts, new views, filters, bulk cancel, CSV | Yes | `tabCount`/`viewFilters` in `views.ts` computed from three independent `itemState` count calls (`index.tsx:137-149`), not addition of client-derived numbers — matches the screenshot's Blocked 9 = Needs mapping 7 + Needs artwork 2. `en-03-bulk-cancel-confirm.png` viewed. Bulk cancel and CSV re-run above. |
| 5 en/es, 390 px, keyboard, loading/empty/error | Yes | en/es key sets added in `bca872f` are 1:1 (110 keys each, diffed by key name). Client-side ZIP regex matches server's exactly. Not independently re-screenshotted (see product-designer's co-review for the layout/a11y pass). |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — backend `modules/orders/**` only; web `features/orders/**`, `routes/_app/orders/**`, `i18n/{en,es}.ts`, `scripts/i18n-*.json`.
- [x] Nothing outside scope — `import.ts`'s change is the `upsertBuyerPii` extraction the card's evidence explicitly calls for ("reusing `import.ts:283-360`"), not unrelated work.
- [x] Tests exercise the behavior, and none were weakened — `address.test.ts` (9 new tests, all real assertions, no `.skip`/`.only`) covers release, no-hold-write, kept-hold, idempotency, `ADDRESS_INVALID`, `ADDRESS_LOCKED` across every lock state plus post-void, stale-quote drop, cross-tenant `NOT_FOUND`, and router-level `FORBIDDEN`/success. Scan-script hits traced to other commits, not this one (see Evidence).
- [x] Tenancy (`withTenant`, RLS on new tables) — `updateAddress` takes no explicit `companyId` filter on its `orders`/`shipments` reads, same as every other function in `service.ts`; it relies on RLS via the `withTenant`-scoped connection, which is the established pattern here (confirmed by `db/client.ts`'s comment: "Every request-scoped query goes through `withTenant()`"). The `address.test.ts` cross-tenant test ("returns NOT_FOUND for another company's order") passed. No new tables were added by this card.
- [x] Idempotency, money in cents, en/es text — `updateAddress` is idempotent (test + code: `upsertBuyerPii` no-ops and skips the audit/outbox/quote-drop when nothing changed); no money fields touched; en/es key parity confirmed.
- [x] Decisions recorded where needed — the report's "Decisions" section covers the stricter gate (also refusing `buying`/`voiding`), the row lock, requiring `city`, dropping stale quotes, and keeping the channel's email. All match what's in the diff.

## Optional notes (not blocking)
- CSV export has no dedicated permission beyond the page's `orders.read` gate (no `orders.export` permission exists in the contract). Given the export only reformats data already visible on the page the user can already see, and the card didn't ask for a stricter gate, this is fine — flagging so a future card can add one if buyer name in a downloadable file becomes a concern.
- `Person timeline`/shipment status strings are still server-side English (`en-12-after-void-released.png`'s shipment row) — the report already lists this as a known, pre-existing gap outside this card's owned paths (B-93-adjacent), not introduced here.
- The follow-up "explicit address-changed guard + re-check at buy time" is correctly deferred to the shipping owner (wave.md's build log already tracks it), not a gap in this card's own scope.
