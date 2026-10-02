# Review of T-26-4 (round 2), security co-review, S-51 only

- Reviewer: security-reviewer on opus
- Author: backend-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/modules/photos src/db/rls-coverage.test.ts src/api/authz.test.ts` | exit 0; 6 files, 56 passed (before my new test) |
| `pnpm typecheck` | exit 0 |
| `git show 790986f -- src/modules/photos/security.test.ts` | one word: `it.fails` → `it` |
| new test in my `security.test.ts`: two `createSet` via `Promise.allSettled` on 8 credits, renders in parallel | passes 3/3 runs; remaining ≥ 0; every `failed` image has `key = null` |
| same file against `790986f~1` (git archive) | S-51 test and concurrent test both fail: `expected -8 to be >= 0` |
| `scan-test-weakening.sh invai-backend 790986f~1` | 1 hit: `vi.mocked(imaging.photoRender)` in `photos.test.ts` (imaging double, not the unit under test); 0 assertions removed |

## Acceptance criteria (S-51)
| # | Met? | Evidence |
|---|---|---|
| Sequential: two 8-composition sets on 8 credits never go negative | Yes | `createSet` subtracts `openCommitments` (`service.ts:63`, `:554`); S-51 test green |
| Concurrent createSets never go negative | Yes | both may pass the unlocked check, but `recordRenders` takes `pg_advisory_xact_lock` then re-reads the balance (READ COMMITTED, read after lock) and voids instead of charging (`:1208`, `:1244`); new test |
| Failed images never charged | Yes | charge needs a `rendered/approved/rejected` image; claim-step and void paths set `failed`, no `chargeCredits` |
| No deadlock from the new lock | Yes | the advisory lock is only taken in `recordRenders`, always as the tx's first lock (prior statements in prep / `failComposition` / job persist are plain selects); holders of set/composition/image locks (`reviewImages :759`, `exportZip :826`) never wait on it, so no cycle |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (service.ts, photos.test.ts; one-word grant in my file)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; none weakened
- [x] Tenancy: `openCommitments` runs inside `withTenant` (RLS scopes the count); no `withSystem`
- [x] Decisions: none; S-51 marked Fixed in `security/v1-review.md`

## Optional notes (not blocking)
- Agree with author gaps: `estimate.canAfford` ignores open commitments (UX only; `createSet` is the gate); voided renders leave files under `<company>/photos/<set>/` (company-prefixed, small; purge with the set).
- Low, before wave 27 scenes: the claim check reads the balance without commitments, so racing sets can render (real provider spend) compositions that are then voided. Shop credits stay correct; our provider cost doesn't. Suggest the claim step take the same advisory lock and count claimed-uncharged compositions.
- My test addition (concurrent test in `src/modules/photos/security.test.ts`) needs `reviewer` + backend-foundation review per my role rules.
