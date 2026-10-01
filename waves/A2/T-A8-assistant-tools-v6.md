# T-A8: Assistant tools v6 and prompt v6 ("why" with evidence), evals (B-175)

| Field | Value |
|---|---|
| Wave | A2 |
| Scope ref | `product/scope.md#mvp-in` item 13 (read-only assistant tools) |
| Spec | `specs/business-analytics-v2.md` Track E "Assistant tools"; AC-A5, AC-E3, AC-E4, AC-G1 (assistant leg) |
| Owner | ai-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (tenancy, prompt injection; sonnet) |
| Risk flags | ai, tenancy |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/modules/ai/**` (`assistant-tools.ts`, `analyst-queries.ts`, tests)
- `invai-backend/src/ai/**` (prompts, validators, model config)
- `invai-backend/evals/assistant/**`, `invai-backend/evals/baseline.json` (assistant rows only)

## Read-only paths
- `invai-backend/src/modules/analytics/**` (call `unitEconomics`, `profitBridge`, `operations`, `inventoryHealth`, `shippingMargin` services; don't change them), `invai-contracts/**` (the five tool names are already reserved in 0.9.0), `src/db/**`, `src/lib/**`

## Depends on
- Nothing in this wave. Runs in parallel with T-A10 and T-A6.

## Acceptance criteria
1. Five read-only tools: `get_unit_economics`, `explain_profit_change`, `get_operations_health`, `get_inventory_health`, `get_shipping_insights`. Each returns `{ data, summary, answer }`, at most 20 rows, runs inside `withTenant`, and holds no buyer name, email, address or personalization text.
2. Prompt v6: for a "why did profit change" question the model calls `explain_profit_change` first; every recommendation states its evidence numbers and the metric name. Prompt version bumped; older prompt kept per the existing versioning pattern.
3. AC-A5: on two weeks with different sales, the stated volume and per-unit parts add up to the stated change, and the top design named equals `analytics.profitBridge`'s first mover (eval case plus a unit test on the tool output).
4. AC-E3: a Spanish question gets a Spanish reply and Spanish labels (eval case).
5. AC-E4: a tool called for company A returns no company B row (test per tool).
6. AC-G1 assistant leg: `get_unit_economics` net for the last completed week (no channel, dimension order) equals `analytics.unitEconomics` to the cent; with `channel: "shopify"` the two are equal too.
7. Evals: at least 2 cases per tool (the spec review flagged thin coverage on 3 of 5), run on the mock provider; baseline updated only for the new cases; no existing case's threshold lowered.
8. Tool output is treated as data, not instructions (an injection string in a design name doesn't change the model's behavior; one eval or unit case).

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint && pnpm test src/modules/ai src/ai 2>&1 | tail -n 40`
- `pnpm eval assistant` (or the repo's eval command) on the mock provider; report pass counts vs baseline.
- Live: `PORT=3162 REDIS_URL=redis://localhost:6379/<own db> pnpm dev:api`; as `owner@desertbloom.test` ask the assistant "why did profit change this week?" and "¿por qué cambió la ganancia esta semana?"; show the tool calls and that the numbers match `analytics.profitBridge`. As `designer@` the finance tools are refused.

## Out of scope
- Any write tool. Model or effort changes (decision 0007 needs evals first). Web assistant UI changes. Track D.

## Budget
- About 3 hours. Escalate if blocked for more than about 30 minutes.
