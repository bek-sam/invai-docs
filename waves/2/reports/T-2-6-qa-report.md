# Report: T-2-6 Golden path reflects CSV-channel shipping semantics (T-2-5 follow-up)
Author: qa-engineer on Fable

## Intake
- Card: T-2-6. Owner: qa-engineer.
- Trigger: T-2-5 (`invai-backend` `e399249`) changed shipping semantics: CSV-only channels (Etsy,
  Amazon, TikTok, Walmart while on CSV) no longer count as "pushed" at label time. Units become
  `shipped` only on the carrier's first scan, which the mock carrier fakes after
  `MOCK_CARRIER_TRANSIT_HOURS` (backend default 2h, read as `process.env.MOCK_CARRIER_TRANSIT_HOURS`
  in `invai-backend/src/modules/shipping/service.ts:76`, consumed as a real-time BullMQ delay in
  `shipping/jobs.ts`'s `scheduleMockTrackingJob`).
- Owned paths: `invai-web/e2e/**`, `invai-floor/e2e/**`.

## Built
1. **`invai-web/e2e/api-golden-path.spec.ts`, step 9:** replaced the single `orderItems.get` /
   `orders.get` reads after the tracking-push poll with `poll(...)` for `item.state === "shipped"`
   and `order.status === "shipped"`. No sleeps; bounded by the helper's default 60s timeout.
2. **`invai-web/e2e/golden-path.spec.ts`, step 9:** same fix for `order.status`. Also relaxed the
   shipment poll condition from `s.status === "labeled"` to `s.status !== "pending" && s.status !==
   "rated"`, so it doesn't require catching the shipment in the narrow `labeled` window before the
   mock scan (now seconds away, not hours) advances it to `in_transit`.
3. **Incidental fix, same file, step 1:** `getByText("Due today")` was a strict-mode locator
   collision — it also matches the pre-existing "over capacity" banner text ("More work **due
   today** than the team can finish...", `src/routes/_app/index.tsx`/`i18n/en.ts:1351`), which
   this seed's deterministic due-today count triggers. Scoped to
   `getByRole("link", { name: "Due today" })` (the stat card is a link). Unrelated to T-2-5; found
   because it blocked step 9 from ever running (`test.describe.configure({ mode: "serial" })`
   skips the rest of the file after a failure). Test-code fix only, no product code touched.
4. **`invai-infra/scripts/dev.sh`:** exports `MOCK_CARRIER_TRANSIT_HOURS="${MOCK_CARRIER_TRANSIT_HOURS:-0.001}"`
   (an agent can still override it) before starting api/worker/imaging/web/floor. A 2h real delay
   is far outside any sane E2E poll timeout; 0.001h (~3.6s) is quick but non-zero so the browser
   suite's shipment-status assertions still have room to be observed mid-flight. **Flagged for
   platform-sre review** — `invai-infra` isn't my owned repo; committed separately with that noted
   in the commit message.

## Bug filed and root-caused along the way (not fixed by me): B-106 confirmed
Seeding `invai_qa2_copy` with the worker running failed deterministically on a `stock_levels`
unique-constraint violation (`company_id, blank_variant_id, location_id`) inside the seed's own
bulk aggregate insert (`src/db/seed/index.ts:1428`). The tech lead identified this as the known
B-106 problem (the worker's own jobs — e.g. `inventory.syncAvailability`, which the worker log
shows firing seconds after seeding starts — write to `stock_levels` for a company the seed just
created, racing the seed's own unguarded insert). Confirmed: reseeding with the worker **stopped**
(imaging still up) succeeded cleanly both times. No backend code changed for this; filing it here
is enough since the tech lead already has it as B-106.

## Verified for real
Own stack, backend at HEAD `e399249` (shared tree, no backend edits), imaging shared at `8000` (free
before I started; my PID). DB copy `invai_qa2_copy` (`createdb -T invai`), `DATABASE_URL`/
`MIGRATION_DATABASE_URL` pointed at it, `REDIS_URL=redis://localhost:6379/8`, api `3280`, web
`5280`, worker with `MOCK_CARRIER_TRANSIT_HOURS=0.001`.

| Step | Command | Result |
|---|---|---|
| Reset/migrate/seed (worker stopped, per B-106) | `pnpm db:reset && pnpm db:migrate && pnpm db:seed` | Clean both times (`orders":360, "items":674`, ~25s) |
| API golden path | `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` | **13/13 passed** (12.9s); step 9 (`shipping: rates, buy...`) 4.7s — item/order reached `shipped` well inside the poll |
| Reseed + wait 65s (sign-in rate limit) | — | done |
| Browser golden path + screens smoke | `pnpm e2e` | First run: 1 failed (step 1 locator collision, pre-existing/unrelated), 12 skipped (serial mode), 2 passed (smoke). After the step-1 locator fix: **15/15 passed** (49.2s); step 9 6.2s |

Screens smoke: "No screen issues." across all 27+ routes plus detail pages and the vendor portal.

## Decisions
- **Poll, not a fixed env override alone, in the suites themselves.** Both are needed: the env
  override (`invai-infra/scripts/dev.sh`) makes the mock scan fast enough to observe in a test
  run at all; the poll makes the assertion correct regardless of exactly how fast, per
  `run-golden-path`'s "wait-for instead of sleeps" rule. Neither alone was sufficient — a poll
  against the 2h default would time out, and a single read against even a few-seconds delay is
  still a race.
- **0.001h (~3.6s), not 0h**, for the default transit delay: at 0h the mock scan could plausibly
  land in the same window as the browser suite's own network round-trips, flipping the shipment
  straight from `labeled` to `in_transit` before any observer sees `labeled` — hence also
  broadening `golden-path.spec.ts`'s shipment-status poll condition to accept anything past
  `pending`/`rated`, which is robust either way.
- **Fixed the step-1 locator** rather than working around it, since it was blocking step 9
  (serial mode) and is squarely test code I own; did not touch the capacity-banner feature itself.

## Known gaps / follow-ups
- `invai-floor/e2e/press.spec.ts` was not run this pass (not requested by T-2-6; no shipping-state
  assertions there).
- The `MOCK_CARRIER_TRANSIT_HOURS` default in `invai-infra/scripts/dev.sh` needs platform-sre's
  review/ownership sign-off (flagged in the commit message).
- B-106 (seed vs. running worker race on `stock_levels`) is confirmed again; not mine to fix.

## Processes and data
- Stopped, by recorded PID, in order: initial api/worker (killed before reseed), imaging, second
  api/worker, web. No other agent's process was touched.
- Dropped `invai_qa2_copy` at the end.
- Shared dev DB untouched throughout.

## Commits (not pushed)
- `invai-web` `4425d5e`: golden-path poll fix (both suites) + step-1 locator fix.
- `invai-infra` `148df7d`: `MOCK_CARRIER_TRANSIT_HOURS` default in `dev.sh` — **flagged for
  platform-sre review**.
