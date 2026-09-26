# Review of T-7-2 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-engineer (finance) + integrations-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `grep -n "withTenant\|withSystem" invai-backend-review-t72/src/modules/finance/router.ts` | Every `finance.refunds.*` and `finance.profit`/`orderProfit` handler wrapped in `withTenant(tenant.companyId, ...)`; no `withSystem` in this card's files |
| `grep -n "ingestChannelRefunds" invai-backend-review-t72/src/modules/channels/sync.ts` + read surrounding code (lines 205-280, 540-560) | Both call sites (`runCsvImport`, the Shopify poll path) execute inside an already-open `withTenant(companyId, tx)` block passed down from the caller — no cross-tenant write path |
| `grep -n "refundEvents\|tenantPolicy" invai-backend-review-t72/src/db/schema/finance.ts` | `refund_events` has `tenantPolicy("refund_events")` and `.enableRLS()`, plus a `(companyId, orderId)` index and the `(companyId, channel, channelRefundId)` unique index used for the idempotent upsert |
| Read `ingestChannelRefunds` (`refunds.ts:175-252`) | Upserts via `onConflictDoUpdate` targeting the `(companyId, channel, channelRefundId)` unique index; re-running the same CSV import or Shopify poll cannot create a duplicate `refund_events` row — a re-sync test would show `upserted` count unchanged on replay (covered by `refunds.test.ts`, run green above) |
| Read `recordRefund` (`refunds.ts:116-167`) | Requires `finance.manage` permission (contract), validated inside `withTenant`, and calls `audit(tx, {...})` recording actor, order, refund id and amount — auditable, not silent |
| `node_modules/.bin/vitest run src/modules/finance src/integrations/channels/shopify src/integrations/channels/csv/parse-refunds.test.ts` (backend worktree) | 50/50 passed |
| `grep -rn "console.log\|PII\|email\|phone" invai-backend-review-t72/src/modules/finance/refunds.ts invai-backend-review-t72/src/integrations/channels/shopify/refunds.ts` | No PII fields touched; refund rows carry only ids, amounts and dates |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t72 2d4668f^` and `...invai-web-review-t72 d9c1e90^` | No hits in either repo, scoped to this commit |
| DB-copy live pass (idempotent re-sync, cross-tenant negative test) | **Not run** — Docker/OrbStack was unresponsive for the remainder of this review (see reviewer's file); relying on the DB-backed `refunds.test.ts` re-sync assertions instead, which already prove no duplicate row on replay against real Postgres |

## Payments/tenancy checklist
- [x] `refund_events` is a tenant table with `company_id`, RLS enabled, and a `company_id`-leading unique index for the idempotent upsert.
- [x] Every request path into refunds (`record`, `list`, `profit`, `orderProfit`, and the two ingest call sites in `channels/sync.ts`) runs under `withTenant`. No new `withSystem` usage introduced by this commit.
- [x] Idempotency: channel-sourced refunds upsert on `(companyId, channel, channelRefundId)`; a re-poll or CSV re-import updates the amount/fee in place rather than inserting a second row. Manual refunds have no channel id and are intentionally append-only (each call is a distinct real-world event) — that's the correct idempotency model for that path, not a gap.
- [x] `finance.manage` gates `recordRefund`; `finance.read` gates `list`/`profit`. No new permission or role logic was added or weakened.
- [x] The manual refund path is audited (`audit(tx, {...})` with actor, order id, refund id, amount) — traceable if a bad entry is recorded.
- [x] No secrets, tokens or PII flow through the new refund tables or the fee math; Shopify's refund GraphQL query reads only amounts/ids.
- [x] No webhook signature or auth logic touched by this card (Shopify refunds are read via the existing poll, not a new webhook endpoint).

## Blocking findings
None from a security/tenancy/idempotency standpoint.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy, idempotency, money in cents, en/es text
- [x] Decisions recorded where needed

## Optional notes (not blocking, for security posture)
- `recordRefund` has no upper bound on `amountCents` relative to the order total, and there's no `update`/`delete` on `finance.refunds` to correct a mistaken entry (only `record`/`list`). This isn't an authz or tenancy hole — `finance.manage` already gates it and it's audited — but it is a control gap for a payments-flagged card: a permitted user (or a compromised office/owner session) can silently push a period's reported profit arbitrarily negative with a single call and no way to undo it except a direct DB edit. The reviewer and data-analyst files both block on this from the correctness side; from a controls standpoint I'd want the same fix (a cap, or at least a delete/correct path with its own audit trail) before this is trusted for real money.
- Docker being down for the rest of the session meant I could not run the "different tenant's id → NOT_FOUND, not FORBIDDEN" negative check live against the DB copy; I'm relying on the existing RLS-coverage pattern (`tenantPolicy` + `withTenant` everywhere, no bypass) rather than a fresh manual probe. Worth a quick manual confirmation once infra is back, though I found nothing in the diff that would change that behavior.
