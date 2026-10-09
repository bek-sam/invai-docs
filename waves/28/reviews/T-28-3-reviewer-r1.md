# Review of T-28-3 (round 1)

- Reviewer: reviewer on Fable 5.1
- Author: backend-engineer (privacy) on Opus 5.5. Reviewed invai-backend `dd4907e` only (T-28-2 commits in the same tree not judged) and invai-docs `4fc1bfe`.
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show --stat dd4907e` / `git show 4fc1bfe` | backend: 3 files, all `src/modules/privacy/**`; docs: `decisions/0026-*.md` + one README row. Nothing else. |
| `pnpm typecheck` (invai-backend) | exit 0 |
| `pnpm exec biome check src/modules/privacy` | 8 files, no diagnostics |
| `pnpm exec vitest run src/modules/privacy --reporter=dot` | 4 files, 23 passed, 1 expected fail (the untracked `security.test.ts` `it.fails`, S-56, security-reviewer's own file; not part of dd4907e) |
| `scan-test-weakening.sh invai-backend dd4907e~1` | 1 hit: `vi.mock("../../lib/audit")` in the new test (a dependency, used only to make one company's audit throw; not the unit under test). 0 assertions removed, 42 added. |
| Probe test (scratch worktree at dd4907e, deleted after): csv orders whose last run is `etsy`/`generic` format, `etsy` channel, Amazon orders 6 years old in `on_hold`/`ready_to_ship`/`new`/`needs_attention`, Amazon delivered placed exactly at the cutoff; two tenants; order/item/shipment row counts; audit row per tenant without order numbers; second run | 1 passed: every fence untouched, cutoff−1 s swept in both tenants, row counts unchanged, 1 counts-only audit row per tenant, second run 0 orders |
| Mutation proof on the author's test (same worktree): delete each of `inArray(orders.status…)`, `holdsAmazonDropData`, `isAmazonOrder`, `lt(orders.placedAt, cutoff)` from `amazonStale` | each one turns "clears only drop values…" red (fence snapshot mismatch ×3; `expected 3 to be +0` for the holds predicate). Full suite not re-run (decision 0019); the report's one failure is `rls-coverage` on `password_history` (T-28-2), noted only |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes (classification itself is compliance-officer's call) | 0026 keep/drop table covers every table the sweep touches; consumers of dropped columns traced: `channelListingId` only feeds `channels/sku.ts` listing learning (skips null) and the order view; `shippingMethod` only the order view and label rate; `listings.raw` has no production reader; `import_runs.file_key` is read only by live import runs |
| 2 | yes | service.ts `amazonStale.orders` = Amazon ∧ `placed_at < buyerPiiCutoff` ∧ status ∈ {shipped, delivered, cancelled}; test asserts drop values null/deleted, every other column incl. `updated_at` equal (`$onUpdate` overridden with `updatedAt: sql\`${t.updatedAt}\``), profit totals equal after recompute |
| 3 | yes | author's fences (17-month, open 30-month, partially_shipped, shopify, csv) + my probe (etsy/generic-run csv, on_hold, ready_to_ship, new, needs_attention, exact cutoff) + 4 mutations red |
| 4 | yes | `holdsAmazonDropData` on orders, `file_key <> '' or errors <> '[]'` on runs, `raw <> '{}'` on listings, delete on snapshots; `for update` + limit 500 per `withTenant` tx, `more` loop with a changed-nothing guard; `withSystem` reads ids only; try/catch per company (test: failing company rolled back, others swept, next run picks it up) |
| 5 | yes | dry-run test: counts equal twice, rows unchanged, no audit row, real counts equal dry counts |
| 6 | yes | `log.info` carries counts + cutoff; `log.error` carries companyId + error message; audit `data` = counts; tests and probe assert no order number in the audit row |
| 7 | yes | `service.test.ts`, `tenant.test.ts` unchanged in the diff and green |
| 8 | yes | README row is the only README hunk in `4fc1bfe` |

## Blocking findings
none
## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope (no schema, no order/item/shipment deletes, PII sweep untouched)
- [x] Tests exercise the behavior, and none were weakened (no `.skip`, loosened assertions, mocks of the unit under test, rewritten snapshots)
- [x] Tenancy (`withTenant` per company; `withSystem` ids-only with reason comment), idempotency (re-run 0), money untouched, no UI text
- [x] Decision 0026 recorded (proposed; compliance-officer and security-reviewer accept)

## Optional notes (not blocking)
- Import runs stuck in `pending`/`running` past 18 months keep `file_key`/`errors` (predicate filters completed/failed; S3 lifecycle covers the file). An Amazon file imported as `generic` format on a csv connection is not detected; worth one line in 0026. The nightly `withSystem` id scan runs four EXISTS subqueries over all orders (no index on `channel`); fine today, watch at scale.
