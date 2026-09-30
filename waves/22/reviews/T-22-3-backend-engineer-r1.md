# Review of T-22-3 (round 1): shipping consumer co-review

- Reviewer: backend-engineer (shipping) on Sonnet 5
- Author: integrations-engineer on opus
- Verdict: approve

## Evidence I re-ran (own DB invai_t22_3b, Redis DB 9, worktree at 0720eaa)
| Command | Result |
|---|---|
| `vitest run --reporter=dot src/modules/shipping` | `Test Files 10 passed (10)`, `Tests 88 passed (88)` |
| `vitest run --reporter=dot src/integrations/carriers` | `Test Files 5 passed (5)`, `Tests 33 passed (33)` |

## Judgment 1: label-safety.test.ts change
Legitimate replacement, not a weakening. The removed test asserted the pre-AC3 rule (expired quote
→ immediate `RATE_EXPIRED`, 0 buy calls). `buyLabel` now takes a `"rerate"` plan branch
(`service.ts`, `rerateThenBuy`) that re-rates via `rateOrder` and buys only at an identical
carrier+service+cents (`3bd775d`). The new test uses the file's existing `onBuy` hook (already
used elsewhere in the same file) to prove the re-rate happens before the single buy call, with the
fake carrier's deterministic same price. The moved-price path (0 buys, `RATE_EXPIRED`, new quote
stored) moved to `rate-ttl.test.ts` and is still covered there — I ran it and it asserts
`calls: { rate: 2, buy: 0 }` then a clean re-buy at the new price. Coverage is equal or better.

## Judgment 2: shipping invariants
- **Idempotent buy:** `buyLabel`'s Tx1 row-locks (`for("update")`) before branching; the `rerate`
  branch writes nothing to the shipment row, so a concurrent second caller re-enters its own Tx1,
  gets a fresh `"rerate"` plan too, and worst case one caller's stale `rateId` no longer matches
  after the other's `rateOrder` overwrites `rateQuotes` — it fails closed with `rateExpired()`,
  never a double buy. The carrier `buy()` call still happens with no transaction open.
- **address_check hold:** `verifyAddress` stores only a keyed HMAC + status (no address at rest,
  no PII in logs); `holdOrder` runs in a savepoint so a refused hold (label mid-buy) still commits
  the stored verification result.
- **Permissions:** `scanForms.*` and `verifyAddress` route through the existing
  `shipping.manage` contract permission (unchanged); router hunks are a straight
  `stubRouter` removal following the module pattern.
- **No side effects inside DB transactions:** every carrier call (`createScanForm`,
  `verifyAddress`, `rerateThenBuy`'s `rateOrder`) happens between two `withTenant` calls, never
  inside one — matches the claim/call/record pattern.

## Blocking findings
None.

## Checks
- [x] Only granted hunks in `shipping/{router,service}.ts` reviewed; `0720eaa` is carriers-only, outside my grant
- [x] Tests exercise the new behavior; label-safety.test.ts change is additive coverage, not weakened
- [x] Idempotency, address_check hold, permissions, no side effects in transactions all hold
- [x] Not my concern: mailer subject-hash finding (security-reviewer, in progress)

## Optional notes (not blocking)
- Minor: `rerateThenBuy`'s failure mode under true concurrency (stale `rateId` after a
  competing re-rate) surfaces as a generic `RATE_EXPIRED`-style error rather than a friendlier
  message; not a correctness issue, just a rough edge worth a follow-up card if it's ever hit.
