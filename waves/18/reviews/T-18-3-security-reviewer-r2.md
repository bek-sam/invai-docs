# Review of T-18-3 (round 2)

- Reviewer: security-reviewer on claude-sonnet-5
- Author: backend-engineer (market) on claude-opus-5-5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 72e3e59 -- src/modules/market/service.test.ts` | Confirms the round-1 finding is fixed: `demandProvider()` now takes an `onQueries` capture hook that records the exact `queries` array passed into each provider's `series()` before any test-only `extra` is mixed in; the test asserts `expect(fetchedQueries.census).toBeUndefined()` and `expect(new Set(fetchedQueries.google_trends)).toEqual(CANONICAL_QUERIES)`, plus the same Set-equality on the stored non-census rows. The pre-existing containment loop (`for (const r of qs) ... expect(CANONICAL_QUERIES.has(r.q))`) is kept, not removed |
| Worktree `../invai-backend-sec-w18` (detached HEAD `1b57f13`, which contains `72e3e59`), own DB `invai_t18_sec`, Redis DB 9: `vitest run src/modules/market/service.test.ts -t "refreshDemand stores only taxonomy queries"` | 1 passed \| 25 skipped — the strengthened test passes against the shipped code |
| Same worktree, `sed`-equivalent one-line edit to `src/modules/market/jobs.ts:99` (uncommitted): `const queries = [...CANONICAL_QUERIES].slice(0, Math.floor(CANONICAL_QUERIES.size / 2));` (simulates the exact S-34 regression — a subset apparently derived from tenant-used niches), then re-ran the same `-t` filter | 1 **failed** on `expect(new Set(fetchedQueries.google_trends)).toEqual(CANONICAL_QUERIES)` (diff showed dozens of taxonomy queries missing from the captured set) — proves the new assertion, not just today's implementation, is what stops the regression |
| Restored `jobs.ts` from `git show HEAD:src/modules/market/jobs.ts`, re-ran the same filter | 1 passed \| 25 skipped again; `git diff --stat HEAD -- src/modules/market/jobs.ts` empty — no residual change left in the worktree |
| Same worktree: `vitest run src/modules/market/service.test.ts src/modules/market/engine.test.ts src/db/rls-coverage.test.ts src/api/authz.test.ts` | 4 files, 75 passed — nothing else regressed by the round-2 diff |
| `git -C invai-backend show --stat 72e3e59` | Only `src/modules/market/service.test.ts` changed (33 lines, +30/−3); no product code, no other test files |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 2b / S-34 ("A test asserts the fetched query set equals the taxonomy's") | yes | `service.test.ts:518-534` now asserts Set-equality on the captured `series()` argument, not just containment on stored rows; confirmed it both passes on the real code and fails when the code is regressed (above) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat 72e3e59`: `src/modules/market/service.test.ts` only, the file the round-1 finding named)
- [x] Nothing outside scope (test-only change; no product code touched, matching the report's claim)
- [x] Tests exercise the behavior, and none were weakened — this is a strengthening (containment kept, equality added), the opposite of weakening; scanned for `.skip`/`.only`/loosened assertions in the diff, found none
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — unaffected by this round's diff; already verified in round 1
- [x] Decisions recorded where needed — S-34 closed in `invai-docs/security/v1-review.md` with this review's evidence linked

## Optional notes (not blocking)
- The report's round-2 section accurately describes both the change and why: `jobs.ts:97-131` already built `queries` unconditionally from `CANONICAL_QUERIES` with no tenant input, so this was a test-coverage gap, not a live implementation bug — matching what I found in round 1 (`s34.security.test.ts`, proof-only, discarded with that worktree).
- My round-2 mutation (`jobs.ts` narrowed to half the taxonomy) was made only in my own detached worktree (`../invai-backend-sec-w18`), never touched the shared `invai-backend` tree, and was restored via `git show HEAD:<path>` (no `git checkout`, per the guard hook) before I finished. `git diff --stat HEAD` on that path is empty.
- S-34 closed in `invai-docs/security/v1-review.md` (Low counts now 8 fixed / 6 open, from 7/6).
