# Review of T-20-1 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: backend-engineer on Opus 5.5
- Commits reviewed: `invai-backend` `076dd69` (author's round-2 fix) and `d6a19f1` (QA's acceptance-file fix)
- Verdict: **approve**

## Context
Round 1 (`T-20-1-reviewer-r1.md`, `T-20-1-product-manager-r1.md`) both landed on the same single
blocking finding: `facts.ts`'s `signedPts` used a bare `es` locale for Spanish point changes
("+6,9 pts", decimal comma), which is the only place in the digest that doesn't follow the file's own
`LOCALE` map (`es-US`, period decimal) used for money, counts and relative percent. The PM's r1 review
recorded the fix as a decision in `specs/weekly-digest.md` (2026-09-28): Spanish points use `es-US`,
"+6.9 pts", identical to English. Everything else in round 1 (R1 timing AC1/AC2, mock `asOf` AC4, the
Today alert AC5, scope, ownership, tenancy) was already sound.

This is a fresh round-2 review (the previous reviewer run was lost to a usage-limit stop before
writing anything); I read the card, both r1 review files and the diff cold, per `independent-review`.

## Evidence I re-ran
Own DB `invai_t20_rev1b` (dropped after), Redis DB 10 (flushed after). `T-20-5`'s uncommitted WIP
(`src/db/reset.ts`, `src/db/reset.test.ts`, `src/db/seed/builder.ts`, `src/modules/README.md`,
untracked `src/db/seed/sweep-race.test.ts`) is sitting in the same working tree — confirmed with
`git -C invai-backend status --short` before touching anything. That WIP is unrelated to this card's
owned paths (market/digest/today) and I excluded its failures below as instructed.

| Command | Result |
|---|---|
| `git -C invai-backend status --short` | Confirms only T-20-5's WIP is uncommitted; nothing of mine or the author's |
| `git -C invai-backend log --oneline -5` | `076dd69` (T-20-1 r2) on top of `d6a19f1` (QA r2) on top of `8814acb` (QA's wave-18 acceptance fix, already judged correct in r1) on top of `8fdc733` (T-20-5, unrelated) on top of `bfae180` (T-20-1 r1) |
| `git -C invai-backend show --stat 076dd69` | `src/modules/digest/facts.ts` (8 lines), `src/modules/digest/pure.test.ts` (4 lines) — both inside the card's owned digest globs |
| `git -C invai-backend show --stat d6a19f1` | `src/modules/digest/date-copy.acceptance.test.ts` (4 lines) — QA's own acceptance file, not the author's to touch, correctly committed separately |
| `pnpm typecheck` (invai-backend) | Fails with 2 errors, both in `src/db/seed/sweep-race.test.ts` (`Property 'size' does not exist on type 'never'`) — that file is untracked, belongs to T-20-5, and is nowhere near this card's owned paths. Excluded per the task's instruction. No errors in any digest/market/today file |
| `pnpm lint` (biome) | `Checked 395 files in 240ms. No fixes applied.` — clean, includes T-20-5's WIP files (biome doesn't fail on them) |
| `TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_t20_rev1b TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_t20_rev1b REDIS_URL=redis://localhost:6379/10 pnpm vitest run src/modules/digest src/modules/market src/modules/today src/integrations/market` | `Test Files 21 passed \| 2 skipped (23)`, `Tests 244 passed \| 3 skipped \| 1 todo (248)` |
| same env, `pnpm vitest run src/modules/digest/date-copy.acceptance.test.ts --reporter=verbose` | `Test Files 1 passed (1)`, `Tests 7 passed (7)` — all of QA's AC1–AC5 acceptance tests green, including the two just-updated Spanish-points assertions (AC3) |
| `git -C invai-backend diff --stat 076dd69~1 076dd69` and `d6a19f1~1 d6a19f1` | 2 files + 1 file, all inside owned/QA paths, no scope creep |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend d6a19f1~1` | Deleted-assertion hits are all the expected comma→period value swaps in `pure.test.ts` and `date-copy.acceptance.test.ts` (exact-match assertions still exact-match, just corrected values — not a loosening), plus unrelated hits in T-20-5's `src/db/reset.test.ts` WIP, excluded. No skips, no mocks of the unit under test, no snapshot rewrites |
| Red-for-the-right-reason: copied `pure.test.ts` from `076dd69` onto the pre-fix tree (`076dd69~1`) and ran it | Both round-2 assertions fail on the old code: `expected '(+6,9 pts...)' to contain '(+6.9 pts...)'` and `expected {es:'-6,9 pts'} to equal {es:'-6.9 pts'}` — the fix is proven, not vacuous |
| `node -e 'console.log(new Intl.NumberFormat("es-US",{minimumFractionDigits:1,maximumFractionDigits:1,signDisplay:"exceptZero"}).format(6.9))'` | `+6.9` — confirms `LOCALE.es = "es-US"` (unchanged, `facts.ts:11`) now drives `signedPts` too, since `PTS_LOCALE` was deleted and `signedPts` reads `LOCALE[lang]` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 No past peak | Yes (unchanged from r1, re-confirmed) | `date-copy.acceptance.test.ts` AC1, both tests green |
| 2 Peak under way | Yes (unchanged from r1, re-confirmed) | `date-copy.acceptance.test.ts` AC2 green |
| 3 Points, not relative percent | **Yes, now** | `pure.test.ts` en "+6.9 pts" / es "+6.9 pts" (period, both languages); `date-copy.acceptance.test.ts` AC3 both tests green with the corrected es assertions; `facts.ts:87-96` `signedPts` uses `LOCALE[lang]` (`es-US`), no more `PTS_LOCALE` |
| 4 Mock source date | Yes (unchanged from r1, re-confirmed) | `date-copy.acceptance.test.ts` AC4 green |
| 5 Today alert | Yes (unchanged from r1, re-confirmed) | `date-copy.acceptance.test.ts` AC5 green |
| 6 Existing tests stay green | Yes | 244/248 (3 skipped, 1 todo, 0 failed) on a clean two-agent-free run; the wave-18 acceptance test QA fixed in `8814acb` (already judged correct in r1) still passes |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` on both commits: `digest/facts.ts`, `digest/pure.test.ts` — author's owned globs; `digest/date-copy.acceptance.test.ts` — QA's own file, committed separately)
- [x] Nothing outside scope (no contract, web, other-module, or unrelated file touched by either commit)
- [x] Tests exercise the behavior, none weakened (scan clean apart from the expected value corrections; red-for-the-right-reason confirmed on the two new/changed assertions that carry the round-2 proof)
- [x] Tenancy / idempotency / money-in-cents / sizes-in-inches — not applicable, no side effects, no schema, no money or sizes touched by this diff
- [x] en/es text — Spanish points now match the digest's one `es-US` convention; no mixed-separator line remains in the reviewed diff
- [x] Decisions recorded where needed — the PM's r1 decision lives in `specs/weekly-digest.md`; the PM's r2 review (`T-20-1-product-manager-r2.md`) independently confirms `076dd69`/`d6a19f1` close it and approves

## Optional notes (not blocking)
- The PM's r2 review also checked the web's R1 peak-under-way fallback and the `invai-web` es-US widening for consistency across cards; both are outside this card's owned paths and are covered by my separate T-20-2 round-2 review.

## Disposition
Round 1's sole blocking finding (Spanish points decimal comma) is fixed exactly as specified by both
the reviewer's and the product-manager's round-1 reviews, in the author's owned files plus QA's own
acceptance-file correction. All tests pass on a clean re-run isolated from T-20-5's uncommitted WIP.
No new findings. **Approve.**
