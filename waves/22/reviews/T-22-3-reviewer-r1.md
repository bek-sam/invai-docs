# Review of T-22-3 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: integrations-engineer on opus
- Verdict: approve

## Evidence I re-ran (worktree at 0720eaa, `invai_t22_3r`, Redis DB 10; T-22-2's 3b50fb8 is in the base but not reviewed)
| Command | Result |
|---|---|
| `tsc --noEmit` / `biome check .` | 0 errors / `Checked 408 files ... No fixes applied.` |
| `vitest run --reporter=dot src/integrations/carriers src/modules/shipping src/integrations/channels/csv src/integrations/vendors` | `Test Files 20 passed (20)`, `Tests 143 passed (143)` |
| `vitest run src/db/rls-coverage.test.ts src/api/authz.test.ts` + scratch test (deleted) | 3 files, 29 passed. Scratch: 8 concurrent `createScanForm` (carrier call delayed 300 ms) → 1 ok, 7 `CONFLICT`, 1 carrier call, 1 row (3 labels); a 9th call returns the same form. Shop B insert into shop A's `scan_forms` → rejected (RLS); `address_verifications` with a foreign order id → rejected (composite FK) |
| `scan-test-weakening.sh` (faff2b9~1..0720eaa) | 3 removed assertions, all in `label-safety.test.ts` expired-quote test (see Checks); `carriers/index.ts` hit is the normal mock selection; `fk-coverage.test.ts` hit is T-22-2 |
| Fixture PII greps on new fixtures | only `@example.com`; phone-shaped hits are order ids |
| `git show faff2b9~1:.../csv/parse.ts` | `shipping-price` already mapped at line 575 before the card; `seed/builder.ts:800` hardcodes Amazon shipping 0 |
| No curl pass: every criterion was judgeable from tests plus the scratch probe. Cleanup: worktree removed, DB dropped, Redis 10 flushed (0 clients) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `service.ts` createScanForm: claim row under unique `(company_id, carrier, date)`, carrier call outside tx, read-back on unknown; `NOT EXISTS ... any(shipment_ids)` excludes labels on any form; status filter excludes voided. 8 SCAN tests + my concurrency probe |
| 2 | yes | verifyAddress stores status/detail/HMAC only (no address column in 0032); failed → `holdOrder(address_check)` in a savepoint; logs carry ids and status. 5 address tests incl. log spy |
| 3 | yes | `buyLabel` expired → `rerateThenBuy`; buys only if same carrier+service at the same cents, else `RATE_EXPIRED` 409; `rerated` flag stops loops. `rate-ttl.test.ts`: moved price → `{rate: 2, buy: 0}`, status `rated`. Concurrent re-rates replace rateIds, so a stale buy hits `rateExpired()`, not a charge |
| 4 | yes (no parser bug) | Evidence above holds; Order Report fixture test reads `orders.shipping_cents` 499/599/0 |
| 5 | yes | all four mailer log lines use `subjectLogFields` (template + 16-hex hash); `mailer-subject.test.ts` |
| 6 | yes | checks above green |

## Blocking findings
none

## Checks
- [x] Only owned paths changed: carriers, csv, mailer, shipping router/service hunks, schema + migration (granted). Tests `rate-ttl.test.ts`, `scan-forms.test.ts` new beside the granted hunks; `label-safety.test.ts` edit disclosed, left to backend-engineer's co-review
- [x] Nothing outside scope (`address_verifications` accepted by tech lead)
- [x] No weakening that loses coverage: the removed "expired refused, 0 buys" assertions encode the behavior AC3 replaces; "never charge a moved price" is asserted in `rate-ttl.test.ts:155-179`
- [x] Tenancy: both tables `company_id` + RLS + tenant policy + `company_id`-leading indexes; all paths `withTenant`; other shop → `NOT_FOUND`; `scanForms.create`/`verifyAddress` need `shipping.manage`, list `shipping.read`. Idempotency proven. Money in cents. No UI text
- [x] Decisions: `CarrierExtras` and HMAC-not-address are card-local, in the report

## Optional notes (not blocking)
- 0032 has no `SET LOCAL lock_timeout` (new tables only; backend-foundation's call). If the carrier refuses a form because one label is already manifested elsewhere, the whole day is refused with no way to leave that label out. Worth a follow-up.
- `scan form failed` logs the raw carrier error text (`detail`); security-reviewer may want it trimmed.
