# Review of T-P4-4 (round 1)

- Reviewer: reviewer on claude-opus-5-5
- Author: ai-engineer on claude-opus-5 (report header)
- Verdict: approve

## Evidence I re-ran
Run in an isolated worktree of `461c8fd` at `/tmp/rv-p4-4`, with node_modules symlinked and none of T-P4-1's uncommitted edits. The worktree has since been removed.
| Command | Result |
|---|---|
| `vitest run src/modules/ai --reporter=dot` | 8 files, 103 passed |
| Restore `eq(profitLines.isReprint,false)` in both files (worktree only), run the 2 test files | 2 failed / 41 passed: analyst `expected undefined to be defined`, topDesigns `expected 1 to be 2`. Only the two new tests fail. |
| `tsc --noEmit` | exit 0, no output |
| `biome check .` | 455 files, no fixes |
| `scan-test-weakening.sh /tmp/rv-p4-4 461c8fd^` | removed=0 added=5. The only hits are 2 new `toBeDefined()` lines, each followed by an exact-value assertion. Not blocking. |
| `grep isReprint ai/analyst-queries.ts ai/assistant-tools.ts` | no matches left |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | The diff removes exactly the two filters (`analyst-queries.ts:385`, `assistant-tools.ts:601`). `eq(refundsCents,0)` stays in the analyst query. topDesigns never had a refund filter, so nothing changed there. |
| 2 | Yes, with a note | A 2-unit order with 1 reprint gives `units === 2` from topDesigns, and `soldOn units:3` in cross-listing gaps. Both tests fail on the base filter (re-run above). Neither query selects revenue (both are unit counts), so "revenue in answer data" can't be tested at these two sites, as the report says. |
| 3 | Yes | The diff is 4 files under `src/modules/ai`. Tool descriptions, prompts, models and credits are unchanged, and the mock provider path is untouched. |

## Blocking findings
none

## Checks
- [x] Only owned paths changed: `ai/analyst-queries{,.test}.ts`, `ai/assistant-tools{,.test}.ts`
- [x] Nothing outside scope. The `export topDesigns` and the new `units` field are in an owned file, and no contract or type is affected. The function has 4 internal callers (`:878`, `:889`, `:1230`, `:1233`). They read only `id`, `name` and `channel`. The objects from `:889` reach tool output only as `{id, name}` (`:908`, `:993`), so `units` never reaches model-facing data.
- [x] Tests exercise the behavior and none were weakened. In the analyst test, the 3rd unit gets past the `having count(*) >= 3` gate. The test still has meaning: with the filter the count is 2, the design drops out and the test goes red; without it the test pins the exact count of 3. The red is a missing row rather than a wrong number, but it is still red.
- [x] Tenancy: `topDesigns` filters on `companyId` and the test runs under `withTenant`. No new tables, no idempotency surface, no money arithmetic, no user-facing strings.
- [x] Decisions: this implements 0020. Nothing new to record.

## Optional notes (not blocking)
- The test comments say the reprint sits "on the same order_items row". In fact, `finance-testkit.addOrder` sets `isReprint` only on `profit_lines`, each on its own item, and leaves `order_items.is_reprint` false. That is harmless, because both queries read only `profit_lines`.
- The new tests import `analytics/finance-testkit.ts`, which T-P4-1 is rewriting (uncommitted). At the commit, the tests use only `addDesign` and `addOrder({lines:[{designId,isReprint,revenue}]})`. The gate should re-run `src/modules/ai` after T-P4-1 lands, in case that signature changes.
