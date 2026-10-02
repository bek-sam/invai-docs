# Review of QA/security test suites for T-26-4 / T-26-5 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: qa-engineer (photos.acceptance.test.ts, listing-photos.spec.ts, screens.smoke.spec.ts)
  and security-reviewer (security.test.ts) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-backend && OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/modules/photos` | exit 0; 4 files (contrast, photos, photos.acceptance, security), 43 passed; benign "Vite servers not exiting" teardown message only |
| `cd invai-web && pnpm exec tsc --noEmit -p .` | exit 0, no output |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend e32f9c5~1` | hits only `vi.mock`/`vi.spyOn` on `ai/photo-analysis`, `ai/photo-attach`, `ai/service` and `imaging` (dependencies, not the photos unit under test — same seam as the author's own `photos.test.ts`); 0 assertions removed, 82 added |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web a9a5dc6~1` | no hits; 0 removed, 19 added |
| `grep -n '\.skip\|\.only\|it\.fails\|test\.fail\|fixme'` in all 4 touched test files | none (the one text hit is a code comment referencing a past `it.fails`→`it` grant, not a live skip) |
| `git -C invai-backend diff --stat e32f9c5~1..47a54b3` | `photos.acceptance.test.ts` (new, 517), `security.test.ts` (new+2 edits, 256 net), `photos.test.ts`/`service.ts` touched only by the author's own r2 commit `790986f` (not these two authors) |
| `git -C invai-web diff --stat a9a5dc6~1..a9a5dc6` | `e2e/listing-photos.spec.ts` (new, 112), `e2e/screens.smoke.spec.ts` (+1 line, route entry) |

## Acceptance criteria (test-quality checks, not the product ACs)
| # | Met? | Evidence |
|---|---|---|
| Real behavior, not mocked unit-under-test | Yes | photos.acceptance.test.ts and security.test.ts call `svc.*`/`router.photos.*` directly against `invai_test` with real RLS; only the AI-analysis/attach modules and the imaging HTTP client are doubled, matching the author's own test pattern |
| No `.skip`/`.only`/unfalsifiable markers | Yes | grep clean across all 4 files |
| No leaking shared state | Yes | every test calls `shop()`/`createCompany()` for a fresh tenant; `idempotencyKey` defaults to `crypto.randomUUID()`; no global DB wipe or shared Redis key |
| Only authors' owned paths touched | Yes | QA: `photos.acceptance.test.ts` (backend, card names it as qa-engineer's), `e2e/listing-photos.spec.ts` + one route line in `e2e/screens.smoke.spec.ts` (both e2e, qa-engineer's read/write per T-26-5 card); security: `security.test.ts` only in its two commits |
| Tests pass for real | Yes | backend suite green (43/43); web spec itself not run (route doesn't exist yet per card, expected red until T-26-5 lands — QA's report says so); web `tsc` clean |
| S-51 credit-overcommit regression covered | Yes (already proven by security-reviewer's own r1/r2 files with git-archive-against-base evidence, which I read; current suite re-confirms green) | `security.test.ts:112-163` |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`, see evidence table)
- [x] Nothing outside scope (test files only; no production code touched by QA or by security-reviewer's own two commits)
- [x] Tests exercise the behavior, and none were weakened (no `.skip`, loosened assertions, mocks of the unit under test, rewritten snapshots)
- [x] Tenancy: `security.test.ts` tenancy suite hits `analyzeDesign`/`estimate`/`getSet`/`reviewImages`/`exportZip`/`attachToDraft` with a foreign id → all `NOT_FOUND`; roles suite checks presser/packer/receiver → `FORBIDDEN` on all 8 procedures; idempotency: render-job-twice test asserts exactly one ledger row per composition
- [x] Decisions: none needed

## Optional notes (not blocking)
- `invai-web/e2e/listing-photos.spec.ts` can't be run yet (web screen not built); verification here was limited to `tsc --noEmit` per instructions. It should be re-run as part of the T-26-5 web-engineer review/gate once the route exists.
- `photos.acceptance.test.ts:271` (`toHaveLength(2)`) and a few other exact-count assertions are tightly coupled to the fixture's 2 garments × 2 colors × 1 back-eligible view; fine as written, just noting for future fixture changes.
