# Review of T-29-1 (round 1)

- Reviewer: reviewer on Fable 5.1
- Author: backend-engineer on opus (backend 63682ed, 2529441; docs cb012d1)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `vitest run --reporter=dot src/modules/privacy src/modules/orders/purge.test.ts src/modules/personalization/purged.test.ts src/modules/production/purged-artwork.test.ts src/db/rls-coverage.test.ts src/api/authz.test.ts` (invai_test + real MinIO) | exit 0; 10 files, 54 tests passed; S-56 passes as `it` |
| `biome check` on the 11 changed files | 11 files, no diagnostics |
| `pnpm typecheck` (main tree) | 1 error, only in `channels/webhook-auto-import.test.ts` (another builder's uncommitted edit, out of this card); `tsc --noEmit` in a clean worktree of 2529441: exit 0 |
| `scan-test-weakening.sh invai-backend 47ce0ee` | removed assertions all in T-29-2/T-29-4 files; this card: +103 assertions, mocks only on deps (`lib/s3.deleteObject`, imaging client); `it.fails` -> `it` allowed by the card |
| New tests on 95324fe (worktree, removed) | 13 of 17 red (`redactBuyerText is not a function`, assertion failures); 4 green = 2 pre-existing purge tests + 2 guard tests, covered by mutations below |
| Mutation A: drop item-state filter (`privacy/service.ts:210`) | "keeps a unit still in production" red (expected text, got null) |
| Mutation B: drop clock (`orders/jobs.ts:71` -> `.where(unredacted)`) | "keeps everything inside the clock" and "cancelled_at clock" red |
| Mutation C: drop failed-delete skip (`privacy/service.ts:306`) | "leaves a unit whose delete failed" (30-day) and "passes over an order" (18-month) red |
| Mutation D: `withTenant` -> `withSystem` in the job (`jobs.ts:106`) | tenant test still green (per-company id grouping confines writes; see note 1) |
| Probe test (scratch, removed): shared `{c}/artwork/` key, `{c}/design/` key, another company's key on shipped units; then redact the last owner | keys nulled + `purged`, all 3 objects kept, `files: []`; last owner's redact deletes `shared` + `solo` |
| `git show --stat 63682ed 2529441` | 11 paths, all inside owned globs; no uncommitted work of this card |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | purge.test.ts per-unit, pii-already-gone, cancelled clock; mutations A, B; `sheets.ts:169` needs rendered/approved key + `production/purged-artwork.test.ts` (ready + reprint -> `needs_artwork`) |
| 2 | yes | purge.test.ts: 5 note kinds null, reason `misprint` and 500 cents kept; vendor/station notes untouched (0027 keep list) |
| 3 | yes | buyer-text.test.ts redact + 18-month (`ready` unit cleared); security.test.ts S-56 green as `it` |
| 4 | yes | purged.test.ts: approve -> CONFLICT, `updateArtworkValues` re-enters to `approved`; batch preview excludes both units |
| 5 | yes | purged.test.ts: old render 404 after re-render, new one present; prefix guard; `afterCommit` at service.ts:536 |
| 6 | yes | run-twice in purge/buyer-text tests; tenant test + RLS probe (`redactBuyerText` under company B with A's ids -> zeros); mutation C; `handlePrivacyRequest` throws on `failedFiles` so the delivery retries |
| 7 | yes | "keeps everything inside the clock"; mutation B proves the clock is load-bearing |
| 8 | yes | decisions/0027 lists fields, 3 clocks, keep list with reasons, 0026 narrowing, 3 gaps with owners, links; README row |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope (no web/floor, no migration: column is text)
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy (`withSystem` reads ids only with a reason comment; all writes in `withTenant`; `isCompanyKey` on every deleted key), idempotency (second run: zeros), money kept in cents, no en/es strings added, no PII in logs
- [x] Decisions recorded (0027 proposed; security + compliance to accept)

## Optional notes (not blocking)
1. The job's tenant test cannot tell `withTenant` from `withSystem` (mutation D). Fine today because ids are grouped per company; a stronger test would give company B a due order and assert both purge in one run.
2. Storage-first order inside one unit: render and preview are deleted before the photo, so a failed photo delete leaves an `approved` unit (scope `all`) whose `artworkKey` object is already gone until the next run. Card-designed ("keeps its keys and status"); deleting the render last would shrink the window.
3. No separate tsx script was re-run; the tests put real objects in MinIO and assert 404s against `invai_test`, which I count as the real exercise.
