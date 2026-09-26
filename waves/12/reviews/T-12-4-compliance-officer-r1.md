# Review of T-12-4 (round 1)

- Reviewer: compliance-officer on Sonnet 5
- Author: backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `.claude/skills/privacy-request-handling/SKILL.md` | routine-purge clock is "buyer PII deleted 30 days after delivery" for the Shopify-webhook redaction path; this card's independent 18-month sweep is the processor retention backstop (B-23), not a replacement for that clock |
| `git show ba9db95 -- src/modules/privacy/service.ts` (retention section) | `BUYER_PII_RETENTION_MONTHS = 18`; `redactStaleBuyerPii` reuses `redactOrders`, the same function the Shopify `customers/redact` handler uses, so redaction scope is consistent (buyer_pii row, note, ref, personalization answers, raw payload) and order facts (totals, item counts, dates, SKUs) are kept, per the playbook's "keep non-PII order facts needed for the shop's accounting" rule |
| `vitest run src/modules/privacy/tenant.test.ts` | 10/10 passed, incl. the 18-month test (order at cutoff+1 day loses PII, totals/item counts/order number untouched, a recent order and company B's order untouched, no double audit row on re-run) |
| Read migration 0026 + `hardPurgeCompany` | soft-delete → 30-day hard purge matches stub B and the card; `audit_log` keeps only `tenant.*` lifecycle rows, everything else purged; tombstone documented and justified (avoids cascading deletes into other companies' `vendor_access` rows) |
| Read report "Known gaps and follow-ups" | Stripe-not-cancelled and sign-in-during-soft-delete are explicitly called out, not silently missing; `wave.md` records both as tracked follow-ups |
| Checked `invai-docs/compliance/privacy-requests/log.md` was not touched | correct per the playbook — this card built the tooling, no real request was logged against it |

## Acceptance criteria (compliance-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| Export/delete owner-triggered only | Yes | `org.export`/`org.delete` owner-only; matches card's "never a bare admin" wording |
| Audit trail for export/delete/cancel/purge | Yes | `tenant.export_requested`/`delete_requested`/`delete_cancelled` carry the acting user; `tenant.purged` carries `actorKind: system`; all four are in `AUDIT_ACTIONS` and kept during the purge itself |
| 18-month buyer-PII retention, independent of export/delete | Yes | daily `privacy.retentionSweep`, tested with a seeded order at the boundary |
| Cross-tenant safety on all of the above | Yes | test harness checks company B's rows/audit/files untouched by every operation on A |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — not applicable to money/i18n here; idempotency verified (no double-redaction audit row, no-op re-cancel, no-op re-purge)
- [x] Decisions recorded where needed — tombstone-vs-delete rationale and the four follow-ups are written into the report and `wave.md`, giving the owner a clear record to act on (Stripe cancel is a billing-track decision, sign-in-during-soft-delete is already flagged P1 security)

## Optional notes (not blocking)
- "Users aren't deleted" (global Better Auth users who were only members of the purged company) is correctly flagged as needing an owner/compliance decision rather than resolved unilaterally in this card — agree with deferring it, since InvAI is the controller for that data and it's a policy call, not a bug.
- Backups aging out on the RDS retention window (not actively purged) should be stated in any real deletion-confirmation reply to a shop, per the privacy-request-handling playbook; note this for whoever drafts that reply when a real request lands.
