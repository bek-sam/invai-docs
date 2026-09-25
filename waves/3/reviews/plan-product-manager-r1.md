# Wave 3 plan review — product-manager, round 1

**Verdict: approve with clarifications applied** (directly to the cards and `wave.md`; listed below).

## Scope traceability
| Card | Scope ref | Traced to |
|---|---|---|
| T-3-1 | `scope.md#mvp-in` item 2 (CSV import + Shopify API adapter) | Correct. |
| T-3-1 §5, compliance webhooks (B-06) | not an explicit `scope.md` MVP-in line item | **In scope**, via `scope.md`'s "Always in scope: compliance deadlines... privacy requests" — Shopify's `customers/data_request`, `customers/redact`, `shop/redact` are both a privacy-request mechanism and a Shopify App Store listing requirement (marketplace approval), both always-in-scope buckets. No decision reopening needed. Recommend (non-blocking) a one-line `scope.md` change-log entry noting this so the next auditor doesn't have to re-derive it. |
| T-3-2 | `scope.md#mvp-in` item 7 (shipping: tracking push) | Correct — "real tracking updates" is the literal gap audit flagged (B-66). |
| T-3-3 | `scope.md#mvp-in` items 2 and 6, decision 0003 | Correct, and decision 0003's opt-in gating is in the acceptance criteria (AC3), not just cited. |
| T-3-4 | owner's rule 9 (heavy work → job queue), always-in-scope reliability | Correct; this is infrastructure hygiene, not a new user-facing feature, so it doesn't need a `scope.md` line — the owner's rule is the ref. |

No card builds anything cut by decision 0006 (direct Amazon/Etsy/TikTok/Walmart APIs, SanMar, etc.) or outside the always-in-scope buckets. All four backlog IDs cited (B-28, B-63, B-06, B-04, B-05, B-99, B-66, B-65, B-61, B-12, B-100) trace to `build/audit-2026-09-24.md` findings I could locate by file:line — verified, not just cited by number.

## Testable acceptance criteria — gaps found and fixed
1. **T-3-1 AC5** said `redact` must act "within the required window" with no number given — untestable as written. Changed to a concrete, verifiable rule: PII is gone **synchronously, inside the webhook handler**, before the 200 response. QA can now assert this in one test instead of guessing a deadline.
2. **T-3-3 AC2** said affected variants are "queued and debounced" with no window — changed to ask for a concrete debounce interval (e.g. 30-60s) so the behavior is deterministically testable, not just "eventually happens."
3. The rest of the criteria (paid-order filtering, pagination beyond 100, HMAC verification, idempotent `setAvailability`, out-of-order tracker events never moving state backwards, 5,000-row import not holding one transaction, no duplicate labels after a worker restart) are each concrete and independently verifiable — good.

## Other notes
- T-3-1 bundles order/inventory correctness, token refresh and a brand-new compliance/privacy subsystem into one card with 9 acceptance criteria. Scope-wise every piece belongs, but see the architect's review for a sizing recommendation — that's their call, not scope.
- T-3-3 correctly waits on T-3-1's `setAvailability` fix rather than building on top of the known-broken version; good sequencing.
- No pricing, plan-limit or segment-targeting decisions are implicated by this wave; nothing to escalate to the owner.
