# Review of T-22-5 (round 1)

- Reviewer: reviewer on opus. Author: backend-engineer on opus. Verdict: **changes-required**. Diff: contracts `9e8ea0c`; backend `f6725b8 159c7da a6fb254 fb8aa0a 19c16a5 147a2bf b90157c` (other unpushed commits belong to other cards).

## Evidence I re-ran (own DB `invai_t22_5r`, Redis 10; DB dropped, Redis 10 flushed after)
| Command | Result |
|---|---|
| backend `pnpm typecheck && pnpm lint` | tsc clean; `biome check .` 417 files, no fixes |
| `vitest run src/modules/orders src/modules/vendors src/modules/finance src/integrations/channels/csv` | 18 files, 111 passed |
| `vitest run ai/listing-attributes.test.ts db/rls-coverage.test.ts api/authz.test.ts` | 3 files, 16 passed |
| contracts `pnpm test` | 8 files, 88 passed |
| `import-races.test.ts` on HEAD with `import.ts` from `147a2bf~1` | 4 of 5 fail (`duplicate key ... orders_company_id_channel_channel_order_id_index`; money asserts) → red for the right reason |
| Mutation: advisory-lock line removed | 5/5 pass, 3 runs → the lock itself is not proven by any test (note 1) |
| Scratch probe (delivery.test fixtures): stale `sending` → job, and a 550 → job; then read `getSheet` + `alerts` | `PROBE 0 sent sent 0 null`: 0 mails, both sheets say `sent`, 0 alerts, no delivery field anywhere |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | ON CONFLICT + fallback update; parallel tests real and red on old code |
| 2 | yes | no code change; T-7-4 `import-edits.test.ts` green in my orders run |
| 3 | **no** | once-only claim, resend window (lock-serialized), `vendors.manage` all good. But a kill between the claim and the SMTP call ends `unknown` with 0 mails, and `unknown`/`failed` reach no API, alert or UI (finding 1). The card's own check ("kill mid-job, restart: one email") gave 0 |
| 4 | yes | `fees.test.ts`, `profit.test.ts`, `tiktok-fee-backfill.test.ts` (only tiktok at 8 moves; etsy 8 and tiktok 7.5 kept) |
| 5 | yes (tests) | `listing-attributes.test.ts` green; the hunk itself is for the ai-engineer |
| 6 | yes | tenancy test for `vendor_sheet_deliveries` (cross-shop read, composite FK, WITH CHECK); rls-coverage/authz green |
| 7 | yes | Order Report → Unshipped keeps 2499/499/258; red on old code |

## Blocking findings
1. `src/modules/vendors/delivery.ts:199-212, 226, 280-290` (with `service.ts:411-423`): the vendor email can now be lost silently. Before, a failed send failed `sendSheetToVendor` and the office saw an error. Now the sheet is `sent` at once, and a delivery that ends `unknown` (worker killed after the claim, even before any SMTP byte: `sheetDownloadUrls` + connect run after the claim commits) or `failed` (550, 5 retries) is written only to a table nothing reads (`grep vendorSheetDeliveries` → no reader outside delivery.ts) and a log line. Scenario: the worker restarts during a deploy right after claiming sheet #12. The row becomes `unknown`, no mail goes out, the office sees "sent", and the only signal is the generic `sheet_stuck` alert 24 h later. The ship-by date is missed. Fix inside owned paths: when a row ends `unknown` or `failed`, raise an open alert through `raiseAlert` (precedent: `shipping/jobs.ts:584` `alertStuck`, reusing the closest kind, `sheet_stuck`) that tells the office "Email to <vendor> for sheet X may not have gone out. Resend it." (en+es from the web later). Also claim after building the links, to narrow the "claimed, nothing sent" window. A dedicated alert kind or a `lastDelivery` field is an additive contract follow-up (architect).

## Checks
- [x] Only owned paths changed (vendors/orders/finance, schema vendors.ts + 0034/0035, ai/service.ts grant hunk)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; none weakened (scan: only a mailer `vi.mock`, a dependency; `fees.test.ts:90` 8→6 is the required source update)
- [x] Tenancy: `withTenant` only, no `withSystem` in the code; new table has company_id, RLS, composite FKs and a company-leading unique index. Money in cents
- [ ] Idempotency: at-most-once holds (never double-sends), but the lost-send case is invisible (finding 1)

## Optional notes (not blocking)
1. The advisory lock is untested (the mutation above stays green), and `updateExisting` doesn't lock the order row. Two *different* connections of one channel editing the same existing order at once could both add the unit for a quantity increase. Consider `for("update")` on the order.
2. `errorCode` treats every non-5xx error as "nothing accepted" and retries. A socket reset after DATA could send a second copy. That is rare, and it contradicts the at-most-once rationale.
3. `mergeTotals` also ignores a real change to 0 (for example, a Shopify edit that makes shipping free). Scoping the rule to price-less payloads would be tighter.
