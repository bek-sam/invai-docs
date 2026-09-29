# Review of T-22-3 (round 1): security co-review (pii, payments)

- Reviewer: security-reviewer on opus 5.5 · Author: integrations-engineer on opus
- Verdict: **changes-required** (one blocking finding, S-38 Medium; one retention note)
- Scope: invai-backend faff2b9, d5a7312, 3bd775d, 044c3af, acd1dbf, 0720eaa (T-22-2's 3b50fb8/6a8856c excluded)

## Evidence I re-ran
| Command | Result |
|---|---|
| `git archive HEAD` (6a8856c) to scratch; `vitest run` rls-coverage, fk-coverage, rls, authz, shipping/{scan-forms,rate-ttl,label-safety}, integrations/{carriers,vendors}, privacy, orders/purge + my S-38 test (DB invai_t22_3s, Redis 11) | `Test Files 1 failed / 17 passed`, `Tests 1 failed / 112 passed`; the one failure is my S-38 proof test |
| Own API :3163, `packer@` → `scanForms.create`, `verifyAddress` | `403 FORBIDDEN` "Missing permission shipping.manage" (both) |
| `node brute.mjs` (plain node:crypto, digest subject template) | `recovered net profit $12,345.67 in 25684 ms from subjectHash 0dba532b4a4de939` |
| Cleanup | API PID killed, port free; `invai_t22_3s` dropped; Redis 11 flushed; scratch removed |

## Security checks
| Check | Result |
|---|---|
| Buyer name/address in logs, errors, audit, jobs | Clean. `verifyAddress` logs ids + status/`CarrierError.code` only; audit summary is carrier/date/count; no job payloads; EasyPost form download logs host/status only; mock SCAN PDF has no buyer data. |
| `address_verifications` minimisation | Stores status, carrier reason (≤200 chars), time and a keyed HMAC of name+address (`hmacHex(BETTER_AUTH_SECRET, "address-check:v1:<company>:…")`); corrected address never stored. Good. |
| RLS / company_id / composite FKs | Both tables `tenantPolicy` + `ENABLE RLS` in 0032; `address_verifications (company_id, order_id)` composite FK to orders; `scan_forms.shipment_ids` is an array built only from a tenant-scoped query (never input). rls-coverage + fk-coverage green. |
| Permissions | create/verifyAddress `shipping.manage` (owner/admin/office, all hold `orders.manage`, so the returned suggestion stays with roles allowed to see ship-to); list/get `shipping.read`; authz matrix green. |
| SCAN form file key | `scanFormObjectKey(ctx.companyId, …)` = `{companyId}/label/scanform-*.pdf`; download via `files.downloadUrl` company-prefix + `label` kind check; covered by the 30-day `label` purge. |
| No silent charge on re-rate | `buyLabel` re-rates once (`rerated` flag, not client-settable); buys only same carrier+service at the identical cent price, else `RATE_EXPIRED` with 0 buys (rate-ttl.test green). |

## Blocking findings
1. `src/integrations/vendors/mailer.ts` `subjectLogFields()`: `subjectHash = sha256Hex(subject).slice(0,16)` is unkeyed. The digest subject is `"Your week at {{shop}}: net profit {{net}} ({{change}})"` (`digest/render.ts:26`) and the same log line carries `companyId`, so anyone with log access recovers a shop's weekly net profit by hashing guesses (proved above, 26 s on one core). AC5's purpose (B-139) is not met. Fix: `hmacHex(env.BETTER_AUTH_SECRET, "mail-subject:v1:" + subject).slice(0,16)`, as already done for `addressHash`. Proof test (red at 6a8856c, add to `src/lib/security.test.ts` once fixed):
   `expect(subjectLogFields({ subject: s }).subjectHash).not.toBe(sha256Hex(s).slice(0, 16))` → `expected '2c138a096017caef' not to be '2c138a096017caef'`. Recorded S-38 (Medium), owner integrations-engineer, due 2026-10-29.

## Non-blocking (Low, follow-up card for backend-engineer orders/privacy)
- Retention: `purgeBuyerPii` (`orders/jobs.ts:20`) and `redactOrders` (`privacy/service.ts:106`, customers/redact, shop/redact, 18-month sweep) never touch `address_verifications` (grep: no reference); the order row survives, so the cascade never fires. The keyed HMAC of name+address outlives the buyer's PII with no remaining purpose (nothing left to compare) and still lets a key holder confirm a guessed buyer/address. Pseudonymised data is still personal data; delete the row (or null `address_hash`/`detail`) in both paths, with a purge test.
- Shared dev DB `invai` currently lacks `scan_forms` (my packer `scanForms.list` got 500 "Failed query … from scan_forms"); environment state, not code. Tech lead: re-run `db:migrate` when no agent is mid-run.
- `scan_forms.file_key` keeps pointing at a PDF the 30-day `label` purge deleted (download 404s later). Not a leak.
