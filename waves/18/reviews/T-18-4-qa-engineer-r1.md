# Review of T-18-4 (round 1, qa-engineer co-review)

- Reviewer: qa-engineer on Opus (this session)
- Author: ai-engineer on opus
- Verdict: **approve**

Scope of this co-review (per the tech lead's dispatch, wave 18 QA lens): commits `25b1b9e..1b57f13`
(T-18-4's commits, listed below), whether QA's `src/modules/ai/market.acceptance.test.ts` passes at
HEAD, and whether the existing (wave 17) assistant golden-path behavior is unchanged. The primary
reviewer (`T-18-4-reviewer-r1.md` changes-required, `T-18-4-reviewer-r2.md` approve) and
security-reviewer (`T-18-4-security-reviewer-r1.md` approve) already cover the full acceptance-criteria
table, tenancy/injection checks and the round-1→round-2 defect fix in depth; this review doesn't
repeat that work, only adds the QA-specific evidence the card asks for.

T-18-4's own commits in range: `25b1b9e` (niche stub, day 1), `54640f2` (tools, gateway answer
check, niche route, prompt v5, service pass-through), `4a76268` (market eval set), `5e398dc`
(trademark threshold 60), `fb89c1f` → `f0a4685` (seasonal-prep R1 copy), `74268c3` (message order
tie-break), `987b839` (eval baseline), `1b57f13` (round-2 fix: disclose mock sources in the
fail-closed fallback).

## Evidence I re-ran

| Command | Result |
|---|---|
| `git -C invai-backend log --oneline 25b1b9e..1b57f13` | matches the 9 commits the author's report names, in the same order |
| `git -C invai-backend diff --stat 987b839~7..1b57f13 -- <every path this card owns or is granted>` | every touched file (`src/ai/**`, `src/modules/ai/{assistant-tools,niche,service}.ts`+tests, `evals/**`, `src/db/schema/ai.ts`) is inside T-18-4's owned/granted paths; no touch to `src/modules/market/**`, `trademark.ts`, `src/integrations/**` or `invai-contracts/**` |
| `node_modules/.bin/tsc --noEmit -p .` (repo-wide, at HEAD `0fce415`, after my own wave-18 QA fixture commit) | clean, 0 errors |
| `node_modules/.bin/biome check .` (repo-wide) | `Checked 343 files … No fixes applied.` |
| Own test DB `invai_t18_rev_4`, Redis DB 10: `vitest run src/modules/ai/assistant-tools.test.ts src/modules/ai/niche.test.ts src/modules/ai/service.test.ts src/ai/answer-guard.test.ts src/ai/validators/answer.test.ts src/ai/ai.test.ts src/ai/breaker.test.ts src/modules/ai/market.acceptance.test.ts` | `Test Files 8 passed (8)`, `Tests 131 passed (131)` — includes my (QA-owned) `market.acceptance.test.ts`, fixed in my second pass earlier the same session, now green at HEAD |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-backend 987b839` | hits span the whole repo since `987b839` (includes T-18-2's and my own unrelated later QA commit, both outside this card); scoped instead to `git diff 987b839~7..1b57f13 -- <T-18-4 paths> \| grep -E "^-.*expect\("` |
| Scoped removed-assertion check (above) | 2 hits, both explained: `MARKET_TERM_MAX_RISK` 25→60 (the threshold itself changed, with the author's measured rationale in `5e398dc`'s message and `niche.test.ts`'s new "keeps real niche terms that only fuzzily resemble a mark" case); an exact-string `out.answer` assertion replaced by a more precise `out.meta?.recommendations?.map(id)` check plus new cases in the same test (`f0a4685`) — a tightening, not a loosening |
| Own test DB `invai_t18_rev_4`, Redis DB 10: `vitest run` (full backend repo suite, no filter) | `Test Files 114 passed (114)`, `Tests 928 passed (928)` — every backend test in the repo, at HEAD `0fce415`, is green |
| Cleanup | dropped `invai_t18_rev_4`; flushed Redis DB 10 |

## My AC → test check

The card's own criteria are already scored in `T-18-4-reviewer-r2.md`'s table; the two I can verify
independently from my QA seat:

| # | Met? | Evidence |
|---|---|---|
| My `ai/market.acceptance.test.ts` passes at HEAD | **yes** | 9/9, run above, on `invai_backend` HEAD `0fce415` (T-18-2 round 2, T-18-3 incl. S-34, T-18-4 round 2 all landed). This file needed my own second-pass fixture fixes first (price cents, THIN-cost/fee-schedule mismatch); once fixed, it is green against T-18-4's code unmodified. |
| Existing (wave 17) assistant golden-path behavior unchanged | **yes** | `src/modules/ai/service.test.ts` and `src/modules/ai/assistant-tools.test.ts` (non-market cases) pass unchanged; the message-order fix (`74268c3`) has its own regression test (`service.test.ts`, fails on `f0a4685`'s code per the author's report, passes at `74268c3`) for the intermittent T-17-3 failure it fixes. No wave-17 assistant test was deleted, skipped or loosened in this range. |

## Blocking findings

None.

## Checks

- [x] Only owned paths changed (see "Evidence I re-ran"; the `CREDIT_KINDS`/`market_niche` addition
  to `src/db/schema/ai.ts` is inside the card's written grant, produced no migration)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened in T-18-4's own commit range (2 removed
  assertions, both explained above as tightenings/threshold updates, not loosenings)
- [x] Tenancy / idempotency / money / en-es — covered by the primary and security reviews; my run
  adds no new finding here
- [x] Decisions recorded where needed — unchanged from r2 (the `market_niche`/`sku_suggestion`
  credit-kind gap is tracked, waiting on the architect's contract follow-up)

## Optional notes (not blocking)

- The report's "Known gaps" section still lists the real-model eval as waiting on OI-8, and the
  T-18-2 mock-seasonality gap (mk-005/mk-006) as routed, not this card's — both match `wave.md`'s
  "Cross-card findings routed" and my own second-pass findings; nothing new to add.
- I did not additionally run the browser E2E golden path for this card (`invai-web`'s
  `golden-path.spec.ts`/`screens.smoke.spec.ts`); per the dispatch, that is the integration gate's
  job, not this co-review's.
