# Report: T-A8 Assistant tools v6 and prompt v6 ("why" with evidence), evals
Author: ai-engineer on opus. Commit: invai-backend `9f49291` (not pushed).

## Built
- 5 read-only tools in new `src/modules/ai/analytics-tools.ts`, spread into `assistantTools()`; each calls the analytics service (`unitEconomics`, `profitBridge`, `getOperations`, `inventoryHealth`, `shippingMargin`) inside its own `withTenant`, returns `{data, summary, answer}`, caps lists at 20 (`V6_MAX_ROWS`), names its metric (`contribution_margin`, `profit_bridge`, ...), en/es answers and labels via `lang`. Registered only when the caller has `finance.read` (same permission as `analytics.*`).
- Prompt `assistant` v5 → v6 (`src/ai/prompts/index.ts`): profit "why" calls `explain_profit_change` first, states total/volume/per-unit and the top mover as ranked; Evidence names the metric; `lang` for every tool; `*Pct` are percents. Older versions stay in git history (same pattern every prompt uses; v5 was also an in-place bump).
- Mock (`src/ai/providers/mock.ts`): routes the 5 tools by keyword (profit "why" → explain first instead of compare_periods; sales "why" unchanged), Spanish period words for v6 tools, Spanish demo footer for Spanish questions.
- Evals: 12 new cases as-031..042 (explain 4, others 2 each; Spanish, injection); `evals/assistant/run.ts` runs tools with owner permissions; baseline assistant row updated.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 five tools, shape, ≤20 rows, withTenant, no PII | yes | `analytics-tools.test.ts` "AC1" (walks data, buyer note seeded, 40 orders → 20 rows) |
| 2 prompt v6, explain first, metric in evidence | yes | `service.test.ts` prompt v6 test; mock + live call order |
| 3 AC-A5 parts add up, top design = profitBridge | yes | unit test parses answer vs `profitBridge`; live below |
| 4 AC-E3 Spanish | yes | unit test + eval as-033/as-039 + live below |
| 5 AC-E4 per tool | yes | test "AC-E4" (9 tool/input pairs, A↔B both ways) |
| 6 AC-G1 all channels and shopify | yes | test via `router.analytics.unitEconomics` on `lastCompleteWeek`; live 153390 = $1,533.90 |
| 7 evals ≥2/tool, mock, no threshold lowered | yes | 42/42 plumbing, 28/28 quality (was 30/30, 17/17; old tags unchanged) |
| 8 tool output is data | yes | test "AC8" (hostile design name kept as label, no extra tool call); eval as-042 (real-model gated) |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| backend | `pnpm typecheck` / `pnpm lint` | clean / 442 files, no fixes |
| backend | `vitest run src/modules/ai src/ai src/api/authz.test.ts` (own DB `invai_ta8_test`, Redis 12) | 15 files, 187 passed |
| backend | `tsx evals/run.ts assistant` (NODE_ENV=test, own DB, mock) | 42/42 plumbing, 28/28 quality, median 10 ms |
| backend | full `typecheck && lint && test` (own DB, Redis 12, pipefail) | exit 0; 166 files passed, 2 skipped; 1307 tests passed, 3 skipped, 1 todo |

## Exercised for real (API :3162, shared dev DB, mock AI)
- owner "Why did profit change this week?" → tool_call `explain_profit_change` (Sep 28–30 vs Sep 21–23): +$188.20 = volume +$65.76 + per unit +$122.44; top "Sun's Out Buns Out". `rpc analytics.profitBridge` same periods: 18820 / 6576 / 12244, first mover same.
- "¿Por qué cambió la ganancia esta semana?" → same tool with `lang:"es"`, Spanish text, labels and footer.
- "unit economics last week" → CM3 $1,533.90; `analytics.unitEconomics` cm3 153390.
- Refused: designer → `ai.assistant.ask` FORBIDDEN, `analytics.unitEconomics` FORBIDDEN (finance.read).

## Decisions
- New file instead of growing the 1,239-line `assistant-tools.ts`; it reuses that file's range guard wrapper (S-33).
- No real-model eval run: no `ANTHROPIC_API_KEY`. Model and effort unchanged, so cost per call is unchanged apart from about 5 new tool definitions in the cached prefix. The real-model diff for prompt v6 (as-042, refusals, injection set) still needs an owner run, as for earlier prompt versions.

## Known gaps and follow-ups
- Real-model eval of prompt v6 is pending a key (owner). `evals/**` isn't typechecked or linted; running it is the check.
- Web: tool names already sit in contract 0.9.0; the answer is Markdown text, nothing new to render.

## Blocked by other owners
- none

## Processes and data
- Stopped: API PIDs 40312 (tsx) and 40322 (node) on :3162. Dropped `invai_ta8_test`, flushed Redis DB 12. Shared dev DB: read only (3 assistant conversations added by the live asks).
