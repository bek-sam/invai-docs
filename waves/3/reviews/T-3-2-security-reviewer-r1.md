# Review of T-3-2 (round 1)

- Reviewer: security-reviewer on Opus
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Threat model

**Entry point:** `POST /webhooks/easypost`, `auth: public` (no session). Worst case if broken: an attacker forges tracking events and moves any shop's shipment state (marks packages delivered, ships units that were never handed to a carrier, or masks a real exception), or floods the dedupe table.

**Tenant comes from:** never the request body. The route has no company context at all until `processCarrierEvent` matches the event's `carrierShipmentId`/`trackingCode` against `shipments`, and only then routes to `target.companyId` — exactly the "workers enter the tenant too" pattern research 12 §1.1 requires. The event itself carries no `company_id`.

**Data touched:** tracker status, timestamps, tracking code, EasyPost's internal ids. **PII check:** `parseEasypostEvent`/`normalizeEasypostTracker` never copy `signed_by` or `tracking_location` out of the raw payload; `TrackerUpdate`'s doc comment says so explicitly and the webhook test asserts `JSON.stringify(e)` doesn't match `/ORLANDO|tracking_location|signed_by/`. I independently exercised this: posted a live signed event whose payload included `"signed_by":"SOMEONE"` and a `tracking_location.city: "ORLANDO"`, then inspected both the Postgres row (`carrier_webhook_events.detail`) and the raw BullMQ job hash in Redis (`bull:ship:easypost-evt_r32_a`) — neither field appears anywhere in either. **Confirmed: no PII in the queue or the DB.**

## Evidence I re-ran

| Command | Result |
|---|---|
| `tsc --noEmit`, `biome check .`, `vitest run` (worktree `invai-backend-r32` @ `b648cfd`, `invai_test_r32`) | clean / clean / 53 files, 380 tests passed |
| `vitest run src/db/rls-coverage.test.ts src/api/authz.test.ts` | 2 files, 14 tests passed |
| `grep -n "withSystem(" src/api/webhooks-carriers.ts src/modules/shipping/jobs.ts \| grep -v test` | every hit is either the cross-tenant fan-out (`findStuckIntents`, `trackerPollSweepJob`, `purgeCarrierWebhookEvents`) or a write to `carrier_webhook_events` (`recordCarrierEvent`, `forgetCarrierEvent`, `finishCarrierEvent`), which is a system-only table by design (0009's pattern) — no request-path use on tenant data |
| `\dp carrier_webhook_events` on the DB copy | `invai_app=r/invai` only — INSERT/UPDATE/DELETE correctly revoked |

### HMAC — verified myself
- **Timing-safe comparison:** `verifyEasypostSignature` does `a.length === b.length && timingSafeEqual(a, b)` (`easypost/webhook.ts`). The length check leaks only the (public, fixed 64-hex-char) length of a valid signature, not secret material — this is the standard pattern, not a timing oracle.
- **Raw body:** the route reads `c.req.text()` and verifies against that exact string *before* `JSON.parse`, so no round-trip normalization can desync the signed bytes from the verified bytes. I confirmed this live: a body with one trailing space changed appended (`${officialBody} `) fails verification in the test suite, and my own live run's bad-signature case returned 401 before any DB write (checked API logs: `easypost webhook with a bad or missing signature`, no query logged).
- **Header format:** `X-Hmac-Signature: hmac-sha256-hex=<hex>`, matched case-insensitively, hex-only compared (prefix stripped from both sides). I posted with a 64-zero fake signature and got 401.
- **Unicode normalization claim:** the report claims the secret is NFKD-normalized before HMAC and cites EasyPost's own official test vector. I verified this is a *real*, checkable claim, not an assertion: `webhook.test.ts` reproduces EasyPost's documented fixture (`sécret` / `hmac-sha256-hex=38f3f5…7db`) and a second test proves the *unnormalized* NFC form of the same secret produces a **different** signature that does *not* match the vector. I ran this test myself (part of the 380 passing) and additionally hand-verified `signEasypostBody` reads `Buffer.from(secret.normalize("NFKD"), "utf8")` — the body itself is **not** normalized, only the secret, matching the cited official clients. This is solid, reproducible evidence, not a claim I have to take on faith.

### Production / mock-secret rejection
Started the API with `NODE_ENV=production ALLOW_MOCKS=true` and no `EASYPOST_WEBHOOK_SECRET`. Posted a webhook signed with the mock dev secret (`mock-easypost-webhook-secret`, hardcoded and exported as `MOCK_EASYPOST_WEBHOOK_SECRET`) — got `404 {"error":"not found"}` before the signature was even checked (`noMockEasypostWebhooksInProd` runs ahead of the route). **Is 404 the right code, per the card's question?** Yes: it matches the existing `noMockWebhooksInProd` treatment of `/webhooks/shopify` byte-for-byte (same guard function shape, same 404, registered the same way), so the route's existence isn't distinguishable from any other unmounted path in production without a real secret. A 401/403 would confirm to a prober that a carrier-webhook endpoint exists at all; 404 doesn't. Consistent, defensible, not a new pattern invented for this card.

### Dedupe race
`carrier_webhook_events` is unique on `(provider, event_id)` and the insert uses `.onConflictDoNothing().returning(...)`, checked in a single statement — Postgres enforces this atomically at the index level, so two concurrent deliveries of the same event id can't both "win": exactly one insert returns a row, and `recordCarrierEvent` returns `false` for the loser, which the route answers with `{"ok":true,"duplicate":true}`. I replayed the same signed event live and got `{"ok":true,"duplicate":true}` on the second call. No TOCTOU window: this isn't a read-then-write dedupe check, it's a constrained write.

### State monotonicity — can an event move a state backward?
Two layers, and I checked both:
1. **Table-level (this card's addition):** `processCarrierEvent` runs under the shipment's row lock (`for("update")`) and checks for any already-`processed` event on the same `subjectId` with a strictly greater `occurredAt` before applying; if found, the incoming event is recorded `ignored`. I posted an older `in_transit` event after a `delivered` one and confirmed it was ignored (state stayed `delivered`) and the DB row shows `status: ignored, detail: "older than the last applied tracker event"`.
2. **Service-level (defense in depth, `service.ts`, read-only for this card, pre-existing):** `markInTransit` only applies from `status === "labeled"`; `markDelivered` only from `labeled|in_transit|exception`; the new `markException` only from `labeled|in_transit`. So even without the event table's check, none of these functions can move a shipment backward from a later state, and calling them again from an already-later state is a safe no-op. The one narrow gap the table-level check specifically closes (verified by reading `applyReading`): the *finer* `trackingStatus` (e.g. `out_for_delivery`) is written outside `markInTransit`'s own guard, keyed only on the coarse status still being `in_transit` — so an older, plainer `in_transit` reading arriving after a more specific one *could* regress `trackingStatus` without the `occurredAt` check. This is a real, legitimate reason for the extra columns, not speculative hardening.

## Findings

None blocking.

**Note, not a finding requiring a fix:** if `EASYPOST_API_KEY` is set for real but `EASYPOST_WEBHOOK_SECRET` is not, the route silently 404s in production and the shop's real tracking relies entirely on the 3-day-late poll. This is already an open, named follow-up in the wave doc and the author's report ("Decide whether EASYPOST_WEBHOOK_SECRET is required in production... backend-foundation"), not something this card silently introduced. I'd escalate this to a High if it were unflagged; since it's explicit and assigned an owner, it's acceptable to leave open for now, but I recommend backend-foundation add it to `PRODUCTION_KEYS` (or a documented waiver) before EasyPost keys go live for a real shop.

## Checks
- [x] Only owned paths changed (webhooks flag: co-review required — confirmed via `git show --stat` on both commits).
- [x] Nothing outside scope.
- [x] Tests exercise the behavior; `scan-test-weakening.sh` run, all hits reviewed (mocks are of dependencies, not the unit under test; the `if (!env.isTest)` hit matches an existing codebase-wide convention).
- [x] Tenancy: RLS + system-only writes verified live on the DB copy; no request path uses `withSystem` on tenant data without a documented reason.
- [x] Idempotency: DB-constrained dedupe, verified with a live replay; no PII in logs, queue payloads or the DB, verified live with a payload containing PII fields.
- [x] Decisions recorded: schema matches 0009; HMAC pattern matches Shopify's; no new decision record needed for either.
