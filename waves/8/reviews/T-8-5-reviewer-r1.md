# Review of T-8-5 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: ai-engineer on Sonnet 5 (commit co-author line)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show --stat d3bbc80` | 19 files changed: `evals/**` (new), `package.json`, `.github/workflows/ci.yml`, `README.md` — matches owned files |
| `git -C invai-backend diff origin/main d3bbc80 -- package.json .github/workflows/ci.yml` | `"evals": "tsx evals/run.ts"` added; ci.yml gets one `pnpm run --if-present evals` line right after `test`, with a comment noting no `ANTHROPIC_API_KEY` there |
| `git -C invai-backend diff d3bbc80 HEAD --stat` | later commits (T-8-2 fix, T-8-1) touch only `src/ai/**`/`src/modules/ai/**`; no `package.json`/lockfile drift, so the worktree's symlinked `node_modules` is valid for d3bbc80 |
| `git worktree add ../invai-backend-t85-review d3bbc80` + symlink `node_modules`, copy `.env` (`ANTHROPIC_API_KEY=` blank) | worktree built cleanly |
| `node_modules/.bin/tsx evals/run.ts` (= `pnpm evals`) | `mode: mock (no ANTHROPIC_API_KEY)`; listing_copy 21/21, trademark_judge 14/14, assistant 16/16 plumbing; personalization_check skipped (13 staged); `Overall plumbing: 51/51 (100%)`; **exit 0** |
| same, redirected, `echo $?` | `EXIT=0` |
| `node_modules/.bin/tsx evals/run.ts nonexistent_route` | `Unknown route "nonexistent_route". Known routes: ...`; **exit 1**, no hang (confirms the report's `closeResources()`-on-every-path fix) |
| `docker exec local-postgres-1 psql -U invai -d invai -c "select count(*) from companies where name like 'Eval harness%';"` | **13** — confirms the report's disclosed gap: nothing deletes the throwaway tenant |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits are all pre-existing test files from other in-flight cards, or the mock-provider selector pattern (`if (env.mocks.ai) return mockProvider`) that predates this card; the one T-8-5 hit is the intended `ci.yml` addition itself, not a loosening |
| `git worktree remove ../invai-backend-t85-review --force` | removed |
| `docker exec local-postgres-1 psql ... delete from companies where id in (<my 2 run's ids>)` | `DELETE 2` — cleaned up my own eval-tenant rows, left the other 11 (not mine) |

Read (not re-run as commands): `evals/run.ts`, `evals/lib/{fixtures,gateway-run,jsonl,stats,report,types}.ts`, all four `<route>/run.ts`, all four `cases.jsonl`, `README.md`'s new section, `evals/baseline.json`.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Harness, one eval set/route, ≥10 cases, PII-scrubbed | Yes | `evals/run.ts` + 4 route dirs; 21/14/16/13 cases. All four `cases.jsonl` read in full: invented shop/product/message text (design names, briefs, trademark strings, assistant questions); no real buyer names, emails, addresses. `evals/lib/fixtures.ts` reuses `src/test/fixtures.ts`'s synthetic company/user/location generators (`test-<uniq>@test.local`), same as unit tests |
| 2. Scoring (schema+rules or judge), prints pass rate/cost/latency | Yes | Each route's `run.ts` does gateway schema validation + a deterministic rule check (`validateListing`; judgement cardinality/mark-fidelity; tool-selection/content); no separate LLM-judge call, which AC2's "or" permits. Actual run output above shows pass rate, cost (median/p95 ¢), latency (median/p95 ms), cache-hit% per route |
| 3. Mock mode auto-detected, checks plumbing, no key needed | Yes | Local run above with blank `ANTHROPIC_API_KEY` printed `mode: mock`, ran all mock calls, exit 0; `ci.yml`'s job env sets no Anthropic key either |
| 4. `pnpm evals` documented, wired into CI after `test`, `--if-present`, baseline checked in | Yes | `package.json` script; `ci.yml` line right after the `test` step; README's new "AI evals" section; `evals/baseline.json` (251 lines) matches the printer's shape |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` against d3bbc80: `evals/**`, `package.json`'s `scripts.evals` line, `ci.yml`'s new step). `src/ai/**`/`src/modules/ai/**` untouched — the assistant eval only *imports* `assistantTools`/`systemContext`, read-only as the card requires.
- [x] Nothing outside scope — every changed line serves AC1–AC4.
- [x] Tests exercise the behavior, and none were weakened — `scan-test-weakening.sh` hits are all outside this card's files (see evidence table); the mock-mode `note` branch in `trademark_judge/run.ts` is the harness's documented plumbing/quality split, not a loosened assertion.
- [x] Tenancy (`withTenant`, RLS), idempotency, money in cents, en/es — every DB read/write in the harness goes through `withTenant`/`withSystem` (via reused fixtures and `gateway-run.ts`'s `jobCost`); no new tables; `costCents` read as integer cents from `ai_jobs`; idempotency N/A (no webhook/job/side effect here, read-only eval calls); en/es N/A (developer console output, not product UI).
- [x] Decisions recorded where needed — none new required; correctly cites decision 0007.

## Optional notes (not blocking)
1. **Throwaway tenant is never deleted.** `evals/lib/fixtures.ts`'s `createEvalTenant()` / `evals/run.ts` have no delete path. Confirmed live: 13 `Eval harness *` companies sitting in the local dev Postgres before I even ran it, +2 more from my own two runs (which I deleted). Harmless — RLS-isolated, and CI's Postgres service is destroyed at job end — but a local dev DB will accumulate these forever. The report already discloses this as a known gap. Worth a quick follow-up (e.g. delete-in-`finally`, or a `--keep-tenant` opt-out) rather than leaving it open-ended.
2. `README.md` isn't named in the card's "Owned files" line, though AC4 requires the doc and `operating-system.md`'s carve-out (README "edited by that repo's owner", docs-writer reviews) covers it. Flagging so docs-writer knows to look, not blocking.
3. `tsconfig.json`'s `include` and `biome.json`'s `files.includes` are both scoped to `src` only, so `pnpm typecheck`/`pnpm lint` silently skip `evals/**` — verified directly by reading both configs. The author correctly left these alone (not owned) and flagged it; a fast follow-up for whichever role owns those files would close the gap.
4. The NUL-byte crash the author found in `gateway.ts`'s `startJob` is already fixed on top of this commit (`e0937cd`, T-8-2 r1) — confirmed by `git log`; not re-verified further here per this review's scope.
