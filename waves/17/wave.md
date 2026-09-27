# Wave 17: the assistant as the shop's business analyst

- Goal: the assistant answers "why", "are my ads worth it", "which designs to push" and "what should I do this week" with evidence and ranked actions, using only the shop's own data.
- Spec: `specs/assistant-business-analyst.md`. Scope: `product/scope.md#mvp-in` item 13 (read-only tools).
- Rules: `team/agent-brief.md`. **Every prompt says "Don't push; only the tech lead pushes after the gate."**
- Runs alongside wave 16 (team harness), which touches only team files.

## Cards
| Card | Owner | Flags | Model |
|---|---|---|---|
| T-17-1 Assistant tool names in the contract | architect | — | sonnet |
| T-17-2 Analyst tools: compare_periods, get_ad_performance, get_design_insights, get_fulfillment_health | ai-engineer | tenancy, ai | opus |
| T-17-3 Assistant loop and prompt v4: tool memory, shop context, language, analyst mode | ai-engineer | ai, pii | opus |
| T-17-4 Assistant screen: new tool chips and starter questions (en/es) | web-engineer | ui | sonnet |

## Order and ownership
1. **T-17-1** first (small). Then **T-17-2**, then **T-17-3** (same agent, one after the other; both touch `src/modules/ai`). **T-17-4** starts after T-17-1 lands.
2. Only T-17-1 changes contracts; T-17-2 and T-17-3 touch backend only.

| Card | Owns (exclusive) |
|---|---|
| T-17-1 | `invai-contracts/src/schemas/ai.ts` (`AssistantEvent.tool_call.name`), `package.json` version, `CHANGELOG.md`, `src/compat.ts` if the version constant lives there |
| T-17-2 | `invai-backend/src/modules/ai/assistant-tools.ts`, new `src/modules/ai/assistant-tools.test.ts`, `src/ai/providers/mock.ts` (routing for new tools), `invai-backend/evals/assistant/**` |
| T-17-3 | `invai-backend/src/ai/prompts/index.ts` (assistant prompt only), `src/ai/providers/anthropic.ts` (assistant fn), `src/ai/providers/types.ts`, `src/ai/gateway.ts` (assistant path), `src/modules/ai/service.ts` (`ask` only), `src/modules/ai/service.test.ts`, `invai-backend/evals/assistant/**` (after T-17-2) |
| T-17-4 | `invai-web/src/routes/_app/assistant.tsx`, `invai-web/src/i18n/en.ts` + `es.ts` (assistant keys only) |

## Interfaces agreed
- New tool names (exact): `compare_periods`, `get_ad_performance`, `get_design_insights`, `get_fulfillment_health`. `get_production_status` joins the contract enum too.
- Tool output shape stays `ToolOutput = {data, summary, answer}`.
- i18n keys: `assistant.tool.<name>` for chips; `assistant.starter.<review|ads|designs|shipping>` for starter questions.

## Reviews
- Every card: `reviewer` (sonnet; opus builders get a sonnet reviewer).
- T-17-2 and T-17-3: `security-reviewer` co-review (tenant isolation of new SQL; prompt injection through tool data; no PII in history lines).
- T-17-4: `product-designer` co-review is waived for this small change by the tech lead (token budget, decision 0011); the reviewer checks en/es and 390 px.

## Grants
- 2026-09-26: T-17-2 gains criteria 12–13 from the PM's plan review (spec AC9, AC10). No new paths.
- 2026-09-26: T-17-2 and T-17-3 may update the assistant entry in `invai-backend/evals/baseline.json` (criterion 10 needs it; the file sits outside `evals/assistant/**`).
