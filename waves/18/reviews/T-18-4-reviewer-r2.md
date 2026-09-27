# Review of T-18-4 (round 2)

- Reviewer: reviewer on sonnet
- Author: ai-engineer on opus
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add /Users/bekbolsun/invai/invai-backend-rev-t18-4 1b57f13` + symlinked `node_modules` | clean worktree at the fix commit |
| `node_modules/.bin/tsc --noEmit -p tsconfig.json` | clean, no errors |
| `node_modules/.bin/biome check .` | `Checked 339 files … No fixes applied.` |
| `createdb -T invai invai_t18_rev_4`; `vitest run src/ai src/modules/ai` (own DB `invai_t18_rev_4`, Redis DB 10) | `Test Files 1 failed \| 7 passed (8)`, `Tests 2 failed \| 128 passed \| 1 skipped (131)` + 1 suite-level throw. All reds in `src/modules/ai/market.acceptance.test.ts` (QA-owned, not a T-18-4 path): AC30 (no R2, mock comparables < 8), AC33 (no R1 for Halloween designs), and the AC8-suite throw ("no mock niche series is rising or falling") — exactly the 3 T-18-2 mock-data reds the author's report names, confirmed against `waves/18/wave.md` "Cross-card findings routed" (line 71) and `reports/QA-acceptance.md` (this file is qa-engineer's, per its own intake note, lines 4-6) |
| `vitest run src/modules/ai/assistant-tools.test.ts src/modules/ai/niche.test.ts src/modules/ai/service.test.ts` | `Test Files 3 passed (3)`, `Tests 72 passed (72)` |
| Round-1 defect check: copied `git show 987b839:src/modules/ai/assistant-tools.ts` over the worktree's file (leaving the new test file at 1b57f13), then `vitest run src/modules/ai/assistant-tools.test.ts -t "T-18-4 r2"` | `Tests 3 failed \| 1 passed \| 32 skipped (36)` — the two named-tool tests and the "every market tool's fallback passes" test fail (`get_market_trend` still returns `missing_sample_label`/`missing_source`); only the "own-cost-only simulation adds no source line" test passes unchanged, as expected (no disclosure needed there) |
| Restored the fixed file, reran the same command | `Test Files 1 passed (1)`, `Tests 4 passed \| 32 skipped (36)` — all 4 new tests pass at `1b57f13` |
| `createdb -T invai invai_t18_rev_4_eval`; `DATABASE_URL`/`MIGRATION_DATABASE_URL` pointed at it, `tsx src/db/migrate.ts` | `[migrate] up to date` (copied-template DB already carries the applied migration state) |
| `tsx evals/market/main.ts --json /tmp/market-eval-1b57f13.json` (mock mode, Redis DB 10) | `Plumbing: 19/21 (90%)`, `Quality: 17/19 (89%)`; only failures `mk-005`/`mk-006` ("get_seasonality … missing October/octubre" — the routed T-18-2 seasonal-shape issue) |
| Diffed the JSON output and `evals/baseline.json`'s `market` route entry | identical: `plumbingPass: 19, qualityPass: 17, cases: 21`, same `byTag` counts — the refreshed baseline is reproducible on a fresh migrated DB |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-backend 987b839` (repo-wide, since 987b839) | Hits found only in T-18-2's files (`src/integrations/market/**`, not this card's paths); `git diff 987b839 1b57f13 -- src/modules/ai/assistant-tools.test.ts \| grep -E "^-.*expect\("` → no output — zero removed assertions in the T-18-4 test file for this fix commit. One "test-only branch" hit inside `assistant-tools.ts` (`if (mock && !SAMPLE_LABEL.test(line))`) is real production logic gating on the tool output's `mock` field, not a test-only shortcut — not blocking |
| `git -C invai-backend diff --stat 987b839 1b57f13 -- src/modules/ai/assistant-tools.ts src/modules/ai/assistant-tools.test.ts src/db/schema/ai.ts evals/baseline.json` | matches `1b57f13`'s own commit stat exactly: 4 files, 201 insertions, 12 deletions — no file outside the fix commit |
| `node_modules/.bin/drizzle-kit generate --name t18_4_rev_check` (after the `CREDIT_KINDS` change) | `No schema changes, nothing to migrate 😴` — confirms `enumText()` (`src/db/schema/_shared.ts:66`) is a TS-only marker, not a pg enum or CHECK constraint, so the added `market_niche` value needed no migration |
| Cleanup | `git -C invai-backend worktree remove ... --force`; `dropdb invai_t18_rev_4`, `dropdb invai_t18_rev_4_eval`; `redis-cli -n 10 FLUSHDB` (via `local-valkey-1`) → `OK`; `git -C invai-backend worktree list` shows only `main` and another agent's `invai-backend-sec-w18` worktree (untouched) |

## Acceptance criteria (round-1 blocking finding only; all others already `yes` per r1)
| # | Met? | Evidence |
|---|---|---|
| 2 / 3a (answer honesty, sample-data disclosure for `get_price_position` unavailable + `simulate_price`) | **yes, now** | New unit tests in `assistant-tools.test.ts` (`get_price_position unavailable with mock comparables names the source, date and 'Sample data'`, `simulate_price with mock comparables names the source, date and 'Sample data'`, `every market tool's fallback passes the answer check when its sources are mock`) all pass at `1b57f13` and fail at `987b839`; `evals/market` mk-003/004/013/018 (previously red on my r1 rerun) are green at 19/21, matching the refreshed baseline |
| 9 (evals baseline accurate) | yes | Baseline (19/21 plumbing, 17/19 quality) reproduces exactly on a fresh migrated DB; remaining mk-005/mk-006 are the already-routed T-18-2 seasonal-mock issue, not this card's |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat 987b839 1b57f13` limited to `src/modules/ai/assistant-tools.ts`+test, `src/db/schema/ai.ts` (grant), `evals/baseline.json`; matches the commit's own stat)
- [x] Nothing outside scope (no touch to `src/modules/market/**`, `trademark.ts`, `src/integrations/**`, `invai-contracts/**`; `CREDIT_KINDS` addition is inside the card's explicit grant, "add job/credit kind values for the niche route", and produced no migration — verified with `drizzle-kit generate`)
- [x] Tests exercise the behavior, and none were weakened (new tests only; zero removed assertions in this card's test file since 987b839; the new tests fail against 987b839's tool file and pass against 1b57f13's)
- [x] Tenancy / idempotency / money / en-es — unaffected by this fix: it only changes answer text formatting inside tools that already passed r1's tenancy and idempotency checks; no new DB reads or writes
- [x] Decisions recorded where needed: the `disclosure()` helper's design (mirrors `sourceLine`'s own regexes so it never double-labels an answer that already names its source) is explained in the code comment and the report; the `market_niche`/`sku_suggestion` credit-kind gap is unchanged from r1 and still tracked for the architect's contract follow-up

## Optional notes (not blocking)
- The three r1 optional notes (unguarded pre-tool-call text window, digit-only number validator, the r1 report's undercounted QA red count) are unchanged this round; still worth a look in a later card but none are new or blocking.
- The report's round-2 section is accurate and specific (names exact file:line-level changes, the sibling `get_market_trend`/`get_seasonality` gap it found on its own via the new all-tools test, and corrects its own r1 baseline claim) — nothing to add.
