# Review of T-7-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: integrations-engineer + web-engineer on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-contracts` (main, already at `7412d89`): `node_modules/.bin/tsc --noEmit && node_modules/.bin/biome check . && node_modules/.bin/vitest run` | pass (4 files, 31 tests) |
| `invai-backend` worktree @`24b6790`: `node_modules/.bin/tsc --noEmit` | clean |
| same: `node_modules/.bin/biome check .` | Checked 46 files, no issues |
| same: `node_modules/.bin/vitest run` (full suite, own test DB `invai_test_review71`) | **1 failed / 525** — `src/modules/shipping/export-tracking.test.ts:111`, `expect(again.count).toBe(0)` got `1` |
| same: `vitest run src/modules/shipping/export-tracking.test.ts -t "re-export with since=null"` ×4 | fails deterministically every time when run alone (not flaky-by-parallelism; reproducible) |
| `invai-web` worktree @`073c53f`: `tsc --noEmit`, `biome check .`, `vite build`, `vitest run` | all clean/pass (76 tests, build OK) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` / `invai-web ...` / `invai-contracts ...` | hits exist but all belong to other cards' commits already on local `main` (T-6-x/T-7-2/T-7-4); nothing in T-7-1's own diff removes or loosens an assertion |
| DB-copy live exercise: `invai_t71_review_copy` (copy of dev `invai`), API on `:3194` (`REDIS_URL=/12`), web on `:5194`. Signed in as `owner@desertbloom.test`, inserted 2 labeled Etsy shipments directly, then `POST /api/v1/shipping/exports/tracking {channel:"etsy", since:null}` over curl | `count:108` (2 mine + 106 seed), downloaded the MinIO object: header `receipt_id,tracking_code,carrier_name,note_to_buyer,send_bcc`, both my orders present, correct Etsy shape |
| Same call repeated immediately (curl) | **`count:1`**, not `0` — a shipment was re-exported that should not have been |
| Web: clicked "Export tracking for Etsy" once on the Shipping → Tracking push tab (already primed from the curl calls above) | toast read **"1 shipments exported for Etsy"** instead of "Nothing new to export" — same bug visible in the UI |
| Cleanup | dropped `invai_t71_review_copy` and `invai_test_review71`, flushed Redis db 12, killed the API/web processes, removed both worktrees |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Export files per CSV channel, marketplace's own format, carrier mapping | Yes | `tracking.ts` builders + `tracking.test.ts` fixtures for Etsy/Amazon/TikTok/Walmart; `Record<Carrier,string>` per marketplace is exhaustive over the 3-value `Carrier` type (compiler-enforced, no missing case); live download confirmed Etsy header/rows |
| 2. `exported_at` marks shipments, re-export possible | **No** | Marks correctly on first run, but re-export is not idempotent — see blocking finding 1. "Nothing new" (AC's implicit "re-export just re-runs the query") fails both under test and live |
| 3. Web export button with count, file downloads, en/es hint | Partially | Button, count, download all work (verified live). But two of the four per-channel hint strings are not translated — see blocking finding 2 |
| 4. Fixtures for each format | Yes | `tracking.test.ts` (9 tests) covers all 4 formats + CSV-injection guard; `export-tracking.test.ts` (5 tests, 1 failing) covers the DB-backed query |

## Blocking findings
1. `invai-backend/src/modules/shipping/service.ts` (`exportTracking`, the `cutoff`/`gte(shipments.labeledAt, cutoff)` logic) — re-export is not idempotent because the cutoff and the value it's compared against come from two different clocks. `cutoff` is `max(shipments.exportedAt)`, stamped by the **Postgres server's** `now()`; it's compared against `shipments.labeledAt`, stamped by the **application host's** `new Date()`. Direct inspection of the review DB copy showed a shipment with `labeled_at = 06:18:23.870` and `exported_at = 06:18:23.843947` — i.e. `exported_at` **26ms before** `labeled_at`, on the very row the export itself had just stamped. When that happens, the next call's `cutoff` sits below that shipment's `labeledAt`, so it matches `labeledAt >= cutoff` again and is re-included, re-uploaded, and re-marked. Reproduced at three layers: the unit test (`export-tracking.test.ts:111`, deterministic on every standalone run), a live HTTP round trip (`POST /shipping/exports/tracking` immediately repeated returned `count:1` instead of `0`), and the web button (clicking "Export tracking for Etsy" once, having just exported, produced the toast "1 shipments exported for Etsy" instead of "nothing new"). Concrete failure: a shop clicks the export button twice (or retries after a slow network response, or the button is double-clicked), and Etsy receives the same tracking number uploaded a second time through whatever bulk-upload connector consumes the file — and every subsequent export can pick up that same shipment again, since its `exportedAt` never advances past its own `labeledAt`. Per the tech lead's note (T-7-3 saw the same failure on a clean checkout — not caused by my environment): this is a real bug, not flakiness from parallel test workers. Fix: don't compare a DB-stamped timestamp against a host-stamped one. Compute both `exportedAt` and the value used to build the *next* `cutoff` from the same clock in the same request (e.g. capture `const asOf = new Date()` once in the handler and use it for both the `UPDATE ... SET exported_at = ${asOf}` and as what a following export's cutoff will read back), or store/compare using a monotonic sequence instead of wall-clock time. Tests should pin the clock (`vi.useFakeTimers()` / an injected `now()`) rather than relying on real elapsed time between two calls.
2. `invai-web/src/i18n/es.ts` (`shipping.exportWhere.amazon`, `shipping.exportWhere.tiktok`) — both strings are byte-for-byte identical to `invai-web/src/i18n/en.ts`'s versions ("Amazon: Seller Central → Orders → Upload Order Related Files → Shipping Confirmation." and "TikTok Shop: Seller Center → Orders → Manage orders → Upload → Add Tracking No."), i.e. raw, untranslated English shipped in the Spanish locale. The Etsy and Walmart hints in the same object *are* translated, so this isn't a placeholder pattern — it's a miss on exactly 2 of 4 channels. Failure scenario: a Spanish-locale shop owner selects "Amazon" or "TikTok Shop" in the export picker and gets an English paragraph telling them where to upload the file, breaking the card's own AC3 ("Short instructions (en/es)") and the repo-wide "no raw English" rule.

## Checks
- [x] Only owned paths changed (`git diff --stat` on each of the 3 commits: contracts `src/schemas/shipping.ts`; backend `integrations/channels/exports/**`, `modules/shipping/{router,service}.ts` + tests, `integrations/channels/pending.ts` copy-only touch per the card's clarification; web `routes/_app/shipping.tsx`, `i18n/{en,es}.ts`) — matches owned paths and the `db/schema`/contracts grants from `wave.md`.
- [x] Nothing outside scope.
- [ ] Tests exercise the behavior, and none were weakened — the export-tracking re-export test itself is correct and catches the bug (good test); no weakening found in T-7-1's own files via the scan script; but the test currently **fails**, which is the blocking finding above, not a test-quality issue.
- [x] Tenancy: `exportTracking` runs inside `withTenant(tenant.companyId, ...)`; `exportedAt` is a new nullable column on the existing `shipments` table (already `company_id` + RLS), not a new table — no new RLS surface to add.
- [ ] Idempotency: intended (re-export is explicitly called out as safe in the stub) but is not, under the clock-source bug above — blocking.
- [x] Money in cents: n/a, no money fields touched.
- [ ] en/es text: Etsy/Walmart hints translated; Amazon/TikTok hints are raw English — blocking.
- [x] Decisions recorded where needed: the `trackingPushStatus='manual'` deviation is documented in `service.ts` and the report; I verified it does **not** leak Shopify or already-`pushed` orders — the query joins on `orders.channel = input.channel`, and `input.channel` is gated to the 4 CSV-only channels by `isTrackingExportChannel`/`NOT_CSV_CHANNEL` before the query ever runs, and a real `pushed` status is architecturally impossible for a `pendingApproval` adapter (confirmed against `pending.ts`). No cross-contamination.

## Optional notes (not blocking)
- CSV injection: `neutralizeFormula` is applied in both `toCsv` and the Amazon `toTsv` path and is unit-tested (`tracking.test.ts`, formula-injection case) — good.
- Etsy/TikTok/Walmart column names are the author's best-effort reading of public docs (the live Seller Center templates are login-gated); already flagged transparently in the report as a follow-up. Reasonable to accept as-is.
- Web copy: the success toast says "1 shipments exported" (should be singular for n=1) — a small `t("...", {count: n})`-style pluralization miss, not blocking.
- The author's report correctly disclosed "no live HTTP exercise" as a known gap; I closed it (see Evidence table). Note for the tech lead: OrbStack's Docker daemon went down mid-review (`docker.sock` missing) and I was denied permission to restart it (classified as interfering with shared workloads); the tech lead restarted it and I resumed and completed the live exercise on the same DB copy without needing to redo the DB setup.
