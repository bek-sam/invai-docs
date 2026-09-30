# Wave A1: analytics v2, the data and read services (B-168..B-172)

- Dates: started 2026-09-30 00:05 CDT. Runs next, before waves 24/25 (paused until the owner starts AWS, decision 0019) and before the rest of 23b (T-23-3, T-23-4), as the PM ranks them.
- Goal (user outcome): a shop owner can get, from InvAI's API, true unit economics, losing orders, leakage, shipping margin, operations waits and inventory health on 18 months of realistic seed history. Screens come in A2.
- Spec: `specs/business-analytics-v2.md` (Tracks A–C). Scope check: `waves/analytics-scope-check.md` (PM, 2026-09-28: fits scope items 5–8, 13, 14, 17).
- Plan reviewed by: product-manager (2026-09-30, scope confirmed, see below); architect (2026-09-30, `reviews/wave-plan-architect.md`: approve-with-changes; all 3 blocking and 2 other findings applied to T-A2..T-A5 the same day).

## Spec status (product-manager, 2026-09-30): **ready**
- Scope confirmed (open question 1 in the spec, `waves/analytics-scope-check.md`): B-168..B-177 fit items 5, 6, 7, 8, 13, 14, 17; Track D (B-178..B-181) stays gated on OI-18.
- product-designer and qa-engineer reviews run (`waves/A1/reviews/business-analytics-v2-{product-designer,qa-engineer}.md`), both **changes-required**; all 8 blocking findings (combined: 4 unique + overlap on D10-D13) fixed directly in the spec — new AC-Seed1, AC-C5, AC-B/C-screen1, AC-E1b..E1f, AC-G1 rewritten for an unambiguous period/filter, AC-A3 and AC-E2 extended for their zero-data states. Spec's own review log has the detail.
- customer-success evidence review not run separately this round (2 short reviewers max, per instruction); evidence already cited in the spec is the owner's direction plus research pain #1/#5/#6/#7/#8 — flag to customer-success once pilots are live.
- Full task cards are now written: `waves/A1/T-A1-analytics-seed.md` .. `T-A5-inventory-design-analytics.md`.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-A1 Analytics-ready seed (B-168, absorbs B-130) | backend-foundation | sonnet | reviewer (opus) | golden path | building: scratch seed on `invai_ta1` finished in 543 s (1326 orders); run 4 (07:48) does the AC-Seed1 counts, API golden path, `market-demand.test.ts` timeout, commit |
| T-A2 `analytics.*` contract (B-169) | architect | fable | reviewer (opus) | contract | **approved r1** (contracts f466088, backend 9228343). AC5 deviation accepted: `channel?` only on the 7 sales-based reads. `supplierTrends.avgUnitCost` fractional cents accepted as a documented derived average. |
| T-A3 Finance analytics service + `fixed_monthly_cents` migration (B-170) | backend-engineer (finance) | opus | reviewer (opus) + backend-foundation (migration), security-reviewer (tenancy) | tenancy, migration, money | **reviewer approved** r1 (95e9d69, 1afdfc3, 31db7f3) and r2 (8c616ef, zone grouping on `dest_zone`); **security approved** r1; **backend-foundation (migration) approved**. `analytics/finance-testkit.ts` acknowledged inside the `finance*` split |
| T-A4 Operations and shipping analytics + `shipments.dest_zone` (B-171) | backend-engineer (production, shipping) | opus | reviewer (opus) + backend-foundation (migration), security-reviewer (tenancy, pii) | tenancy, migration, pii | reviewer r1 changes-required (flaky sort, no tiebreak) → r2 **approved** (2e564af); **security approved** r1; **backend-foundation (migration) approved** |
| T-A5 Inventory and design analytics (B-172) | backend-engineer (inventory) | sonnet | reviewer (opus) + security-reviewer (tenancy) | tenancy | reviewer r1 changes-required (3 blocking) → r2 **approved** (85fa715, 6b531c2, b5ea7d0); **security approved** r1. Watch at gate: 1 of 7 targeted runs failed while loading `design-service.test.ts` (no assertion failed; not reproduced) |

Co-reviewers follow decision 0019 (trimmed 2026-09-30 after the architect plan review): co-reviewers run on sonnet, the primary reviewer on opus. QA and data-analyst checks run at the gate.

## File and migration split under `src/modules/analytics/**` (fixes the ownership conflict flagged in the wave 23b handoff)
Sequence, not full parallelism, on the shared files: **T-A2 (contract) first**, then T-A3, then T-A4, then T-A5 — each of the last three adds only its own lines to files a prior card created.
- **`analytics/router.ts`**: created as a pure `stubRouter` stub by T-A2 (grant below), taken over by T-A3 (with its own 6 registrations: unitEconomics, losingOrders, leakage, shippingMargin, profitBridge, breakEven). T-A4 adds one registration (`operations`) after T-A3 lands. T-A5 adds three (`inventoryHealth`, `supplierTrends`, `designLifecycle`) plus `export`, after T-A4 lands. No card may edit another card's existing registrations.
- **`analytics/shared.ts`**: T-A3 only (the `computeNet` function backing AC-G1 parity).
- **`analytics/finance-service.ts`**: T-A3 only. **`analytics/operations-service.ts`**: T-A4 only. **`analytics/inventory-service.ts`**, **`analytics/design-service.ts`**: T-A5 only.
- **Migrations**: T-A3 generates `finance_fixed_monthly_cents` first; T-A4 generates `shipping_dest_zone` second (regenerates the journal if it collides, per `CLAUDE.md`). T-A5 adds no migration (size-split logic only, no schema change).
- **`db/schema/finance.ts`**: T-A3 only. **`db/schema/shipping.ts`**: T-A4 only. **`inventory/reorder.ts`**: T-A5 only (size-split addition, not a rewrite).

## Grants (tech lead)
- 2026-09-30, T-A2 (architect): `invai-backend/src/modules/analytics/router.ts` (new, stub only) and the one `analytics: analyticsRouter` line plus its import in `invai-backend/src/api/router.ts` (backend-foundation's file). Reason: the root `os.router()` fails typecheck without it; architect plan review ruling 1.

- 2026-09-30 02:05, T-A5 (backend-engineer inventory): extend owned paths to `invai-backend/src/modules/inventory/service.ts` and `inventory/router.ts` (+ their tests), only to wire `splitBySizeCurve` into `reorderSuggestions`/`createPoFromSuggestions` for AC-C3. Reason: the card granted `reorder.ts` alone, which couldn't meet AC-C3 (card gap, tech lead's).
- 2026-09-30 01:40, T-A5: `analytics/export-service.ts` + its test (given in the build prompt, recorded late here: the card promised `export` but named no file). Lesson: grants go into wave.md in the same step.

## Handoff from wave 23b (2026-09-30, tech lead)
- **State:** everything from wave 23 and 23b step 1 is pushed after a full `pnpm gate` pass (`invai-infra/.gate/run-20260930T045101Z.log`): contracts `7ee15b6`, ui `952c174`, backend `61c6396`, web `eb1e86b`, floor `7900d0a`, imaging `58b67ee`. The dev DB is freshly seeded by that gate (now with a digest and market demand data).
- **Held, don't push:** infra `3dbb899` (T-24-1, needs S-45), `b62ad92`/`3215fc6` (T-23-6, OI-22), `9fe0c55`/`490884d` (T-23-7, sit on top). Don't touch T-23-6 until OI-22 is answered. The push hook needs a fresh `pnpm gate` stamp on the exact SHAs you push; run pushes as plain `git -C /abs/repo push origin main` (no redirect, loop or `cd`: the hook refuses them).
- **Before carding:** the spec is still `draft`. The PM must log the product-designer, qa-engineer and customer-success reviews in it and set it `ready` (`waves/analytics-scope-check.md` lines 53–57). No card starts before that.
- **Sequence:** T-A2 contract first (architect commits the procedure stubs and names), with T-A1 seed in parallel (it has no contract dependency). Then T-A3, T-A4, T-A5. At most 3 agents at once, reviewers included.
- **Ownership conflicts to fix in the cards:**
  - T-A3, T-A4 and T-A5 all write under the new `src/modules/analytics/**`. Give each an exact file set (for example `finance*.ts`, `operations*.ts`, `inventory*.ts`), and have T-A3 own the router and shared helpers with a stub committed first.
  - T-A3 and T-A4 both add migrations. Run them one after the other, or the later one regenerates the drizzle journal (`CLAUDE.md`).
  - T-A1 and any seed work share `src/db/seed/**`. Only one seed card may be open at a time.
- **T-A1 must keep:** golden-path counts and Today queues unchanged, and the T-23-8 digest and T-23-10 market-demand seed steps. The seed already takes 15–20 minutes, so budget its runtime and say what 18 months adds.
- **Fences:** B-178..B-181 (Track D) stay out; OI-18 is not approved. No buyer PII in analytics: T-A4 stores the zone number only (AC-A4). OI-17 is not approved either.
- **Owed from 23b:** look at the floor screens at 1280×800 in en and es (T-23-2) at the A1 gate. No one has looked at them yet.
- **Environment traps (in `team/agent-brief.md`):** pin `REDIS_URL` to your own DB on every backend command, `db:reset` included (B-219). The web dev CSP allows only API :3000 (B-220). The market tests leak cache rows between files (B-221, Medium): if the gate's backend suite fails in `src/modules/market`, that's the cause. **B-221 stays a backlog row, not an A1 card** — the wave is already at its 5-card cap (T-A1..T-A5), B-221 has no dependency on the analytics work, and `backend-engineer (market)` already owns it outside this wave. If it flakes the A1 gate, re-run the backend suite alone (`pnpm test src/modules/market` isolated from the rest) rather than adding a 6th card; only promote it into A1 if a card slips and a slot opens.
- **Unknown processes, leave alone:** :3142 (PID 98947), vite :5183 (PID 73962), PIDs 11838 and 72215.
- **Owner:** OI-20 (disk; 13 GB free on 2026-09-30), OI-21 (CI read token), OI-22 (T-23-6 round 3). OI-17 and OI-18 are not approved.

## Gate risks seen during the wave
- 2026-09-30 00:55-01:10: OrbStack crashed (Docker socket gone, Valkey and Postgres hung). Tech lead ran `orb stop/start` + `compose up`; volumes survived. Three builders lost their final runs; the tech lead re-ran the full backend suite at 31db7f3 (green) and the T-A4 live curl.
- Load-timeout flakes in full-suite runs (same class as B-221): `src/db/seed/market-demand.test.ts` (30 s timeout; T-A1 run 3 fixes it) and `src/modules/shipping/side-effects.acceptance.test.ts` "batchBuy: two batches ... one label per order" (30 s timeout once; 8/8 alone). If the gate flakes on either, re-run that file alone and log it; don't add retries.
- Non-blocking review notes carried to A2: T-A3 channel/service groupings sort by margin only (ties can swap); `shipmentsWithoutZone` counts orders, the contract text says shipments; `break_even.sql` v2 needed (Net includes dated refunds) for data-analyst.

## Integration gate
- [ ] `pnpm gate` passes on a fresh seed, with the SHAs stamped
- [ ] Key screens looked at, including the owed floor screens at 1280×800 in en and es
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
