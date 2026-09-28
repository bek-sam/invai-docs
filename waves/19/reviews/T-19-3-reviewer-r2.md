# Review of T-19-3 (round 2)

- Reviewer: reviewer on sonnet
- Author: backend-engineer (digest) on opus
- Verdict: approve

## Evidence I re-ran
All in a fresh worktree (`git -C invai-backend worktree add /Users/bekbolsun/invai/invai-backend-rev-t19-3b cfe1098`, `node_modules` symlinked), own scratch DB `invai_t19_rev_3b` (`TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` in the worktree's `.env`, per the existing convention: `src/env.ts` prefers these under `NODE_ENV=test`), own Redis db 10. Worktree removed and DB dropped and Redis db 10 flushed at the end (see Processes and data).

| Command | Result |
|---|---|
| `git -C invai-backend show cfe1098 --stat` | 2 files: `src/modules/digest/render.ts`, `src/modules/digest/pure.test.ts` — both inside the module the card owns |
| `git -C invai-backend show cfe1098 -- src/modules/digest/render.ts` | read in full; the fix replaces `channels \|\| channel` (where `channel` could itself be `""`) with `channels \|\| TEMPLATES["market.channels.connected"][lang]`, and adds that new template key with en/es text |
| Read `invai-web/src/components/market/recommendation-copy.ts:50` and `invai-web/src/i18n/en.ts:1005`/`es.ts:1024` | web's own R1 fallback: `t("market.channels.connected", "your connected channels")`; catalog text is `"your connected channels"` (en) / `"tus canales conectados"` (es) — **verbatim match** to the backend's new `TEMPLATES["market.channels.connected"]` in both languages |
| `node_modules/.bin/tsc --noEmit` (worktree) | clean |
| `node_modules/.bin/biome check src/modules/digest` (worktree) | "Checked 22 files in 54ms. No fixes applied." |
| `node_modules/.bin/vitest run src/modules/digest --exclude '**/*.acceptance.test.ts'` (worktree) | "Test Files 3 passed \| 1 skipped (4)", "Tests 43 passed \| 2 skipped (45)" |
| Red-for-the-right-reason: `git checkout HEAD~1 -- src/modules/digest/render.ts` in the worktree (pre-fix code, new test file already present from HEAD), `vitest run src/modules/digest/pure.test.ts -t "R1 channel-list fallback"` | 1 of 3 new cases fails exactly as expected: `expect(en.vars.channels).toBe("your connected channels")` → received `""` (the empty-channel case); the other two new cases (several channels / exactly one channel) pass unchanged on old code, since they never exercised the buggy fallback branch — restored the file to HEAD content afterward (verified `diff` against `git show HEAD:...` was empty before re-running the full suite green) |
| `.claude/skills/independent-review/scan-test-weakening.sh <worktree> HEAD~1` | "Result: no hits" (assertions only added: `removed=0, added=10`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 6 Market watch (R1 rendering) | **yes (fixed)** | R1's channel-list clause no longer renders blank ("List X on  and stock...") when a promotable candidate has neither `params.channels` nor a `target.channel`/`params.channel`; it now falls back to "your connected channels" / "tus canales conectados", matching the wording web already uses for the same gap in `recommendation-copy.ts` |
| 7 Templates en/es | **yes (reconfirmed)** | new template key follows the same `TEMPLATES` shape and P1 convention (fixed key + allow-listed values) as every other template row; both languages present |
| All other criteria (1-5, 8-12) | yes | unchanged since r1 (`T-19-3-reviewer-r1.md`); this round's commit touches only `render.ts`'s `R1` case and adds unit tests, nothing else in the module |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show cfe1098 --stat`: `src/modules/digest/render.ts`, `src/modules/digest/pure.test.ts`, both inside this card's owned module)
- [x] Nothing outside scope — the author checked R2-R5 for the same combining-fallback pattern and correctly found none needed the same fix (confirmed by reading `marketPart`'s other cases: none use `x || y` on two possibly-empty strings the way R1 did)
- [x] Tests exercise the behavior, and none were weakened — all new assertions are additions (`removed=0, added=10`); the one case that exercises the actual bug fails for the right reason on the pre-fix code (see Evidence), the other two (several/one channel) are regression coverage that already passed
- [x] Tenancy / idempotency / money / en-es — pure rendering function, no DB or tenant access in this diff; en/es text added and verified to match web's own copy for the same fallback concept
- [x] Decisions recorded where needed — none needed; this is a same-module bug fix with no cross-cutting shape change (the new `TEMPLATES` key is additive, no contract change)

## Optional notes (not blocking)
1. This finding was originally surfaced by the product-designer's T-19-5 round-1 review as a live artifact ("List Arizona Est. 1912 on  and stock…") and independently reached by T-19-5's own round-2 report tracing it to this exact line before this card's fix landed — both sides now agree on the fix and the wording; confirmed no divergence remains between the backend template and web's fallback text.
2. Verified the fix's wording choice ("your connected channels") reads naturally as a *generic* plural in both languages even though the actual R1 rule (`specs/market-signals.md`) is meant to always have a channel gap by construction — i.e. this is defense-in-depth for the mock/data-artifact case the product-designer observed, not a change to when R1 fires. No action needed.
