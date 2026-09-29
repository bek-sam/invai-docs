# Review of T-22-3 (round 2): security co-review, S-38 fix only

- Reviewer: security-reviewer on opus 5.5 · Author: integrations-engineer on opus
- Verdict: **approve**. S-38 is fixed; set to Fixed (invai-backend@2466954) in `security/v1-review.md`.
- Scope: invai-backend 2466954 (`src/integrations/vendors/mailer.ts`, `mailer-subject.test.ts`) only; both inside the card's owned paths.

## Evidence I re-ran
| Check | Result |
|---|---|
| Hash is keyed | `subjectHash: hmacHex(env.BETTER_AUTH_SECRET, mail.subject).slice(0, 16)`; `hmacHex` = `createHmac("sha256", secret)` (`src/lib/crypto.ts:105`). Same pattern as `addressHash`. |
| `vitest run --reporter=dot src/integrations/vendors` (DB invai_t22_3s2, Redis 11) at 2466954 | `Test Files 2 passed (2)`, `Tests 5 passed (5)` |
| New test on base 6a8856c (`git archive`, test copied in) | FAIL: `expected '2c138a096017caef' not to be '2c138a096017caef'` (1 failed / 2 passed), so it fails on the old code |
| Round-1 proof re-run (plain node:crypto, digest subject, cents 0..2,000,000 × 5 change strings) | `10000005 candidates in 197239 ms; recovered from old sha256 hash: 1; from new HMAC hash: 0` |
| Cleanup | `invai_t22_3s2` dropped, Redis 11 flushed, scratch files removed; no process left running |

## Blocking findings
none

## Optional notes
- Pre-existing (8b9b6f0, T-19-4, not this card): the same log line's `toHash: sha256Hex(mail.to…)` is unkeyed, so anyone holding a candidate email list can confirm recipients. Low; suggest the same `hmacHex` change on a follow-up card (integrations-engineer). Round-1 retention note (`address_verifications` not purged) still stands as a follow-up for backend-engineer.
