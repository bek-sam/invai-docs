# Report: T-3-2 EasyPost live tracking
Author: integrations-engineer on Opus 5.5

These commits are on `main` in `invai-backend`. None are pushed.
- **`55725bf`:** the `carrier_webhook_events` schema and migration `0013_carriers_webhook_events`.
- **`b648cfd`:** the route, the signature check, the tracker states, the poll, the sweep, the error mapping and the tests.

## Intake
- **Card:** T-3-2. **Owner:** integrations-engineer. **Scope:** `product/scope.md#mvp-in` item 7, backlog B-66, plus the T-2-5 follow-up (a sweep for stuck intents).
- **Owned paths:**
  - `integrations/carriers/**`
  - new `api/webhooks-carriers.ts`, and its mount and guard in `api/app.ts`
  - `modules/shipping/jobs.ts`
  - a new schema file with its migration
  - one line in `env.ts`
  - tests next to these files
- **Read-only:** `modules/shipping/service.ts`. I only call existing functions there and didn't edit the file. I didn't need `markInTransit(at)`, because out-of-order detection uses the event table (see Decisions).
- **Risk flag:** webhooks. Co-reviewer: security-reviewer.

## Built
- **Signature check** (`integrations/carriers/easypost/webhook.ts`):
  - `verifyEasypostSignature(headers, body, secret)` checks `X-Hmac-Signature: hmac-sha256-hex=<hex>`. The hex is HMAC-SHA256 of the raw body, keyed with the **NFKD-normalized** secret, compared in constant time with `timingSafeEqual`.
  - Also here: `MOCK_EASYPOST_WEBHOOK_SECRET`, the `easypostWebhookSecret()` fallback and `signEasypostBody`.
  - `parseEasypostEvent` normalizes the Tracker at the edge. The recipient's name (`signed_by`) and scan locations are never copied out of the payload.
  - `acceptedEventMode`: `EZTK` keys accept only test events and `EZAK` keys only production events.
  - I checked the format against the official clients: easypost-python `util.py` `validate_webhook` and easypost-node `src/utils/util.ts` `validateWebhook`. A test reproduces EasyPost's own test vector: secret `sécret`, `hmac-sha256-hex=38f3f5…27db`. That vector matches only with NFKD, and the test proves it.
- **Route** `POST /webhooks/easypost` (`api/webhooks-carriers.ts`). It is its own top-level `app.route()`, registered before `/webhooks` (`api/app.ts`). A request goes through these steps:
  1. Signature check. A missing or wrong signature gets 401 before anything is written.
  2. Parse. A body that isn't an Event gets 400.
  3. Mode check. An event from the other mode is recorded as `ignored` and answered with 200.
  4. Dedupe. The event id is inserted into `carrier_webhook_events`, and a redelivery gets 200 `duplicate`.
  5. Enqueue. The normalized event goes to `shipping.easypostEvent`. If enqueueing fails, the row is deleted and the route answers 503, so EasyPost retries.
- **Production guard:** `noMockEasypostWebhooksInProd` returns 404 when `NODE_ENV=production` and there is no `EASYPOST_WEBHOOK_SECRET`.
- **`carrier_webhook_events`** (`db/schema/carriers.ts`, migration `0013`) follows the decision 0009 shape:
  - `company_id` is nullable and set once the event is routed (foreign key with cascade).
  - The provider is `["easypost"]`, and `status` is `received|processed|ignored|failed`.
  - Unique on `(provider, event_id)`, with indexes on `received_at` and `(company_id, received_at)`.
  - Tenant RLS, plus `REVOKE INSERT, UPDATE, DELETE … FROM invai_app` in the same migration. On the test DB, the grants are `SELECT` only.
  - I added two columns, `subject_id` and `occurred_at`; see Decisions.
  - A daily purge deletes rows older than 7 days.
- **One tracking state function** (`modules/shipping/jobs.ts`): `applyTrackerUpdate` / `applyReading`. The EasyPost event job, the daily poll and the mock timer (`shipping.mockTracking`) all use it.
  - `in_transit`, `out_for_delivery` and `available_for_pickup` call `markInTransit`. That ships CSV-channel units, per T-2-5. The finer status is kept in `trackingStatus`.
  - `delivered` calls `markDelivered(…, at = the delivery scan time)`.
  - `return_to_sender` and `failure` call a new local `markException`, which applies only from `labeled` or `in_transit`.
  - `pre_transit`, `unknown`, `cancelled` and `error` don't move the shipment.
- **Routing and out-of-order events** (`processCarrierEvent`):
  - A tracker is matched to its shipment by the carrier shipment id, or by the tracking code if the id is missing.
  - An event is ignored if the tracking code doesn't match the shipment, if more than one shipment matches, or if no shipment matches.
  - **An event is applied only if no processed event for the same tracker has a later scan.** That check runs under the shipment's row lock, and the event is recorded before the lock is released, so two concurrent events can't both slip past it.
  - The service's forward-only guards cover everything else. A shipment never goes backwards from `delivered`, and never from `exception` to `in_transit`.
- **Tracker creation:**
  - On buy, the EasyPost adapter uses the tracker EasyPost creates at purchase. If the buy response has none, it calls `POST /trackers`, which EasyPost dedupes. This is best effort: the buy never fails because of it.
  - New `TrackingAdapter.track` (EasyPost and mock) and `carrierTracking()`. The EasyPost version calls `GET /shipments/{id}`, then `GET /trackers/{id}`, or creates the tracker if the shipment has none.
- **Daily poll:** `shipping.trackerPollSweep` runs at 06:20 UTC. It finds shipments still `labeled` more than 3 days after the label (up to 500), then runs `shipping.pollTracker` for each, one job per shipment per day. Calls are throttled by a Redis token bucket at 5 per second (`easypost:trackers`).
- **Stuck-intent sweep:** `shipping.stuckIntentSweep` runs every 5 minutes. It finds `buying` or `voiding` shipments, and `pushing` tracking pushes, untouched for more than 15 minutes, then runs `shipping.retryStuckIntent` for each.
  - **Buy:** `buyLabel(…, { readBackOnly: true })`. It records a label the carrier sold, or returns the shipment to `rated`. **It never buys again.**
  - **Void:** `voidShipment` reads the refund status back before asking again.
  - **Push:** `pushTracking`, which T-2-5 made safe to repeat. A `retry` or `busy` result goes back to `shipping.pushTracking`'s own retry loop.
  - Failures are counted per intent in Redis (key `stuck-intent:<kind>:<id>`, kept 7 days). After **3** failures the sweep raises an alert with `raiseAlert` (dedupe key `stuck-intent-<kind>-<id>`). If the carrier refused the void or the push finally failed, it alerts at once.
- **Error mapping** (`carriers/easypost/index.ts`):
  - `rate_expired` now comes only from `SHIPMENT.RATE.EXPIRED`, `SHIPMENT.RATE.CARRIER_ACCOUNT_INVALID` and `ORDER.RATE.UNAVAILABLE`. Before this change, anything containing "RATE" mapped to it, including `RATE_LIMITED` and `SHIPMENT.RATES.UNAVAILABLE`.
  - A 429 is `upstream`/`not_done` with the message "EasyPost is limiting requests right now … Try again in a minute."
  - 429s are retried with exponential backoff and full jitter, at most 3 times, but only for reads, shipment creation and tracker creation. **A buy or refund is never re-sent.**
  - `SHIPMENT.POSTAGE.{NO_RESPONSE,TIMED_OUT,EXISTS}` are `unknown`, so the service reads back before any retry.
- **Carriers we can't label:** rates from carriers we can't store yet (such as FedEx) are logged and named in the "no rates" error. The shipping service still filters what's left by the shop's allowed carriers.
- **Mock carrier:** records now carry `boughtAt`, and `mockTracking.track` follows the same `MOCK_CARRIER_*_HOURS` clock as the timer. The mock timer path is unchanged apart from calling the shared state function.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Webhook: HMAC first, dedupe, state mapping, never backwards | Yes | `webhooks-carriers.test.ts`: 401 in three cases (no header, wrong secret, changed body) with nothing written or enqueued; a redelivery is acknowledged and enqueued once; a failed enqueue gives 503 and the row is forgotten; `/webhooks/easypost` isn't shadowed by `/:channel`. `jobs.test.ts`: in_transit ships CSV units, delivered takes the scan time, out_for_delivery, failure and return become exception; a late in_transit after delivered and a stale failure after a newer scan are ignored; a delivered shipment never becomes an exception. Also exercised for real, below. |
| 2 Tracker creation and daily poll | Yes | `index.test.ts`: `track` reads the tracker made at purchase (`GET /shipments` → `GET /trackers/trk_9`) and creates one when missing (`POST /trackers` with code and carrier). `jobs.test.ts`: the poll sweep queues a shipment labeled 4 days ago but not a fresh one, and the poll moves it to delivered. |
| 3 Mock timer works through the same function | Yes | `jobs.test.ts`: `mockTrackingJob` moves labeled → in_transit (units shipped) → delivered. The full suite, including the T-2-5 tests, passes. |
| 4 Stuck-intent sweep | Yes | `jobs.test.ts`: a buy the carrier sold but we never recorded is read back to `labeled` with **1 buy call in total**; a buy never made goes back to `rated` with no buy; a stuck void is read back and finished; a stuck push is sent **once** and its units ship; a failing push goes back to the push job; 3 failures give `["failed","failed","alerted"]` and an open alert; a later success clears the counter. Also exercised for real, below. |
| 5 Error mapping and unsupported carriers | Yes | `index.test.ts`: `RATE_LIMITED` and `SHIPMENT.RATES.UNAVAILABLE` → `upstream`; the three rate-expiry codes → `rate_expired`; a 429 on rating is retried then succeeds; a 429 on buy means one call and no retry; a read gives up after 4 calls; FedEx is logged and named in the error. |
| 6 Fetch-mocked tests | Yes | 36 new tests in 4 files: `easypost/webhook.test.ts` (8), `easypost/index.test.ts` (8), `api/webhooks-carriers.test.ts` (5), `shipping/jobs.test.ts` (15). |

## Checks I ran
Other agents' uncommitted work (T-3-1 and T-3-4) sat in the shared tree. At one point it broke `tsc` in `modules/channels/sync.ts:921`. So I ran the checks in a clean worktree, `../invai-backend-t32`: HEAD `55725bf` plus only my files, with `node_modules` symlinked. I removed the worktree afterwards.

| Repo | Command | Result |
|---|---|---|
| invai-backend | `tsc --noEmit` | exit 0 |
| invai-backend | `biome check .` | "Checked 225 files … No fixes applied." |
| invai-backend | `vitest run` (`invai_test_t32`, `REDIS_URL …/2`) | **52 files, 373 tests passed** |
| invai-backend | `tsup` (`pnpm build`) | "Build success" |

## Exercised for real
Setup: my API on :3120 and a worker (not in watch mode) on the DB copy `invai_t32_copy`, with `REDIS_URL …/2` and `MOCK_CARRIER_TRANSIT_HOURS=0.001`. On the copy, I set Amazon (CSV-only) shipment `5d25ddbd…` back to `labeled` with both units `packed` (`shp_mock_111`). Then I posted signed `tracker.updated` events with `node` + `fetch`:

```
before: labeled|pre_transit||packed,packed
evt_t32_bad in_transit (wrong secret)          -> 401 {"error":"invalid signature"}
evt_t32_a   in_transit 2026-09-24T10:00Z        -> 200 {"ok":true}
after in_transit: in_transit|in_transit||shipped,shipped
evt_t32_a   (replay)                            -> 200 {"ok":true,"duplicate":true}
evt_t32_b   delivered 2026-09-25T15:30Z         -> 200 {"ok":true}
after delivered: delivered|delivered|2026-09-25 15:30:00+00|delivered,delivered
evt_t32_c   in_transit 2026-09-24T12:00Z (older)        -> 200, state unchanged
evt_t32_d   return_to_sender 2026-09-25T09:00Z (older)  -> 200, state unchanged

 event_id  |  status   | routed |  subject_id  |      occurred_at       | detail
 evt_t32_a | processed | t      | trk_t32_demo | 2026-09-24 10:00:00+00 | in_transit: labeled -> in_transit
 evt_t32_b | processed | t      | trk_t32_demo | 2026-09-25 15:30:00+00 | delivered: in_transit -> delivered
 evt_t32_c | ignored   | t      |              |                        | older than the last applied tracker event
 evt_t32_d | ignored   | t      |              |                        | older than the last applied tracker event
```

**Sweep, for real.** On the copy, I staged:
- a Shopify shipment with tracking push status `pushing`, last attempted 20 minutes ago;
- a `buying` shipment (`shp_mock_81`) with a selected rate and a quote.

Then I enqueued `shipping.stuckIntentSweep` into the worker's queue.
- **Push:** the worker log shows a single "mock shopify fulfillment" for that order. The row ends as `delivered|pushed|1`.
- **Buy:** it was read back. The mock carrier had no record, so the shipment went back to `rated` and no purchase was attempted.

**Production guard.** With `NODE_ENV=production ALLOW_MOCKS=true` and no `EASYPOST_WEBHOOK_SECRET`, a mock-signed POST got `404 {"error":"not found"}`.

**Refused case.** A bad signature gets 401 (above). The route has no user permissions.

**Not run:** a sandbox run against real EasyPost, because no test key exists. It's in the follow-ups.

## Decisions
- **Two columns added to the decision 0009 shape** (`subject_id`, `occurred_at`, plus an index on `(provider, subject_id, occurred_at)`). The forward-only guards in `service.ts` can't tell that a late `failure` is older than an `in_transit` already applied, and `shipments` has no column for the last carrier scan time. That file isn't mine, and the alternative, `markInTransit(at)`, wouldn't store the time anywhere. Storing it on the event row keeps the check inside my paths, and the table's rules (system-only writes, RLS, 7-day retention) are unchanged. No new decision record is needed: this extends 0009's pattern. **Architect and backend-foundation should confirm this in review.**
- **Normalized at the edge, then queued.** The route parses the body only after the signature passes, and it enqueues only normalized fields: ids, status and times. `signed_by` and scan locations never reach Redis or the DB. The marketplace route queues the raw body, but carrier payloads carry the recipient's signature name.
- **The sweep never buys.** A stuck buy is resolved by read-back only. Charging a shop from a background job, long after the click, isn't safe. If the carrier has no label, the shipment goes back to `rated` and the person buys again.
- **Alert kind:** stuck-intent alerts use `tracking_push_failed`. The contract has no label or intent kind, and this is the closest shipping kind that the 5-minute alert sweep doesn't auto-resolve. The title says what actually happened ("A label purchase needs a look"). A proper `label_stuck` kind is an architect follow-up.
- **The failure counter lives in Redis** (7 days), not a new column, because `shipments` isn't mine. If the counter is lost, alerting is only delayed. The retry itself is always safe.
- **Test vs production events:** events whose mode doesn't match the key prefix are acknowledged and recorded as `ignored`. That way a test-mode webhook can never move a live shipment.

## Known gaps and follow-ups
- **No sandbox run against real EasyPost.** There are no keys. That needs a test key (`EZTK…`) and a webhook secret configured in EasyPost's dashboard (owner). Steps: set `EASYPOST_API_KEY` and `EASYPOST_WEBHOOK_SECRET`, register `https://<api>/webhooks/easypost`, buy a free test label, and watch EasyPost's test tracker move through its statuses.
- **Runbook row (docs-writer):** add `EASYPOST_WEBHOOK_SECRET` to the mock → real table. Unset means the mock secret, and in production the route answers 404. Also add the webhook URL `/webhooks/easypost`. I didn't add `EASYPOST_WEBHOOK_SECRET` to `PRODUCTION_KEYS`, because my grant was one line. Production still boots without it and relies on the daily poll. backend-foundation should decide whether it becomes required.
- **Contract (architect):** add a `label_stuck` or `intent_stuck` alert kind; see Decisions. Also, a stuck-intent alert isn't auto-resolved when a later retry succeeds, because `today` has no resolve-by-key API.
- **Other carriers:** FedEx and other rates are now logged and named, but still can't be bought. `CarrierCode`, `CARRIERS` in `db/schema/shipping.ts` and the contract only allow usps, ups and mock (backend-engineer and architect).
- **Not consumed yet:** `refund.successful`, which would move `refund_pending` → `refunded`, and `scan_form.*`. Those events are recorded as `ignored`. That work belongs with B-25 and B-67.
- **A buy intent with missing quotes** makes `buyLabel` throw RATE_EXPIRED before its read-back. The sweep counts it as a failure and alerts after 3 tries. That behavior is in `service.ts`.

## Blocked by other owners
- None. Notes:
  - `db/schema/index.ts` needed a one-line export for the new schema file, because `drizzle.config.ts` reads only `index.ts`. That's backend-foundation's file. The line is in `55725bf`.
  - I didn't reach T-3-4's owner about the `env.ts` line: I have no messaging channel. My hunk is two lines next to `EASYPOST_API_KEY`. `env.ts` held no one else's changes when I committed with a pathspec. Please tell T-3-4.
  - No journal collision. I generated `0013` and committed it at once. The shared dev DB is already at `0013`, because someone migrated it after my commit.

## Processes and data
- Stopped my API (:3120, pid 47032) and worker (pid 47034). Nothing is listening on :3120.
- Removed the worktree `../invai-backend-t32`.
- Dropped `invai_t32_copy` and `invai_test_t32`.
- Flushed Redis DB 2 (mine), which removed my schedulers and test jobs.
- Deleted the temp scripts in `/tmp`.
- I never touched the shared dev DB. The only thing I ran against it was a request with no DB access: the production-guard check, which returned 404 before any query.
