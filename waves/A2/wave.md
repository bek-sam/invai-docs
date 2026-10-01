# Wave A2: analytics v2, screens, assistant and digest (B-173..B-177)

- Status: **done** (2026-10-01 00:40 UTC, gate pass and push). Written by the A1 tech lead as a hand-off on 2026-09-30. A fresh tech lead plans this wave from here (CLAUDE.md token budget, decisions 0018 and 0019).
- Spec: `specs/business-analytics-v2.md` (status `ready`), tracks T-A6..T-A10. Scope check: `waves/analytics-scope-check.md`.

## Handoff from wave A1 (2026-09-30, tech lead)
- **State:** A1 is done and pushed after a full `pnpm gate` pass (`invai-infra/.gate/run-20260930T172303Z.log`): contracts `f466088` (contract 0.9.0, `analytics.*`), backend `5170e12`, web `369705f`, floor `72a842d`. All 5 cards are approved with evidence in `waves/A1/reviews/`. The dev DB is freshly seeded by that gate (5377 orders, 19 months of history, Q4 2025 peak about 2.1x, seed 43 s), plus 2 orders moved through press, QC and pack by the screen check.
- **The API is ready for screens:** `analytics.{unitEconomics, losingOrders, leakage, shippingMargin, profitBridge, breakEven, operations, inventoryHealth, supplierTrends, designLifecycle, export}`; `CostSettings.fixedMonthlyCents`; `Shipment.destZone`; v6 assistant tool names are reserved in the contract.
- **Candidates (PM ranks, at most 5):** B-173 Profit v2 screens, B-174 Operations and Inventory health screens plus the Designs lifecycle column, B-175 assistant tools v6 with evals (ai-engineer co-reviews), B-176 digest detectors D9..D13, B-177 Today actions panel (depends on B-176). Their backlog status still says "PM to confirm". The PM confirms scope and sets the order.
- **Sequence:** B-173 and B-174 both edit web, so give each an exact route and file set, and never both on `routes/_app/profit*`. B-176 must land before B-177. B-175 needs no web change.
- **Fold into cards (from A1):**
  - B-226 Profit es: the Costos KPI is clipped at 1440 px, and the chart axis and margin use English number formats. Goes into B-173.
  - A1 review notes: T-A3 channel and service groupings sort by margin only (add a tiebreak); `shipmentsWithoutZone` counts orders but the contract text says shipments (architect decides which to fix); `break_even.sql` v2 (Net includes dated refunds) for the data-analyst.
  - AC-C1's "G64000 Sand L under-stocked" premise came from the old seed. With the new seed, the top size gaps are BC3001 Black 3XL (+18.0 pts) and Dusty Blue L (−18.6 pts). Fix screen tests and help text to match.
- **Open small bugs from the A1 gate (always in scope, card them if a slot opens):** B-222 floor QC "APROBAR" banner in Spanish (Medium, floor-engineer), B-223 raw English timeline string, B-224 English Today alerts, B-225 Today date locale (a B-207 repeat; add a lint ban), B-227 `db:reset` deadlock flake in the gate.
- **Environment:**
  - Use `pnpm gate <repos>` with the repos named explicitly. Infra must stay out: it holds unpushed T-23-6, T-23-7 and T-24-1 commits, and OI-22 is unanswered.
  - If `db:reset` deadlocks (40P01), re-run the gate once (B-227).
  - Playwright output now goes to `../.e2e-out/<repo>/`.
  - An unknown API is listening on :3142 (PID 30429, parent 11838). Leave it alone.
  - `invai-docs/.claude/agent-memory/` is a stray, untracked folder created by agents started inside `invai-docs`. The product-manager and reviewer memory files there belong in `/Users/bekbolsun/invai/.claude/agent-memory/`. Its owners should move them. Don't commit it.
  - Disk: 14 GB free (OI-20).
- **Fences:** Track D (B-178..B-181) stays out. OI-17 and OI-18 are not approved. No buyer PII in analytics, screens or AI prompts.

## Plan (A2 tech lead, 2026-09-30)
- Goal (user outcome): the owner sees profit, operations and inventory health on screens, gets up to 5 ranked actions on Today, a digest that catches shipping loss, losing orders, stock problems, blank price rises and break-even pace, and an assistant that explains "why" with numbers.
- Plan reviewed by: product-manager (2026-09-30, approve, `reviews/plan-pm.md`); architect (2026-09-30, approve-with-changes, `reviews/plan-architect.md`; rulings 1–3 and findings 5–6 applied to T-A10, T-A9, T-A7 the same day).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-A10](T-A10-a2-contract.md) A2 contract: D9–D13, action kinds, `today.actions`, `today.recordActionClick` (0.10.0) | architect | opus | reviewer (opus) | contract | **approved r1** (contracts 6349ddf 0.10.0, backend stub 3ebfbf8) |
| [T-A6](T-A6-profit-v2-web.md) Profit v2 screens + fixed-cost setting (B-173, B-226) | web-engineer | sonnet | reviewer (opus) + product-designer | ui | **approved r2** (web f9124ac, 81d27c5): designer r1 approve; reviewer r1 changes-required (KPI split at 390 es) → r2 approve |
| [T-A8](T-A8-assistant-tools-v6.md) Assistant tools v6, prompt v6, evals (B-175) | ai-engineer | opus | reviewer (opus) + security-reviewer | ai, tenancy | **approved r1** (backend 9f49291): reviewer approve, security approve. Real-model eval of prompt v6 (as-042) needs the owner's key |
| [T-A9](T-A9-digest-today-backend.md) Digest D9–D13, D2 mover, Today actions service + click table (B-176, B-177 backend; A1 tiebreak note) | backend-engineer (digest, today) | opus | reviewer (opus) + backend-foundation, security-reviewer | tenancy, migration, money | **approved r1** (backend 522433b): reviewer, backend-foundation, security all approve |
| [T-A7](T-A7-ops-inventory-today-web.md) Operations, Inventory health, Designs lifecycle, Today panel (B-174, B-177 web, B-225) | web-engineer | sonnet | reviewer (opus) + product-designer | ui, golden path | **approved r2** (web c756f61, e80298e, a33ffc7, e206b76, fdce8c3; QA 3b6939e): designer r1 approve; reviewer r1 changes-required (AC9 D2 mover, AC8 English labels) → r2 approve |

Co-reviewers per decision 0019 on sonnet; the primary reviewer on opus. QA's check is at the gate (adds `/analytics/operations` and `/analytics/inventory` to the smoke list).

## Order and file split
- Step 1: T-A6 Profit web and T-A8 assistant (no shared files). One slot left open for T-A6's review.
- Step 2: T-A10 starts only after T-A6 commits: its new action kinds break web's exhaustive switch in `components/digest/digest-copy.ts` (architect finding 5), and T-A6 was already running. T-A7 owns that fix. T-A9 after T-A10 is committed (it replaces the stubs). Web typecheck is red between T-A10's commit and T-A7's; no web card runs in that window.
- Step 3: T-A7 after T-A6 (T-A6 owns `routeTree.gen.ts`, `src/i18n/{en,es}.ts` and `scripts/i18n-es.json` until it commits) and after T-A9 (it consumes `today.actions`).
- `src/modules/analytics/**` is read-only for everyone except T-A9's single grant in `finance-service.ts` (tiebreak).
- Numbering: the spec's T-A10 was Today; here B-177 is split into T-A9 (backend) and T-A7 (web) and T-A10 is the contract, so the wave stays at 5 cards.

## Grants (tech lead)
- 2026-09-30, T-A10 (architect): `invai-backend/src/modules/today/router.ts`, stub registrations only for `today.actions` and `today.recordActionClick` (root router typecheck). T-A9 takes the file over.
- 2026-09-30, T-A9 (backend-engineer): `invai-backend/src/modules/analytics/finance-service.ts` (+ test), tiebreak on margin sorts only (A1 review note), (`shipmentsWithoutZone` ruled contract text only, T-A10).
- 2026-09-30 (recorded late, on T-A6's report), T-A6: `invai-web/scripts/i18n-extra-en.json`, its template-literal keys only (`pnpm i18n` needs them there). Card gap, tech lead's.
- 2026-09-30 (recorded late, on T-A7's review), T-A7: `invai-web/scripts/i18n-extra-en.json`, its template-literal keys only (same card gap as T-A6).
- 2026-09-30, T-A7 (web-engineer): `invai-web/src/components/digest/digest-copy.ts` (+ test), the six new action-kind cases with en/es copy (architect finding 5).

## Not in this wave
- B-222, B-223, B-224, B-227, B-209, T-23-3/T-23-4 polish: hand-off to wave 24 (`waves/24/wave.md`). `break_even.sql` v2 (data-analyst, dormant): backlog. Track D, OI-17, OI-18: out.

## Integration gate
- [x] `pnpm gate invai-contracts invai-backend invai-web invai-floor` passed on a fresh seed, run 3 (`invai-infra/.gate/run-20261001T002657Z.log`): contracts 121, backend 1339, web 133 + build, floor 98 + build, API golden path 13/13, browser e2e 34/34, floor e2e 3/3; stamp on contracts 6349ddf, backend 522433b, web fdce8c3, floor 72a842d
- [x] QA added the two routes (3b6939e). Tech lead looked at Profit es 1440 (T-A6) and Today es 1440 (T-A7); Operations and Inventory health were checked by the reviewers' screenshot reviews, not by the tech lead
- [x] Pushed: contracts f466088..6349ddf, backend 5170e12..522433b, web 369705f..fdce8c3 (floor unchanged)

## Build log
- 2026-09-30 Cards written (T-A6..T-A10). Plan review by PM and architect started.
- 2026-09-30 PM plan review: approve. T-A6 and T-A8 started (no dependency on the architect's open rulings, which touch T-A10/T-A9/T-A7).
- 2026-09-30 Architect plan review: approve-with-changes; applied. T-A10 held until T-A6 commits (digest-copy switch).
- 2026-09-30 T-A8 built: backend 9f49291 (mock evals 42/42 + 28/28; real-model eval needs a key). Review started: reviewer (opus), security-reviewer (sonnet).
- 2026-09-30 T-A8 security co-review r1: approve (real-model injection check left to the key-gated eval).
- 2026-09-30 T-A8 reviewer r1: approve (`reviews/T-A8-reviewer-r1.md`). T-A8 done. T-A10 still held for T-A6's commit.
- 2026-09-30 T-A6 built: web f9124ac (6 views, CSV, fixed costs, B-226 fixed; AC-A1 CM3 527973 = Net 527973). Tech lead looked at overview-es-1440: KPIs unclipped, axis in es. Review started: reviewer (opus), product-designer (sonnet). T-A10 started.
- 2026-09-30 T-A6 primary review attempt 1 stalled (600 s watchdog, no file; Docker healthy, no orphan APIs). Relaunched with a short, file-first prompt.
- 2026-09-30 T-A10 built (contracts 6349ddf, backend 3ebfbf8). Backend typecheck red at digest/rank.ts and build.ts (missed in plan review) and web red at digest-copy.ts: owned by T-A9 and T-A7. Neither repo can be gated until both land. T-A9 started.
- 2026-09-30 T-A6 product-designer r1: approve. Non-blocking: losing-orders rows show Units 0 / Revenue $0 on the seed (backend `losingOrders` counts non-reprint lines only; could be reprint-only or cancelled orders, or a data gap). Carried to the wave 24 hand-off for backend-engineer (finance) to verify. Spanish 4-digit money has no group separator (CLDR es minimumGroupingDigits 2): product-designer follow-up in invai-ui. formatPercentPoints unused (cosmetic).
- 2026-09-30 T-A6 reviewer r1 (relaunch): changes-required, 1 blocking: es 390 px KPI money breaks mid-number (`profit-v2/kpi-tile.tsx:27` break-words). Same losing-orders 0-units note. Round 2 started (web-engineer, sonnet). Web typecheck red only at digest-copy.ts (T-A10 → T-A7, known).
- 2026-09-30 T-A10 reviewer r1: approve (the architect's own report confirmed the stub by curl: 501 owner, 403 designer).
- 2026-09-30 T-A6 r2: web 81d27c5 (KPI no-wrap, single column below sm; formatPercentPoints dropped). Reviewer r2 started. T-A7 started (non-Today parts and digest-copy first; Today panel once T-A9 commits).
- 2026-09-30 T-A6 reviewer r2: approve. Note for the hand-off: amounts no longer wrap, so at 768–1100 px es a KPI might spill (estimate, untested; gate screenshot check).
- 2026-09-30 T-A9 built: backend 522433b (typecheck, lint clean; 226 affected tests pass). Deviation from ruling 2: third table `today_action_sets` (built marker + tenant FK rule); reviewers to judge. None of D9–D13 fires on the seed (thresholds not met, D13 has no fixed costs): QA note for the gate. D2 now carries `designName` when a bridge mover exists: T-A7 must render "{{mover}} moved your profit the most". Reviews started: reviewer (opus), backend-foundation (migration); security after a slot frees.
- 2026-09-30 T-A9 backend-foundation (migration) r1: approve (3 tables with RLS and composite tenant FKs; the third table is a documented deviation, not a defect). Security co-review started.
- 2026-09-30 T-A9 security r1: approve. Note: `createCompany` slug-collision flake in `src/test/fixtures.ts` when src/api and src/modules/today run in one batch (pre-existing; watch at the gate).
- 2026-09-30 T-A9 reviewer r1: approve. Follow-ups for the hand-off: a build that fails all 3 tries can't re-queue for 7 days (jobId kept on failure), so the panel stays hidden that day; a future forced-rebuild path must keep clicks.
- 2026-09-30 T-A7 progress: web c756f61 (digest copy; web typecheck green again), e80298e (Operations, Inventory health, lifecycle, nav). QA started on the smoke route list (e2e only).
- 2026-09-30 QA smoke routes: web 3b6939e (smoke 2/2 incl. the two new routes). Reviewed together with T-A7.
- 2026-09-30 Coordinator: third invai_test collision (T-A9). A2 is at its 5-card cap, so B-228 (per-run test DB and Redis DB in global-setup) is the first card of the next wave; lesson row added.
- 2026-09-30 T-A7 built: web c756f61, e80298e, a33ffc7, e206b76 (typecheck/lint/131 tests/build green; smoke 2/2). Tech lead looked at today-es-1440: panel impact reads "~$2,423.28 de impacto" (English number format under es), and the D2 `see_what_changed` case doesn't render `designName` (card AC9, added after launch). Passed to the reviewers. Review started: reviewer (opus, also covers QA 3b6939e), product-designer (sonnet).
- 2026-09-30 T-A7 product-designer r1: approve. Impact chip reuses the digest's existing key/format (the English number format under es is pre-existing digest behavior); follow-ups owned by product-designer in invai-ui: PageHeader actions clip at 390 px (repeat, T-A6 + T-A7), StatCard neutral state, KpiTile label truncation; top Today action visual priority.
- 2026-09-30 T-A7 reviewer r1: changes-required. (1) AC9: D2 ignores `designName`. (2) AC8: operations-view shows the backend's English labels ("Unknown", "In-house", "No station", late drivers) under es. Non-blocking: a money value overflows its tile at 390 px es. My "$2,423.28" note is not a defect (es-US house money format, `digestMoneyLang`). QA 3b6939e clean. Round 2 started.
- 2026-09-30 T-A7 r2: web fdce8c3 (D2 mover copy, operations sentinel labels translated, KpiTile smaller below sm; 133 tests). Reviewer r2 started.
- 2026-09-30 T-A7 reviewer r2: approve. All 5 cards approved. Gate started.
- 2026-09-30 Gate run 1 (`.gate/run-20260930T202516Z.log`): contracts 121, web 133 + build, floor 98 + build, API golden path 13/13, browser e2e 34/34, floor e2e 3/3 all green; backend test 2 failures (B-229: market http retry timeout, publish concurrent signed-URL race), none in A2 code, both pass alone 11/11. Run 2 started.
- 2026-09-30 Gate run 2 (`run-20260930T205946Z.log`): all repo checks green including backend; API golden path, browser and floor E2E failed because Valkey hung (Redis timeouts, 49-min browser run; coordinator restarted OrbStack). Run 3 started on a healthy stack.
- 2026-10-01 Gate run 3: full pass (above). Pushed contracts, backend and web. Hand-off for the next wave written in `waves/24/wave.md`.

## Metrics
- First-pass approval: 3/5 cards (T-A8, T-A9, T-A10 approved by every reviewer in round 1; T-A6 and T-A7 needed round 2, each for 1–2 real UI/i18n defects). Reopen rate 0. Escaped defects: none known yet.
- Canary catch rate: no canary planted (OI-15 still asks the owner for a method).
- Cycle time: about 7 hours from plan to push for the wave; cards 1–3 hours of building each.
- Tokens per card (subagent totals, approximate): T-A6 650k (2 builds) + 290k reviews; T-A7 745k (2 builds) + 320k reviews; T-A8 245k + 270k reviews; T-A9 330k + 420k reviews (3 reviewers); T-A10 150k + 75k review; plan reviews 260k; QA 130k. The two web builders on sonnet were the largest spend (about 250–300 tool calls each).
- Gate runs: 3 (run 1: 2 backend load flakes, B-229; run 2: Valkey hang, environment; run 3: pass).

## Retro (short)
- Worked: contract stub first with a written plan review. The architect's review caught the exhaustive switch in `digest-copy.ts` before it broke a running web card. Sequencing web cards around the generated i18n and routeTree files avoided collisions.
- Didn't: the architect's plan review missed 2 backend exhaustive maps (`digest/config.ts`, `db/schema/digest.ts`), so backend typecheck was red between T-A10 and T-A9. A card AC (T-A7 AC9) added after launch was missed by the running builder. Two late grants (`scripts/i18n-extra-en.json`) came from cards that didn't list the i18n extra-keys file. A third `invai_test` collision led to B-228.
- Rules: when a contract adds enum values, grep every consumer for exhaustive switches and `Record<Enum,…>` maps in the plan review. Never add an AC to a running card without telling its builder; put it on the next round instead. Web cards that add template-literal i18n keys own `scripts/i18n-extra-en.json`.
