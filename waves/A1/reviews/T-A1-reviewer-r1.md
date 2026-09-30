Verdict: changes-required
# Review of T-A1 (round 1). Reviewer: reviewer on Opus 5.5. Author: backend-foundation on Sonnet 5. Commit invai-backend 472bd80.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (invai-backend, Node v24.21.0) | tsc clean; `Checked 440 files ... No fixes applied.` |
| `vitest run src/db/seed/` on `invai_rv8_test` (app `invai_app`, migrate `invai`), `REDIS_URL=redis://localhost:6379/12` | `Test Files 4 passed (4)`, `Tests 6 passed (6)`, 14.37s. DB dropped and Redis 12 flushed afterwards (had 0 keys and 0 clients before) |
| `scan-test-weakening.sh invai-backend 472bd80~1` | `Result: no hits`. The only test change is `}, 60_000);` on market-demand.test.ts:61. No assertion changed |
| `git show --stat 472bd80`, `git status` | 4 files, all under `src/db/seed/**`. Tree clean. `modules/shipping/zone.ts` is unchanged and only imported (`zoneForZips`) |
| PII greps on the added lines | Only email is `orders@valleyprint.test` (reserved TLD). Phone-shaped hits are order/listing ids. Names come from the seed's fake name lists |
I ran no seed and no E2E, as the gate instructions said. `invai_ta1` was already dropped, so the counts below come from the author's report plus my reading of the code.
## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 0 AC-Seed1 | Partly | The numbers clear every threshold, but many are placed on purpose: late iff `driver` is set, 190 scans in one 13-day window, two fixed PO series, one 300-unit overbuy and one excluded variant. Blocking 1 and 2 are about the history volume and when the Q4 peak lands |
| 1 golden path | Pending (gate) | Live-flow changes: `sellableBlanks` (the BC3001 MST 3XL pick falls back), `destZone` on live shipments, 2nd vendor (not default), 2 extra received sheets, 2-day profit cutoff. Author ran 7/13 plus Today by hand. Approval needs the gate's fresh-seed `api-golden-path` and `pnpm e2e` to pass |
| 2 late drivers | Yes | Fix is right: `labeledAt = o.shippedAt ?? old formula` (builder.ts ~1902). Only the closed-history push (1411) sets `shippedAt`. The live push (1101) doesn't, so live orders are unchanged |
| 3 scans | Yes (literally) | Gaps of 90–420 s. But see note b |
| 4 dead stock / size gap | Yes | BC3001/MST/3XL left out of every order path. G64000/BLK/S +300 receive, ledger and stock_levels in step |
| 5 PO trends | Yes | G64000 cost 260→285 (+9.6%), CC1717 lead time 4→9 days |
| 6 edge cases | Yes | Cancelled-after-on_sheet comes from the live flow, unchanged. Orders with no profit line come from `to: at-2d` (weekly-digest.ts:44). The T-23-8 digest and T-23-10 market steps still run in index.ts |

## Blocking findings
1. builder.ts:1152 against 659. History is `random.int(1,2)` orders a day (about 45 a month, Q4 about 107). The live window is 300+60 orders in 30 days (about 360 a month). The author's own totals agree: 1326 orders in all, 99 in Nov-2025 against a 44 trailing average. So the latest month is about 8x the trailing average, and the Q4 "peak" is about a quarter of it. The history turns into a cliff instead of a trend. Concrete failure: `analytics` `basePeriod` defaults to the equal-length period before `period` (contracts analytics.ts:81). For a 30-day period, the profit bridge and period comparisons see about 45 base orders against about 360, so every channel and design looks up ~700%. The card promises realistic history, and the seed-realism lesson applies. Fix: base history volume near the live rate (about 8–12 a day, Q4 1.5–2x that), keeping the driver targets. It's bulk insert, so runtime stays small.
2. builder.ts:1138. `q4Year` uses `histEnd.getUTCMonth() >= 10`, but the comment says "most recent full Nov 1–Dec 31". For a seed run between Dec 2 and Jan 1, `histEnd` falls in Nov, so it picks the current year's partial Q4. Only a few November days get boosted, and the full prior Q4 inside the range stays flat. Example: a seed on 2026-12-05 boosts only Nov 1–4 2026. From then on the AC-Seed1 Q4 check passes only because of the live-window cliff. Fix: pick the latest year whose Dec 31 ≤ `histEnd`.

## Checks
- [x] Only owned paths changed (`src/db/seed/**`)
- [x] Nothing outside scope (no `src/modules/**` edits, no Track D shapes)
- [x] Tests not weakened (scan clean, timeout only). No unit test covers `closedHistory`, and the gate seed is the proof
- [x] Tenancy: every row has `companyId: shopId` inside the seed's `run` (existing seed pattern). No new tables, idempotency paths or UI strings
- [x] Decisions: none needed

## Optional notes (not blocking)
a. Late iff driver (1236): 100% of driver-tagged history ships late and 0% of the rest does (blocked 50/50), so the driver lift is unbounded. Suggest probabilities, for example 40–60% late with a driver and 5–8% without.
b. Scans (1450) sit about 380 days back and are tied to items pressed and delivered months earlier. Reprints (1542) are requested months after delivery. Batch `itemCount` is 40 against 20 items per sheet. The shipments loop overwrites `deliveredAt` with labeledAt+3d, which doesn't match the item `delivered` transition. On-time `shipped_at` can come before `packed`. Received history POs have no inventory receive movements.
c. The weekly-digest.ts comment "always ... well before this cutoff" is wrong on Mondays and Tuesdays: the digest week then includes orders with no profit line (`incompleteOrders > 0`). The 03:15 UTC `finance.nightly` job fills the 2-day gap, so AC-6's case lasts less than a day in dev.
d. Recheck AC-C1's "G64000 Sand L under-stocked" premise (size_mix_gap.md:30, taken from the old seed) against the new seed at the gate.
e. The runtime claim (31 s warm against 543 s cold) is plausible, since history is bulk-inserted with no imaging calls. The gate's seed timing settles it.
