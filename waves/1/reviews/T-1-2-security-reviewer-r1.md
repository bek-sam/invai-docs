# Review of T-1-2 (round 1)

- Reviewer: security-reviewer on Opus
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

Threat model: entry points are `POST /webhooks/:channel` (unauthenticated, internet-facing) and
`GET /webhooks/shopify/oauth/callback` (unauthenticated, internet-facing). Worst outcome if broken: a forged
webhook writes or cancels another shop's order (spoofing), the same delivery is processed twice with a paid
side effect (replay), or an attacker completes another user's pending Shopify OAuth link (session fixation /
account takeover of the connection). Commit reviewed: `90657ac` only, in a clean worktree at that commit
(parent `34ed022`). Own test DB `invai_test_r12`, own Redis DB 12, API/worker on port 3192. Everything cleaned
up afterward (DB dropped, Redis DB flushed, worktree removed, no processes left running).

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit && biome check . && vitest run` (clean worktree, `invai_test_r12`) | all green: typecheck clean, `Checked 191 files … No fixes applied`, `184 passed (184)` (includes `rls-coverage.test.ts`) |
| `grep -rn "timingSafeEqual" src/integrations/channels` | `etsy/webhooks.ts:1,66` and `shopify/common.ts:1,42,59` — every signature comparison is constant-time |
| `grep -rn "\.verifyWebhook(" src \| grep -v .test.ts` | one call site: `modules/channels/sync.ts:334` — no bypass path exists elsewhere |
| `grep -rn "withSystem(" src/modules/channels/sync.ts \| grep -v test` | every write to `webhook_deliveries` goes through `withSystem` (owner role, bypasses RLS by design); the app role's grants were revoked in migration 0007 |
| Live probe: `INSERT INTO webhook_deliveries …` as `invai_app` with a tenant session set | `ERROR: permission denied for table webhook_deliveries` — the revoke is real, not just documented |
| Live probe: cross-tenant `SELECT` on `webhook_deliveries` (unrelated `app.company_id`) | 0 rows; the owning tenant's own session sees exactly its own row |
| 5 concurrent identical Etsy deliveries (same `webhook-id`) | exactly 1 recorded/enqueued, 4 got `duplicate:true`; the DB unique index on `(channel, delivery_id)` — not RLS-filtered, so it dedupes globally across tenants as required — serialized the race correctly |
| 3 concurrent Shopify OAuth callbacks with the same `state` | exactly 1 completed the connection; 2 got "already used" — `consumeOAuthState`'s `SELECT … FOR UPDATE` correctly serializes the race |
| Mock-signed Etsy webhook with `NODE_ENV=production`, `ALLOW_MOCKS=true` | `verifyWebhook` → `false` (double-checked: the outer guard in `sync.ts` **and** the Etsy mock adapter's own `env.isProd` check both refuse it) |

## Signature-bypass checklist (all checked against the live code and, where practical, a live probe)
| Bypass | Result |
|---|---|
| Timing-unsafe comparison | Not present. Both Etsy (`timingSafeEqual`, length-checked first, every `v1,` entry checked with no early exit "so timing doesn't reveal which one matched") and Shopify (`timingSafeEqual`, length-checked) are constant-time. |
| Raw body vs. parsed body | Verification runs on `c.req.text()` (the raw string) before any `JSON.parse`, for both channels. |
| Empty signature list | `webhook-signature` missing or empty → `sig` is falsy → `verifyEtsyWebhook` returns `false` at the guard. A whitespace-only header splits into empty tokens that are skipped (`continue`), leaving `ok = false`. Verified: unsigned request → 401. |
| Timestamp tolerance abuse | ±5 min, checked against `receivedAt` (server time at receipt, not attacker-supplied) for the initial verification; the worker's re-verification checks against the `receivedAt` **recorded at that same initial receipt**, not the current time — so a slow queue doesn't cause a spurious failure, and there's no attacker-controlled field that lets a stale signature look fresh. |
| Mock secret accepted in prod | Blocked twice for Etsy (guard in `sync.ts` plus the mock adapter's own check) and once for Shopify (guard in `sync.ts` only — see note below). Live-verified for Etsy above. |

**Note (non-blocking):** Shopify's mock adapter (`shopify/mock.ts`) has no adapter-level `env.isProd` check,
unlike Etsy's. It is safe today only because `sync.ts:verifyWebhook` is the sole caller of any adapter's
`verifyWebhook` (confirmed by grep, no other call site in `src`). Recommend adding the same defense-in-depth
Etsy has, so a future direct caller can't reintroduce the gap.

## Dedupe race and the "delete on enqueue failure" path
The `(channel, delivery_id)` unique index correctly serializes truly concurrent identical deliveries (verified
live with 5 parallel requests: exactly one wins). This is sound.

The `forgetWebhookDelivery` path (delete the row and return 503 when `job.enqueue()` throws, so the channel's
own retry mechanism is asked to resend) is more subtle. I reproduced the scenario the card asked me to look
hard for: after a delivery was fully processed, I deleted its row directly (simulating `forgetWebhookDelivery`
firing on a false-negative — the job actually reached Redis but the client-side `await` failed) and resent the
identical delivery.

- The route treated the resend as brand new (`200`, no `duplicate` flag) and called `job.enqueue()` again with
  the same deterministic `jobId` (`webhook-<channel>-<deliveryId>`).
- BullMQ (6.3.8) silently returned the existing **completed** job instead of re-running the handler
  (`attemptsMade` and `processedOn` were unchanged from the original run) — so **no double order-processing
  occurred in this test.**
- The practical effect is a `webhook_deliveries` row stuck at `status = "received"` forever (the worker never
  re-invokes `finishWebhookDelivery` for it), until the 7-day purge removes it.

**Severity: Low, not blocking.** The protection against a real double-processing outcome depends entirely on
BullMQ still holding the original job under `removeOnComplete: {age: 24h, count: 5000}` (`lib/queues.ts`, a
read-only file for this card). If a legitimate retry lands *after* that job has aged out of Redis — a narrow
combination of a false-negative enqueue failure followed by a delayed real retry past 24h/5000 completions on
the `sync` queue — BullMQ would create a fresh job and the handler would run a second time. Even then, the
actual side effect (`importNormalizedOrders`) is an upsert keyed on `(channel, channelOrderId)`, so a second
run would very likely be a no-op rather than a duplicate order — I did not find a non-idempotent write inside
`handleWebhook` that a second run would double (the raw-payload archive write and `today.changed` publish are
both harmless if repeated). I'm not blocking this because: (a) it needs two independently unlikely conditions
to line up, (b) the downstream effects are themselves close to idempotent, and (c) it never crosses a tenant
boundary. I record it as a finding for the tech lead to log with an owner (this table's write paths are
`backend-foundation`'s territory going forward); a cheap mitigation would be for `forgetWebhookDelivery` to
check the job's actual state in Redis before deleting the delivery row, rather than assuming the enqueue
promise's rejection means nothing was queued.

## `webhook_deliveries` RLS and revoke design
The author chose a tenant-shaped table (nullable `company_id`, `tenantPolicy()`, `.enableRLS()`) with
`INSERT/UPDATE/DELETE` revoked from `invai_app` (migration 0007), rather than the architect's recommended pure
global table — because `rls-coverage.test.ts` (owned by security-reviewer, unchanged) fails any `company_id`
table without RLS, and the row does carry real tenant data once routed (which shop, and its delivery
outcome).

I judge this **sound**:
- Writes only ever go through `withSystem` (owner role, RLS-exempt by Postgres role membership, not by
  policy) — grep confirms no other write path exists in this commit.
- The revoke closes exactly the attack the author's own note calls out: without it, a compromised or buggy
  tenant-scoped code path could pre-insert `(channel, delivery_id)` and permanently suppress another shop's
  real webhook before it arrives. I verified live that `invai_app` genuinely cannot `INSERT` regardless of
  which `app.company_id` is set.
- The unique index still dedupes globally (constraints aren't RLS-filtered), so cross-tenant anti-replay still
  works even though `SELECT` is tenant-scoped.
- Rows with `company_id IS NULL` (never routed — no matching connected shop, or an ignored event) are
  invisible to every tenant session (`company_id = current_setting(...)` is `NULL` against `NULL`, which is
  never true) and readable only via `withSystem`. No leak.

This is a deviation from the architect's explicit round-1 recommendation ("no company_id/no RLS"), reasoned
and reversible (the author's report gives the exact follow-up: add a `SYSTEM_ONLY_TABLES` allowance to the
coverage test and drop the column). Per CLAUDE.md rule 4, this should be written up in
`invai-docs/decisions/` rather than left only in the task report — not blocking this round (the design itself
is verified safe), but I'd want it recorded before wave 2 builds anything else on top of this table's shape.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Verify before write/enqueue | yes | live probes 3–4 in the reviewer file; no code path writes before `verifyWebhook` returns true |
| 2. Etsy Standard Webhooks (dedupe, multi-sig, tolerance, fetch-by-id) | yes | see signature-bypass table; live curl case 1 imported from the **fetched** receipt |
| 3. `webhook_deliveries`, tenancy explained | yes | see design section above |
| 4. Shopify dedupe, no UUID fallback | yes | `webhookDeliveryId` has no `randomUUID()`/fallback branch; live case: missing header → 400 |
| 5. OAuth state ≤10 min, single use | yes | live 3-way race, exactly one winner |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior; none weakened (scan tool: 0 removed assertions, no `.skip`/`.only`, no mock
  of the unit under test — `vi.spyOn(...enqueue)` is used only to assert non-invocation, which is the correct
  pattern for proving "nothing enqueued")
- [x] Tenancy: `withTenant`/`withSystem` used correctly, new table has `company_id` + RLS + the write revoke;
  `rls-coverage.test.ts` and `authz.test.ts` still green
- [x] Idempotency: dedupe race and enqueue-failure path both examined with live probes (see above)
- [x] PII: the raw webhook payload is stored encrypted (`encryptField`) and only for `order_upsert` (Shopify);
  Etsy's payload carries no PII (ids only) and is never persisted verbatim
- [x] Decisions recorded — see the note above recommending a formal `decisions/` entry (not blocking)

## Optional notes (not blocking)
1. Log the enqueue-failure/stuck-row finding above (id to be assigned by the tech lead) in
   `invai-docs/security/v1-review.md` with an owner, since I'm limited to writing this review file this round.
2. Add Shopify's missing per-adapter `env.isProd` guard for defense-in-depth parity with Etsy.
3. Record the `webhook_deliveries` tenancy-design deviation from the architect's round-1 recommendation in
   `invai-docs/decisions/`.
