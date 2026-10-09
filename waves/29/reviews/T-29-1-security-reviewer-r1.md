# Review of T-29-1 (round 1), security co-review

- Reviewer: security-reviewer on Opus 5.5 (flags pii, tenancy, files, data deletion)
- Author: backend-engineer on opus (backend 63682ed, 2529441; docs cb012d1)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `vitest run --reporter=dot src/modules/privacy src/modules/orders/purge.test.ts src/modules/personalization src/modules/production/purged-artwork.test.ts src/db/rls-coverage.test.ts src/db/rls.test.ts src/api/authz.test.ts` (invai_test, MinIO, `REDIS_URL=.../12`) | exit 0; 14 files, 69 passed; S-56 proof passes as `it` |
| `vitest run src/modules/privacy/security.test.ts` (with my 2 new tests) | 2 passed, 1 expected fail (S-59) |
| S-59 test without `.fails` | red at `security.test.ts:135`: photo object gone (expected false to be true) |
| Mutation in a scratch copy (`/private/tmp`, removed): drop `isCompanyKey` + photo prefix check in `redactBuyerText` | new control test "never deletes another company's objects" goes red |
| `tsc --noEmit`, `biome check` on my test file | clean |

## Threat model (who, what session, whose data, worst outcome)
- Entry points: nightly `purgeBuyerPii` and `redactStaleBuyerPii` (system jobs), `handlePrivacyRequest` (verified Shopify webhook), `personalization.artwork.approve/update` (session, permissioned, contract unchanged). No new procedure, so authz matrix is unchanged (green).
- Tenant source: company ids read as system (`withSystem` reads ids only, reason comment at `orders/jobs.ts`); every read, delete and update runs in `withTenant(companyId)`, so RLS confines the item, artwork, reprint, refund and "shared key" queries.
- Cross-tenant deletion: every deleted key passes `isCompanyKey(item.companyId)`; item keys only under `{company}/artwork/` and only when no other unit points at them; photo keys only under `{company}/photo/`. Proven by my new control test plus mutation. Worst case found: same-company photo reuse (S-59, Low).
- Units in production: scope `shipped-items` filters `shipped/delivered/cancelled` (reviewer mutation A). A unit purged while reprinted shows `needs_artwork` via `sheets.ts:169`; `approve` on purged answers CONFLICT.
- Failed delete: storage first; the unit keeps keys and status and is reselected next night; the redact webhook rolls back and retries. Missing-object deletes are idempotent in S3.
- Leftovers checked: outbox `artwork.*` events carry ids/codes only; `audit_log` flags, gang sheet files and pre-T-29-1 orphan renders are recorded gaps in 0027.

## Acceptance criteria (security view)
| # | Met? | Evidence |
|---|---|---|
| 1, 3, 7 | yes | purge.test.ts, buyer-text.test.ts, S-56 proof green; reviewer mutations A, B |
| 2 | yes | five note kinds null in purge.test.ts; enum reasons and cents kept |
| 4, 5 | yes | personalization/purged.test.ts, production/purged-artwork.test.ts green |
| 6 | yes | run-twice and storage-failure tests green; tenant isolation by my cross-company key test |
| 8 | yes | 0027 read; accepted by security (status set accepted, compliance already approved) |

## Blocking findings
none

## Findings recorded
- S-56: marked Fixed in `security/v1-review.md` (63682ed, 2529441, verification above); DPP 18-month row updated.
- S-59 (Low, new, open, owner backend-engineer privacy): photo-slot keys are deleted without the "no other unit uses it" check that item keys get. Proof `privacy/security.test.ts` (`it.fails`). No DPP clock.

## Optional notes
1. 0027 does not say that a manual "replace artwork" upload under `{company}/artwork/` (not shared) is deleted with the unit; the compliance review asked for the same line. Add it next time 0027 is touched.
2. Reviewer notes 1 and 2 agreed: not blocking (writes are per company in `withTenant`; the dead-key window self-heals next night).
3. A re-render committed between the purge's read and its update leaves the new render orphaned (no row points at it). Narrow race on shipped units; same family as the legacy-orphan sweep backlog line.
