# Review of T-6-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer (+ backend-engineer inventory) on sonnet
- Verdict: approve

## Evidence I re-ran
Reviewed only this card's commits: `invai-contracts` `acbd294`, `57023f2`; `invai-backend` `55ea446`;
`invai-web` `13927c3`. Each repo checked in its own worktree next to the repos, checked out at that
exact commit (detached HEAD), with `node_modules` symlinked from the live repo and
`node_modules/@invai/contracts` re-pointed at a same-depth `invai-contracts` worktree pinned to
`57023f2`, so the check isolates T-6-1 from other cards' commits that share the same repos. All
review worktrees and the temporary re-link were removed at the end; the shared repos'
`node_modules/@invai/contracts` links are back at `../../../invai-contracts`.

| Command | Result |
|---|---|
| `invai-contracts`: `tsc --noEmit` | pass |
| `invai-contracts`: `biome check .` | pass, no fixes |
| `invai-contracts`: `vitest run` | 4 files, 31 tests passed |
| `invai-backend`: `tsc --noEmit` | pass |
| `invai-backend`: `biome check .` | pass, no fixes |
| `invai-backend`: `vitest run src/modules/inventory` (own test DB `invai_test_t61_r1`) | 7 files, 47 tests passed |
| `invai-backend`: `vitest run` (full suite) | 71 files, 498 tests passed — no regressions |
| `invai-web`: `tsc --noEmit` | pass (see note below) |
| `invai-web`: `biome check .` | pass, no fixes |
| `invai-web`: `vitest run` | 14 files, 76 tests passed |
| `invai-web`: `vite build` | succeeds (only a pre-existing >500kB chunk-size warning, unrelated to this card) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-contracts-t61-review acbd294~1` | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-t61-review 55ea446~1` | hits — read below, not blocking |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web-t61-review 13927c3~1` | no hits |
| New backend tests copied onto `55ea446~1` (base) and run in isolation (`mark-placed.test.ts`, `jobs.test.ts`) | all 6 fail against the base code (`markPlacedPo is not a function`) — proves they exercise the new behavior |
| Real pass on DB copy `invai_t61_r1_copy` (API :3191, `REDIS_URL` `/9`), signed in as `owner@desertbloom.test` | see criteria table |

Note on the web `tsc` run: a first pass showed a pre-existing, unrelated error in
`src/features/orders/order-actions.tsx` (not touched by this card) — a `Record<FlagCode, string>`
missing `channel_edit_after_press`. Tracing module resolution showed `@invai/contracts` was being
picked up through `invai-ui`'s own `node_modules/@invai/contracts` link (unaffected by my
per-worktree relinking), which still pointed at the live, ahead-of-wave-6 `invai-contracts` that
already carries later work adding that enum value. Once I pinned that link to the same `57023f2`
worktree for consistency, `tsc` was clean — confirming this was pollution from concurrent,
unrelated work, not a T-6-1 defect. I have restored that link (see the note at the end).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Manual PO (supplier, lines via variant search, qty, cost in cents) | yes | `PoFormDialog`; API pass created a draft PO for supplier `other`, line qty 25 at `unitCost: 639` cents, `subtotal: 15975` — integer cents throughout. Edit path gated on `po.status === "draft"` in `purchase-orders.$poId.tsx`. |
| 2. Mark placed manually (`markPlaced`, draft-only, idempotent) | yes | Contract stub matches `wave.md` verbatim. API pass: draft → `submitted` with `CALL-9981`; same-ref retry returned the same submitted row unchanged (safe no-op); different-ref retry on the now-submitted PO returned `409 INVALID_TRANSITION`. Backend tests cover the same three cases plus a cancelled-PO rejection. |
| 3. Receiving: web sends `idempotencyKey`; list/detail show `submitting`; 15-min stuck alert | yes | `purchase-orders.$poId.tsx` sends a stable `crypto.randomUUID()` per receipt, refreshed only after success (retries of a failed submit reuse the key). API pass: two identical receive calls with the same key produced exactly one `inventory_movements` row (qty 25) and one `purchase_order_receipts` row — verified directly in Postgres. `toPurchaseOrders` no longer masks `submitting` as `draft`; `po-safety.test.ts` updated to assert the real status. `stuckSubmittingPoJob` (`jobs.ts`) sweeps every 5 minutes and raises a `sync_broken` alert past 15 minutes in `submitting`, tested with a backdated `submitAttemptedAt` fixture (`jobs.test.ts`), not a live wait, matching the card's explicit instruction. |
| 4. Stock count (pick location, enter counts, preview diff, submit via `inventory.count`) | yes | `CycleCount` in `stock.tsx`. API pass: seed 20 + received 25 = expected 45, counted 30 → `variance: [{expected:45, counted:30, delta:-15}]`, one `count`-kind movement recorded. |
| 5. Inventory/supplier settings (account #, encrypted+masked API key, free-freight threshold, velocity/lead/safety days, `reserveOnImport`) | yes | `settings/inventory.tsx` never receives the key back (`apiKey` is write-only, `hasApiKey` drives the masked hint/remove button). API pass: `inventory.settings.get` always returns `apiKey: null`; after setting a key, `inventory.suppliers.list` shows `hasApiKey: true` and never the value; the DB row for `suppliers.api_key` holds `k1:<base64>` ciphertext (`encryptedText()` column, AES-256-GCM key-ring), not the plaintext I sent. This encryption/masking code predates this card (owned by an earlier wave) but the new UI correctly respects the write-only contract. |
| 6. Quality: en/es, 390px, keyboard, loading/empty/error states | yes | Every en key added has a matching es key (diffed key sets, no mismatch). New screens reuse `SkeletonRows`/`ErrorState`/`EmptyState`/`Field`/dialogs already used elsewhere at 390px; no raw hardcoded English strings found in the new JSX (checked via diff grep). Not independently re-tested at 390px in a live browser (relying on shared, already-audited components plus the code read); no visual regression indicated by the diff. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`): contracts touches only `src/contract/inventory.ts` and `src/schemas/inventory.ts` (own-diff, isolated from the same-day `production.ts`/`states.ts`/etc. stubs other cards added around it); backend touches only `src/modules/inventory/**`; web touches `features/inventory/**`, `routes/_app/inventory/**`, the new `routes/_app/settings/inventory.tsx`, `src/i18n/{en,es}.ts`, the generated `routeTree.gen.ts`, and one line in `src/lib/nav.ts` to link the new settings route (not in the card's listed globs, but a single additive nav entry needed to reach the route the card was asked to build — see optional note).
- [x] Nothing outside scope: no unrelated refactors; the `po-safety.test.ts` change is a direct, intentional consequence of AC3 (masking removed), not scope creep.
- [x] Tests exercise the behavior, and none were weakened: scan script flagged the `draft`→`submitting` assertion change (explained above, not a weakening — it's checking the new, correct value) and the `if (!env.isTest)` scheduler guard in `jobs.ts` (an existing repo-wide pattern used identically in `channels/billing/finance/shipping/orders/today` jobs, not a T-6-1-specific dodge). New tests were confirmed to fail against the pre-change code.
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text: `markPlacedPo`/`blankLabels`/`stuckSubmittingPos` all run inside `withTenant`; no new tables added (only two nullable-safe additions elsewhere, and this card adds no schema at all — pure logic + query changes); idempotency verified for both `markPlaced` (state-transition no-op) and `receive` (movement/receipt row counted once); money stayed in integer cents end to end (639, 15975); en/es parity confirmed.
- [x] Decisions recorded where needed: none required; this is additive per `wave.md`'s contract-stub note (no deprecation process triggered).

## Optional notes (not blocking)
- `src/lib/nav.ts` (one entry, `inventorySettings`) and `src/routeTree.gen.ts` (auto-generated) are outside the card's literal glob list (`routes/_app/inventory/**`, `features/inventory/**`, the inventory settings route). Wiring the new settings route into nav is a reasonable, minimal, low-risk necessity rather than scope creep, but future cards should ask for an explicit one-line grant the way T-6-2 did for `badges.tsx`, to keep ownership boundaries clean.
- The report claims "4 screenshots saved" for the browser pass, but no screenshot files exist anywhere under `invai-docs/waves/6/reports/T-6-1/` (the directory only contains `T-6-1-report.md`) or elsewhere on disk that I could find. I did my own real pass on a DB copy instead (documented above) and got the same outcomes the report describes, so this doesn't block, but the missing screenshots should be logged so the author knows they didn't actually land.
- Housekeeping: mid-review, re-pointing `invai-contracts` symlinks for isolation briefly and mistakenly touched the *shared* repos' `node_modules/@invai/contracts` links (not just my worktrees) — `invai-backend`, `invai-web`, and `invai-ui`. All three are confirmed restored to `../../../invai-contracts` before finishing this review. No `pnpm` install/dedupe was run in any worktree; only `node_modules/.bin/*` binaries were invoked.
