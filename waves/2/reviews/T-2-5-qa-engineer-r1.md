# Review of T-2-5 (round 1)

- Reviewer: qa-engineer on Fable (this session)
- Author: backend-engineer (shipping) on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| Worktree at `e399249`, symlinked `node_modules`, `invai_test_r25`, redis `/9` | set up |
| `tsc --noEmit` / `biome check .` / `vitest run` / `tsup` | clean / clean / 318 passed / build success |
| API+worker started on :3295 against `invai_r25_copy`, `/health` ok | confirmed |
| `invai-web/e2e/api-golden-path.spec.ts` step 9, read in full (lines 316-353) | see finding below |
| `invai-backend/src/modules/shipping/service.ts:76`, `src/modules/shipping/jobs.ts:99-118` | confirms the default mock transit delay |

**Environment failure, disclosed:** a host disk-full (`ENOSPC`) failure mid-session killed my exercise API/worker and then Docker itself; independently confirmed twice via diagnostic sub-agents, disk went to 0 bytes free and has only partially recovered (Docker/OrbStack still down as of this review). I was not able to actually run `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` myself against a live seed. The finding below is derived from reading the spec and the shipping code directly (not from running the suite), and matches exactly what the author's own report already disclosed as a known gap — I'm independently confirming their analysis is correct and that it is a real, unaddressed break under the suite's default configuration, not merely a hypothetical. Recommend an actual E2E run once Docker is healthy again to confirm this finding as observed (not just traced), but the code paths involved leave no ambiguity about the outcome.

## Acceptance criteria (golden-path impact only — see the primary reviewer file for the card's own criteria)
| # | Met? | Evidence |
|---|---|---|
| Golden path still passes on a fresh seed | **No, under default settings** | See blocking finding below. |

## Blocking findings
1. **`invai-web/e2e/api-golden-path.spec.ts:316-353`** — Step 9 ("shipping: rates, buy (mock carrier), label PDF, tracking pushed, items shipped") polls only `trackingPush.status` for `pushed` or `not_required`, then immediately asserts `item.state === "shipped"` and `order.status === "shipped"` with no further wait. The order used in this test is on the Etsy connection (a CSV channel, per the step's own comment: "Etsy is a CSV connection: there is no API to push to, so the push resolves to not_required"). Under T-2-5's new semantics, a `not_required` push no longer ships the units (`invai-backend/src/modules/shipping/service.ts:930`, the `if (!needsPush) await shipItems(...)` line was deliberately removed) — CSV-channel items now ship only on `markInTransit`, the carrier's first scan. That scan is scheduled as a **delayed BullMQ job**, `MOCK_TRANSIT_HOURS * 3600_000` after the label is bought (`shipping/jobs.ts:99-118`), and `MOCK_TRANSIT_HOURS` defaults to **2 hours** (`shipping/service.ts:76`: `process.env.MOCK_CARRIER_TRANSIT_HOURS ?? 2`). Nothing in `invai-web`'s Playwright config or the project's E2E docs sets `MOCK_CARRIER_TRANSIT_HOURS` to 0. Concrete failure: run the suite as written (`E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts`) with no special env vars — step 9's push resolves to `not_required` immediately, but the item is still `packed` (the mock scan job won't fire for another 2 simulated hours), so `expect(item.state).toBe("shipped")` fails. The author's own report confirms this: they only got it to pass by manually exporting `MOCK_CARRIER_TRANSIT_HOURS=0` for their run, and flagged it explicitly as a known gap with a recommended fix. I independently traced the same code path and confirm their analysis is correct.
   - **Fix (qa-engineer's to make, `e2e/**` is qa-engineer-owned, not T-2-5's backend):** change step 9 to `poll()` (already imported and used elsewhere in the same file, e.g. step 10's `orderProfit` poll) for `item.state === "shipped"` (or for the shipment reaching `trackingStatus === "in_transit"`) instead of asserting immediately after the tracking-push poll resolves. Pair this with setting `MOCK_CARRIER_TRANSIT_HOURS=0` (and correspondingly small `MOCK_CARRIER_DELIVERY_HOURS`) in the E2E stack's environment so the suite still finishes in the ~10s budget `qa-engineer.md`/`CLAUDE.md` call for, rather than actually waiting. The stale comment at line ~345 ("Either way the shipment leaves the pending state") should also be updated — it's no longer true that leaving `pending` implies shipped for a CSV channel.
   - This blocks the wave-2 integration gate's `run-golden-path` checkbox in `wave.md`, not the T-2-5 card's own backend push — the backend correctly implements the new (more correct) semantics; the test fixture is the thing that's now wrong.

## Checks
- [x] Tests exercise the behavior, and none were weakened in T-2-5's own suites (scan clean, see the primary reviewer file)
- [ ] Golden-path E2E suite confirmed green on a fresh seed — **not met**, see blocking finding; also not personally re-run this round due to the environment outage
- [x] The four "look hard for" reproduction scenarios (crash-and-retry, cancel-after-label, cancel-refused-after-push, CSV void-before-scan) are each covered by a named, passing unit/integration test (see the primary reviewer file); could not additionally reproduce live via curl this round due to the same outage

## Optional notes (not blocking)
- Once `MOCK_CARRIER_TRANSIT_HOURS=0` is set for E2E, double check `invai-web/e2e/golden-path.spec.ts` (the browser version of the same 13 steps) and `screens.smoke.spec.ts` for the same assumption — the browser suite likely hits the identical step-9-equivalent issue since it exercises the same backend behavior, though I did not independently confirm this (same env constraint).
