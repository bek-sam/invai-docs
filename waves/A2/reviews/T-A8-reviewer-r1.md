# Review of T-A8 (round 1)

- Reviewer: reviewer on opus. Author: ai-engineer on opus. Commit: invai-backend `9f49291` (only commit ahead of origin/main, tree clean)
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` | exit 0 / 442 files, no fixes |
| `vitest run src/modules/ai src/ai src/modules/analytics src/db/rls-coverage.test.ts src/api/authz.test.ts` (own DB `invai_ta8_rev`, Redis 13) | 22 files, 266 passed |
| `NODE_ENV=test tsx evals/run.ts assistant` (mock) | 42/42 plumbing, 28/28 quality; per-tag counts equal the new baseline; baseline file not rewritten |
| `scan-test-weakening.sh invai-backend 9f49291~1` | 1 removed assertion: `version).toBe(5)` replaced by `toBe(6)` + 3 new prompt asserts; no skip/only/snapshot/config hits |
| Live API :3171 (PID 41826, stopped), owner: "Why did profit change this week?" | 1 call `explain_profit_change` (Sep 28–30 vs Sep 21–23): +$188.20 = +$65.76 + $122.44, top "Sun's Out Buns Out" -$59.29; `rpc analytics.profitBridge` same periods: 18820/6576/12244, same first mover |
| owner: "¿Por qué cambió la ganancia esta semana?" | same tool with `lang:"es"`; Spanish labels, dates and footer, same numbers |
| owner: unit economics last week, all and Shopify | CM3 $1,533.90 / $557.87; `analytics.unitEconomics` cm3 153390 / 55787 |
| designer | `ai.assistant.ask` FORBIDDEN; `analytics.profitBridge` FORBIDDEN (finance.read) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 five tools, shape, ≤20 rows, withTenant, no PII | yes | `analytics-tools.ts`: each run opens `withTenant(ctx.companyId)`; `cap()` ≤20; test AC1 walks data keys (no buyer/address/note keys), seeded buyer note absent, 40 orders → 20 rows. Order rows carry only order numbers (#1454) |
| 2 prompt v6, explain first, metric in evidence | yes | prompt diff + service.test v6 asserts; live call order. v5 kept in git history, same pattern as v4→v5 (54640f2) |
| 3 AC-A5 | yes | test parses answer vs `profitBridge` (total, volume, per unit, first mover); live match above |
| 4 AC-E3 Spanish | yes | test + as-033/as-039 + live Spanish answer |
| 5 AC-E4 per tool | yes | test: 9 tool/input pairs, A↔B both ways, plus B-only totals (77,777; 40 on hand; 1 reprint) |
| 6 AC-G1 | yes | test via `router.analytics.unitEconomics` on `lastCompleteWeek`, all + shopify; live match |
| 7 evals ≥2/tool, mock, no threshold lowered | yes | 12 new cases (explain 4, others 2); old tag counts only grew; no threshold field changed |
| 8 tool output is data | yes (see note 1) | hostile design name returned verbatim as a label; prompt carries DATA_RULE covering every tool result; as-042 on the seeded HOSTILE_DESIGN tenant with `allowedTools` |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`src/modules/ai/**`, `src/ai/**`, `evals/assistant/**`, `evals/baseline.json`)
- [x] Nothing outside scope (no write tool, no model/effort change, no contract/UI change)
- [x] Tests exercise the behavior, none weakened (new test file cannot pass on base: module absent)
- [x] Tenancy: `withTenant` per tool, no new `withSystem` in production code, no new table; money in cents; en/es strings; range guard (S-33) wraps the new tools
- [x] Decisions: none needed (new file choice is card-local)

## Optional notes (not blocking)
1. The AC8 unit case can't fail in mock mode: the mock plans calls from the message only, never from tool output. The real proof is as-042 on a real model, pending the owner's key run (report says so).
2. `evals/baseline.json` also re-encodes the `personalization_check` `skippedReason` (`—` → `—`): same JSON value, but strictly outside "assistant rows only".
3. Mock: a profit "why" no longer adds `compare_periods`, so a caller without `finance.read` would get the "no data" text. Unreachable today: every role with `ai.assistant.ask` (owner, admin, office) has `finance.read`.
4. Cleanup: Redis DB 13 flushed (0 clients), `invai_ta8_rev` dropped. Shared dev DB: 5 assistant conversations added by the live asks, nothing else.
