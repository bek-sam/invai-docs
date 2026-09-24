# InvAI v1 QA report

As of Sep 24, 2026, 07:45 CDT. QA / integration engineer (Claude Fable 5.1). Everything below was
run against the real stack on this machine: api :3000 + worker, imaging :8000, web :5173, floor
:5174, a freshly seeded dev database (`pnpm db:reset && pnpm db:migrate && pnpm db:seed`).

## 1. Golden path

Each step was driven twice: through the browser (Playwright, `invai-web/e2e/golden-path.spec.ts`,
tablet steps in `invai-floor/e2e/press.spec.ts`) and through the API alone
(`invai-web/e2e/api-golden-path.spec.ts`). Final runs on a fresh seed: API 13/13, browser 13/13
(steps 1-3 in one run, 4-13 continuing from that state after a locator fix), screens smoke 2/2,
tablet 1/1.

| # | Step | Browser | API | Notes |
|---|---|---|---|---|
| 1 | Owner signs in, Today shows real numbers | pass | pass | Tiles match `today.summary` |
| 2 | Etsy CSV import via Settings > Channels, orders in Orders with ship-by | pass | pass | Fixture `etsy-sold-order-items.csv`: 4 orders, 1 broken row reported, re-import is idempotent (`ordersSkipped`) |
| 3 | Unmapped SKU mapped in the order drawer with "save rule", item ready | pass | pass | Rule saved; "Needs mapping" tab now uses `orders.list.itemState` |
| 4 | Personalized item: proof visible, approve | pass | pass | Proof rendered by the worker after import (imaging `/render/personalization`) |
| 5 | Gang sheets: preview, build, progress, sheet with preview image, utilization >= 80% | pass | pass | Full 22x240 in sheets nest at 88.5-90.7 % (was 51.7 %); a short overflow sheet can be below 80 % and is not judged |
| 6 | Send to vendor; vendor signs in, inbox, acknowledge, printed, shipped | pass | pass | Vendor opens Shops first (accepts the invite per the security follow-up) |
| 7 | Owner marks received, items `transfer_in` | pass | pass | |
| 8 | Floor: station token, PIN 1155, press scan `T:` + `B:`; wrong blank BLOCKED, right blank PRESS, QC pass, pack | pass (tablet suite) | pass | Tablet suite pairs an "any station" tablet (the seeded Press 1 token is pinned to press, so it cannot switch to QC/pack); wrong style -> "Wrong style", wrong size -> "Wrong size" |
| 9 | Shipping: rates, buy label (mock carrier), PDF, tracking push, items shipped | pass | pass | Etsy is a CSV connection, so tracking push resolves to `not_required` (manual upload) rather than `pushed`; the PDF is verified by content type through the API (headless Chromium downloads PDFs instead of rendering them) |
| 10 | Analytics: profit for the order and its design | pass | pass | |
| 11 | AI listing draft (mock) -> Etsy validation -> approve; trademark "Just Do It Nike shirt" -> high | pass | pass | Draft state after generation is `needs_review` |
| 12 | Assistant answers "what was my TikTok margin this week?" (streamed) | pass | pass | Event iterator: `start`, several `text_delta`, `done` |
| 13 | Tenant isolation: a second company sees none of Desert Bloom's data | pass | pass | Orders/designs empty, Today zero, foreign order and sheet ids are NOT_FOUND |

Every web screen (27 routes + order, sheet, design, template and PO detail pages) was opened as the
owner, and the vendor portal as the vendor, with console errors and failed / 4xx-5xx requests
captured: none remain (`e2e/screens.smoke.spec.ts`).

## 2. Bugs found and fixed

Backlog items from v1-plan section 6 are marked with their number.

| Repo | File | Fix |
|---|---|---|
| invai-contracts | `src/schemas/production.ts` | (#15) `wrong_style` added to `MISMATCH_REASONS` |
| invai-backend | `drizzle/0004_print_size_numeric.sql`, `src/db/schema/orders.ts` | (#1) `print_width_in` / `print_height_in` were integer columns; now double precision |
| invai-backend | `src/modules/orders/mapping.ts`, `src/modules/orders/service.ts` | Mapping and artwork overrides no longer `Math.round` inches |
| invai-backend | `src/db/seed/data.ts`, `src/db/seed/index.ts` | (#14) Realistic print-size mix: 10.5x12 adult fronts, 8.5x9.5 youth, 3.75 in left chest, 3x10 sleeves, 12x14 backs, with sample art rendered at those sizes and matching placements; templates 10.5x12 |
| invai-backend | `src/db/seed/index.ts` | (#10) Opening stock now covers every consumed and reserved unit, so no blank has negative on-hand (9 blanks stay under their reorder point on purpose) |
| invai-backend | `src/db/seed/index.ts` | Personalized artwork keys pointed at files that did not exist; the seed renders the 49 proofs through imaging (proofs open, sheets compose) |
| invai-backend | `src/db/seed/index.ts` | Seeded gang sheets pointed at PNG/preview keys that did not exist (broken image, `ERR_BLOCKED_BY_ORB` on the sheet page and in the vendor portal); open sheets are composed for real, received ones keep no file; seeded transfers are laid out from the real sizes |
| invai-backend | `src/modules/production/jobs.ts` | (#3) Production subscribes to `order.cancelled` and scraps the cancelled items' nested transfers (`scrapTransfers`); test in `production.test.ts` |
| invai-backend | `src/modules/production/matcher.ts` | (#15) A different garment style is `wrong_style` (was reported as `wrong_design`) |
| invai-imaging | `app/nesting.py` | Utilization was 52-63 % on the realistic mix: every MaxRects heuristic rotated a 10.5x12 in front into 12 in wide on 22 in film, which nests one per row. Nesting now also tries "upright only" and "most copies across the width" orientation policies and keeps the best; 16 fronts nest two-up at 90.7 % |
| invai-imaging | `app/sample_art.py` | `/sample-art` returned 500 for the "stars" style on tall narrow art (3x10 in sleeve): star band clamped to the width |
| invai-web | `src/features/orders/views.ts` | (#13) "Needs mapping" / "Needs artwork" tabs filter by `itemState` instead of `status: needs_attention` |
| invai-web | `src/routes/_app/orders/index.tsx` | `?q=3310000001` (an order-number search in the URL) was parsed as a JSON number by the router and dropped by `z.string().catch(undefined)`; coerced to a string |
| invai-web | `src/routes/_app/production/stations.tsx` | Stations board recomputed the staff-output query key on every render, so every live update refetched and aborted the previous request (`ERR_ABORTED` in the console) |
| invai-web, invai-floor | `src/i18n/{en,es}.ts`, `src/scan/result.ts`, `src/stations/PressStation.tsx` | (#15) `wrong_style` strings in English and Spanish; the offline press check reports it too |
| invai-floor | `vite.config.ts` | Vitest picked up the Playwright spec; tests are limited to `src/**/*.test.*` |

Commits (branch `platform-v1`, nothing pushed): contracts `a5e7f45`; backend `a061c46`,
`4b99635`; imaging `951228d`; floor `9e7d239`, `48a6a27`; web `2c25ac4` + the E2E follow-up.
Backend commits touch only QA-owned paths; the security reviewer's migration `0005` sits on top of
`0004_print_size_numeric` in the journal, and `db:reset && db:migrate && db:seed` runs clean from
scratch.

## 3. Remaining known issues (by severity)

1. **Intermittent 403 on the browser's presigned CSV upload** (medium). Twice in ~10 runs MinIO
   answered `SignatureDoesNotMatch` to the browser's PUT while the same upload passed seconds
   later and always passes from Node. The signature now binds `content-length` (security review,
   `src/lib/s3.ts` `presignPut`); a browser that omits or changes that header would fail exactly
   this way. Not reproduced under instrumentation. The E2E logs the storage error body and retries
   the import once. Suggested hardening (reviewer's file, not changed): stop signing
   `content-length` and enforce the size with `headObject` after the upload.
2. **A presser cannot use the Quality check or Pack stations from a press-kind tablet** (low, by
   design). Station kind is fixed per token; only "Any station" tablets switch. The seed only
   issues a "Press 1" token, so a demo of QC/pack on the tablet needs a token from Settings >
   Stations for QC 1 / Pack 1 (or an any-kind station). The tablet suite pairs one through the API.
3. **`blanks.list` needs `catalog.read`, which pressers lack** (low). The floor app does not call
   it, but any future floor screen that looks up blanks by code will need `auth: "floor"` plus a
   permission pressers have.
4. **Etsy/Amazon/TikTok/Walmart tracking push is `not_required`** (accepted for v1). Only the
   Shopify (mock) adapter pushes; CSV channels point the user at a manual upload.
5. **Short overflow sheets can nest below 80 %** (cosmetic). The last sheet of a batch holds the
   leftovers (12-88 in long); the E2E only judges sheets of 100 in or more.
6. Backlog items left open as accepted in v1-plan: #11 (AI publish falls back to CSV), #12
   (`get_production_status` tool name), #16 (vendor accept flow is "open the shop list"), #17
   (`blankReusable` on QC fail), #18 (restart processes before E2E).
7. Worker log noise after a process restart: BullMQ "could not renew lock" for a
   `finance.recompute` job interrupted by the restart, and `catalog.runDesignQa` retries that
   failed against imaging while it was being restarted. Both clear on their own.

## 4. How to run the E2E suites

```
# infra + api + worker + imaging + web + floor (or invai-infra/scripts/dev.sh)
cd invai-backend && pnpm db:reset && pnpm db:migrate && pnpm db:seed   # imaging must be up: the seed renders art

cd invai-web
pnpm e2e                                   # browser golden path + every-screen smoke (chromium, ~1 min)
E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts   # API-only golden path (~10 s); run on a fresh seed, it
                                                  # consumes the same imported orders as the browser path
pnpm e2e:ui                                # Playwright UI mode

cd invai-floor
pnpm e2e                                   # tablet: pair, PIN, press scan check, QC pass, pack (~3 s)
```

- Both golden paths expect a **freshly seeded** database; the browser one tolerates a re-run on
  the same database (steps already done are skipped and verified through the API).
- Playwright needs the Chromium build matching `@playwright/test` (`pnpm exec playwright install
  chromium` once). Reports land in `e2e/.report`, traces and screenshots of failures in
  `e2e/.results` (both git-ignored).
- `E2E_WEB_URL`, `E2E_API_URL`, `E2E_FLOOR_URL` override the default local ports.
- Helpers: `invai-web/e2e/helpers/api.ts` (cookie session + typed oRPC client, station and floor
  sessions, uploads, polling), `invai-web/e2e/helpers/ui.ts` (login, console/request watcher),
  `invai-floor/e2e/helpers/api.ts`.

## 5. Repo checks at hand-off

`pnpm typecheck && pnpm lint && pnpm test` pass in contracts (31 tests), ui (20), backend (148),
web (23, plus `pnpm build`) and floor (41, plus `pnpm build`); imaging `uv run ruff check . && uv run
pytest` (27). The dev database was reset, migrated and seeded last, and every app process was
stopped; only the Docker infra (Postgres, Valkey, MinIO, Mailpit) is left running.
