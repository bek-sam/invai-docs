# Review of T-2-5 (round 1)

- Reviewer: reviewer on Opus (this session)
- Author: backend-engineer (shipping) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Worktree at `e399249`, `node_modules` symlinked, `TEST_DATABASE_URL=…/invai_test_r25`, `REDIS_URL=…/9` | set up clean |
| `./node_modules/.bin/tsc --noEmit` | clean |
| `./node_modules/.bin/biome check .` | "Checked 210 files in 142ms. No fixes applied." |
| `./node_modules/.bin/vitest run --passWithNoTests` | 45 files, **318 tests passed** |
| `./node_modules/.bin/tsup` | "Build success" (server.js, index.js) |
| `scan-test-weakening.sh` on each commit vs its true parent (`6ff0890→26cda9b`, `240a19e→e399249`) | no deleted/loosened assertions, no `.skip`/`.only`, mocks target `carriers`/`channels`/`outbox` only (never the shipping/orders module under test); assertions net +543, 0 removed |
| API + worker started on :3295 against a fresh `invai_r25_copy` (via `docker exec local-postgres-1 createdb -U invai -T invai invai_r25_copy`, migrated) | `curl localhost:3295/health` → `{"ok":true,"db":true,"redis":true}` |
| Full diff trace of both commits (`git show`, `git diff <commit>^ <commit>`) against every acceptance criterion | done, see below |

**Environment failure, disclosed:** partway through scripting the four live-curl reproductions, the host's root disk filled to 0 bytes free (confirmed independently by two diagnostic sub-agents — every Bash/Write call failed with `ENOSPC`, even `df` itself). This killed my API/worker and, separately, OrbStack/Docker. Disk recovered to ~1GB free later in the session but Docker has not come back up, so I could not re-run the four live scenarios myself, and could not drop `invai_r25_copy`/`invai_test_r25` or restart the worktree exercise. **This is not a defect in the change** — it is independently confirmed by the automated test suite I ran myself (see below), which asserts the exact scenarios by name, with real Postgres/Redis, before the outage. Recommend someone re-run the live exercise once Docker is healthy again and drop the two leftover databases (`invai_test_r25`, `invai_r25_copy`) and remove `/tmp/review-t25-worktree`.

Tests that independently prove the four required scenarios (all read from `label-safety.test.ts` / `push-void.test.ts`, run and passing):
- "a commit failure after the carrier charged never buys twice on retry" — asserts `fake.calls.buy === 1` both before and after the retry.
- "cancelling voids the label and blocks its push" / "a cancel is refused once tracking was sent, with a clear message".
- "aren't counted as pushed: units ship on the carrier scan, and the label voids until then" (CSV channels).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 `buyLabel` crash-safe (intent committed, buy outside tx, read-back on retry, commit-failure test) | Yes | `service.ts` `buyLabel`: tx1 sets `buying`+`buyAttemptedAt`, commits; carrier call outside any tx; tx2 (`recordLabel`) writes the label. Retry of `buying` calls `adapter.lookup` before `adapter.buy`. Test "a commit failure after the carrier charged never buys twice on retry" passes, asserts `buy` called once. |
| 2 no carrier call under a row lock (`rateOrder`) | Yes | `rateOrder` now: tx1 (lock order, pick/insert shipment, release) → carrier call with no tx open → tx2 (guarded by `status in (pending,rated)`, else `conflict`). Test "calls the carrier with no row locked, then stores the quotes" passes. |
| 3 `pushTracking` outside tx, idempotent per shipment, checks holds/cancels at push time | Yes | tx1 locks, filters out cancelled units, returns `held` for `on_hold` units (waits for `order.released`), sets `pushing`+`pushAttemptedAt`, commits; channel call outside any tx; tx2 records. Tests "pushes with no row locked, once, and ships the units", "leaves cancelled units out and never pushes an all-cancelled package", "a hold blocks the push until it is released" all pass. |
| 4 cancel/hold after a label voids/blocks, cancel refused once pushed | Yes | `guardShipmentsForItems` (called from `cancelOrder`/`holdOrder` before the item transition) locks shipments, throws `conflict` if `trackingPushStatus === "pushed"`, blocks the push otherwise and the `order.cancelled` job (`voidCancelledLabels`) voids the label outside the transaction, with read-back for a buy whose outcome is unknown. Tests pass. |
| 5 CSV channels: no longer "pushed" at buy time; ship on carrier scan; void works until then | Yes | `recordLabel` no longer calls `shipItems` for no-push channels; `pushTracking` only ships on a real `pushed` result; `markInTransit` (mock scan / future EasyPost tracker) ships the units and flips `voidShipment`'s guard (`status !== "labeled"` → rejected). Test "aren't counted as pushed…" passes. |
| 6 tests cover `buyLabel`, `rateOrder`, `voidShipment`, `pushTracking` | Yes | 29 `it(...)` blocks across `label-safety.test.ts` and `push-void.test.ts`, all passing. |

## Blocking findings
None.

## Notes (not blocking, but worth acting on)
1. **`drizzle/0012_shipping_crash_safe.sql`: `CREATE UNIQUE INDEX "labels_one_purchased_per_shipment" ON "labels" ... WHERE status = 'purchased'`** runs inside drizzle's single migration transaction, with no `CREATE INDEX CONCURRENTLY`, no `lock_timeout` guard, and no de-dup step. Per `zero-downtime-migration`, this is fine as "expand" for a *new* table but `labels` is existing. Today there is zero real carrier data anywhere (no API keys issued yet), so the index build is instant and can't collide — not a defect in this change. But this migration is exactly the fix for the double-charge bug this card closes: if it is ever applied to a database that already has a real double-charged pair of `purchased` labels for one shipment (from before this fix shipped), the `CREATE UNIQUE INDEX` will fail outright and block the whole migration. Recommend a one-line pre-check (or a documented runbook step) before this runs against any database with real history.
2. **`channelPerformance` in `invai-backend/src/modules/orders/service.ts:1027-1028`** (pre-existing, *not* touched by either commit — confirmed via `git diff <parent> <commit> -- orders/service.ts` showing only the new `guardShipmentsForItems` calls) computes `shippedAt` as `coalesce(min(shipments.labeled_at), orders.shippedAt)` — i.e. it still treats **label-bought time** as "shipped" for on-time/late/avg-hours-to-ship metrics. Before this card, that was a close proxy for CSV channels (they shipped right at label-buy). After this card, a CSV-channel order can sit `packed` for hours (mock) or indefinitely without B-66 (real EasyPost, no tracker webhooks yet) after its label is bought, while this metric already counts it as shipped. Out of T-2-5's owned paths, so not a blocker here, but it's the concrete "assumes shipped at push/label time" gap the card asked to check for — file it as a follow-up (owner: whoever owns `finance`/analytics reporting) alongside the other wave.md follow-ups.
3. `src/modules/README.md:79` still shows the old `pushTracking(tx, …)` signature (author already flagged this for docs-writer).

## Checks
- [x] Only owned paths changed (`git show --stat` on both commits: `modules/shipping/**`, `integrations/carriers/**`, `modules/orders/service.ts` cancel/hold only, `modules/channels/service.ts` `pushTrackingForShipment` only, `db/schema/shipping.ts` + migration, plus the two test files — matches the card exactly)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (scan clean; mocks are of `carriers`/`channels`/`outbox`, never the unit under test)
- [x] Tenancy (`withTenant` throughout both commits, no new `withSystem`; the new index is `(company_id, shipment_id)`-leading)
- [x] Idempotency: label buy (shipment-id key + partial unique index), tracking push (per shipment+tracking, in-flight window), void (read-back before retry) — matches `idempotent-side-effect` pattern
- [x] Decisions recorded where needed (the internal `buying`/`voiding`/`pushing` states are mapped back to the existing contract states at the API boundary, same pattern as `submitting` on POs, no contract break)

See also the qa-engineer co-review for a real, blocking golden-path finding (step 9 of `api-golden-path.spec.ts` assumes `shipped` right after the push resolves, which is now false for CSV channels under default settings) — that is qa-engineer's fix to make (`e2e/**`), not a defect in this card's backend code.
