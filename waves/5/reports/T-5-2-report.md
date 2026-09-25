# Report: T-5-2 Channels and shipping settings
Author: web-engineer on Opus 5.5

```
Card: T-5-2  Owner: web-engineer  Scope ref: product/scope.md#mvp-in items 2, 7 (B-85, B-90, B-67 web half)
Owned (edit): invai-web routes/_app/settings/{channels,shipping}.tsx, routes/_app/shipping.tsx (void confirm),
  features/channels/**, own i18n keys, tests
Outside the card's list (flagged below): src/lib/nav.ts (+8 lines), src/routeTree.gen.ts (generated),
  shipping.tsx's old Settings tab (removed, redirects)
Risk flags -> co-reviewers: ui -> product-designer (plus reviewer)
```

## Commit (invai-web, `main`, not pushed)
| SHA | What |
|---|---|
| `a2566b2` | Channels and shipping settings: OAuth return, health, import history, stock push, void confirm (13 files, all mine; `git show --stat HEAD` checked) |

## Built
- **Channels, OAuth return** (`settings/channels.tsx`, `features/channels/status.ts`): the route reads `?connected=shopify&connectionId=` and `?error=`. It shows a translated banner: "connected" names the store and rings its card. Errors are sorted into expired, connected to another account, declined and generic, each with its own message; the server text never shows. The banner has "Connect again" and dismiss (dismiss clears the params).
- **Connection health** (`features/channels/connection-issues.tsx`): uses `channels.health`, falling back to the list's health. Issues show in plain language with a collapsible raw "Details":
  - token lost, and token retrying (T-3-1's refresh messages);
  - degraded webhooks (orders still arrive by the 10-minute poll);
  - stale (more than 30 minutes);
  - pending marketplace approval;
  - install not finished;
  - other sync errors.
  The badge says "Needs attention" whenever an explained issue exists, not only when `health.ok` is false.
- **Reconnect** for Shopify connections that are `pending` or `error`. It opens a "Reconnect Shopify" dialog with the domain filled in and restarts OAuth through `channels.connect`.
- **Stock-push opt-in** (T-3-3):
  - The switch sits on each API card, with what it does: on hand minus reserved, within 30 s, starting at the next change, mapped listings only.
  - It shows "Paused" when the store isn't connected or approved, and is hidden for CSV and pending connections.
  - A toast confirms each change and offers Undo.
  - The settings dialog no longer sends `pushAvailability`, so a stale copy can't overwrite the switch.
- **Import history** (`features/channels/import-history.tsx`): `channels.imports` per connection, 5 at a time plus "Show older imports". Each row has when, rows, new, updated, unchanged and failed. Status is Waiting to start, Importing, Done, "Done, some rows failed" or Failed. Rows with errors expand to the row errors. The list refetches every 3 s while an import is queued or running. The import dialog explains a queued (over 300 rows) import instead of showing zeros. History starts open for CSV connections.
- **Shipping settings** (new `settings/shipping.tsx`):
  - Carrier account shows "Test mode" or "Live", with what that means.
  - Ship-from address with autocomplete hints. Validation checks the required fields and a 5-digit ZIP.
  - Allowed carriers (USPS, UPS; the hidden test carrier "mock" is kept as saved); at least one is required.
  - Label format. ZPL shows as "coming soon", because labels are always bought as PDF today.
  - Package presets with translated labels: Length, Width, Height (in), Empty weight (oz), "Up to (items)", and "Use when nothing else fits". A new preset's name is translated.
  - Weight per style, picking the style from `blanks.facets` (free text if facets fail), with a duplicate check.
  - Batch strategy and tracking push.
  - Sticky Save. The page is read-only without `shipping.manage`.
- **Shipping page:** the old Settings tab and its hard-coded "L (in)" and "Poly mailer" editor are removed. A "Shipping settings" button goes to the new page, and `?tab=settings` redirects there. Nav: "Shipping settings" under Settings (`shipping.manage`).
- **Void confirm** (`shipping.tsx`, Shipments only; T-3-4's `Queue()` is untouched):
  - The dialog says the label is voided and that can't be undone from here, and the refund may show as pending.
  - It says only unscanned labels can be voided, and CSV-channel orders stay voidable until the scan.
  - It says that once tracking is sent to the channel, the order must be cancelled or refunded there.
  - If the row's tracking was already pushed, the dialog says so in red and only offers "Got it".
  - Errors are mapped: VOID_REJECTED (pushed, scanned or shipped, or refused), UPSTREAM_FAILED ("Void again to check"), CONFLICT. The success toast repeats the refund-pending note.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 OAuth return states | Yes | Mock Shopify connect in the browser returned `/settings/channels?connected=shopify&connectionId=b74f…` with the success banner; the `?error=` expired case is in `channels-oauth-error-en.png`; Reconnect on a pending install (created by curl, not completed) returned `connected=shopify&connectionId=c2ee…` |
| 2 Import history, health, Reconnect, stock-push toggle | Yes | Etsy CSV import in the browser gave the history row "6 rows · 4 new · 0 updated · 1 failed" with "Done, some rows failed" (`channels-import-history-en.png`). Token-lost issue and pending install with Reconnect: `channels-issues-en.png`. The toggle turned on with its toast and Undo. |
| 3 Shipping settings | Yes | Saved via the UI; DB copy afterwards: `allowed_carriers {usps,mock}`, `weight_per_style [{"weightOz":15,"styleCode":"BC3001"}]`, zip `85004`. Validation shown (required style, bad ZIP). `shipsettings-es-dark.png` |
| 4 Void confirm with the T-2-5 rules | Yes | Voided a labeled Etsy shipment through the dialog: shipment `voided`, label `voided`. The pushed Shopify label shows the blocked dialog (`void-pushed-en.png`). The backend answer for that case is `VOID_REJECTED` with `detail: "tracking was already sent to the channel"`, which maps to the same message. |
| 5 en/es, 390 px, keyboard | Yes, with a gap | Spanish and dark screenshots. At 390 px `scrollWidth` is 390 on both pages (`channels-es-390.png`); a style row overflow at 390 was found and fixed. Every control is a native button, input, select or `<details>`, and the icon buttons have aria-labels. No separate keyboard-only walk-through was run (token budget). |

## Checks I ran (invai-web, shared tree = exactly `a2566b2`)
| Command | Result |
|---|---|
| `tsc --noEmit` | no errors |
| `biome check .` | `Checked 124 files … No fixes applied.` |
| `vitest run` | 11 files, 66 tests passed (new `features/channels/status.test.ts`: 11) |
| `vite build` | `✓ built in 1.21s` |
| Golden-path E2E | **Not run.** The tech lead's token-budget instruction limits this card to unit tests plus my own flow. The golden path's step 2 selectors (`Import CSV`, dialog name, `#imp-conn`, `#imp-format`, "New orders", "Rows failed") are unchanged, and the same flow passed in my browser run. |

## Exercised for real
The API and worker ran on :3120 from a clean backend worktree at `1539d39`, with Redis db 2, DB copy `invai_t52_copy` (migrated) and imaging on :8120. Web ran on :5123. Screenshots were taken with Playwright, and I looked at each one.
- Mock Shopify OAuth, both from the page and through Reconnect on a pending install, landed back with the success banner. The `?error=` case showed the translated banner, and dismissing it cleared the params.
- CSV import (Etsy fixture) showed in the history. The stock toggle was switched on in the UI.
- Shipping settings were saved and checked in the DB (above). The void was checked in the DB (above).
- Refused cases, as presser: `PATCH shipping/settings` → 403 `FORBIDDEN` (shipping.manage); `PATCH channels/{id}` with `pushAvailability` → 403 `FORBIDDEN` (channels.manage).
- No console errors or failed requests in any scripted run (`errors: []`).
- The token-lost state was **simulated** by writing T-3-1's exact `last_error` text on the copy, because a real refresh failure can't be produced with mocks.

## Decisions
- **The settings editor moved out of `shipping.tsx`.** AC 3 forbids the hard-coded "L (in)" and "Poly mailer", which lived in that file's Settings tab, so it had to change. Keeping two editors would diverge. The tab is gone and `?tab=settings` redirects. Only `ShippingPage`'s tab list and the removed editor changed; `Queue()`'s batch code is untouched.
- **Health issues come from matching T-3-1's `lastError` wording**, because the contract has no issue code. Unknown text falls back to a generic translated line, with the raw text under "Details".
- **"Reconnect" is only for `pending` or `error` Shopify connections**, as the card says. For token problems on a `connected` store, the copy says to disconnect and connect again, because the backend refuses a new OAuth for a connected shop (see gaps).
- The ZPL label format is shown but disabled ("coming soon"): the backend always buys PDF.

## Known gaps and follow-ups
- **Backend: a Shopify connection in `error` (or `connected` with a lost token) can't restart OAuth.** `channels/service.ts` `connect()` throws `ALREADY_CONNECTED` unless the status is `pending` or `disconnected`. The dialog shows a translated "disconnect it first" message on that 409. Owner: integrations-engineer. Suggestion: let `connect()` re-issue OAuth for `error`, and for `connected` with `refreshError`.
- **`ConnectionHealth` has no structured issue code**, so the web matches message text. Owner: architect (add `issue: "token"|"webhooks"|…`).
- **Relative times from `@invai/ui` `RelativeTime` stay English in Spanish** ("6 hours ago"). This was already so before this card. Owner: product-designer.
- **Seeded connections have `lastImportAt` but no `import_runs`**, so "last import 6 hours ago" appears next to "No CSV imports yet".
- The void response doesn't say whether the refund is `refund_pending` or `voided`, so the copy always says it "may" show as pending.
- Label format ZPL isn't implemented in the backend.
- No keyboard-only walk-through, and no golden-path E2E run (budget).

## Outside owned paths
- `invai-web/src/lib/nav.ts`: one nav item "Shipping settings" (+8 lines). The new page is otherwise unreachable from the sidebar.
- `invai-web/src/routeTree.gen.ts`: regenerated by Vite for the new route (+21 lines).
- `scripts/i18n-es.json` and `scripts/i18n-extra-en.json`: my Spanish and the nav key, added by hand so a later `pnpm i18n` keeps them. `pnpm i18n` was not run.
- Keys I no longer use and left in place (harmless): `channels.pushAvailability`, `ship.maxUnits`, `ship.provider`, `ship.tare`.

## Blocked by other owners
- None blocking. See the backend `connect()` gap above.

## Screenshots (`invai-docs/waves/5/reports/T-5-2/`, 6 kept)
`channels-issues-en.png`, `channels-import-history-en.png`, `channels-oauth-error-en.png`, `channels-es-390.png`, `shipsettings-es-dark.png`, `void-pushed-en.png`.

## Processes and data
- Stopped: my API, worker, Vite (:5123) and imaging (:8120). Nothing is listening on 3120, 5123 or 8120.
- Dropped `invai_t52_copy`. Flushed Valkey db 2. Removed the worktree `../invai-backend-t52` and the scratch folder `invai-web/.t52`.
- Shared dev DB: untouched (used only as the copy template).
- Process note: my first API and worker start ran on the system Node 22, because PATH wasn't exported. I restarted them on Node 24, and every result above is from the Node 24 run.
