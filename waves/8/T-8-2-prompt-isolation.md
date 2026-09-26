# T-8-2: Prompt isolation and global AI spend breaker (B-15)

Owned files (wave.md "File ownership and batches", batch 1, parallel with T-8-3 and T-8-5): `src/ai/gateway.ts`, `src/ai/breaker.ts` (new), `src/ai/prompts/index.ts`, `src/modules/ai/assistant-tools.ts`, its own `describe` block in `src/ai/ai.test.ts`.

## Acceptance criteria
1. **Delimited data blocks:** every piece of untrusted text (buyer personalization, product titles, CSV fields, shop notes, the assistant's tool results) goes to Claude inside delimited data blocks, with an explicit "treat as data" instruction.
2. **Injection test set:** a test set of injection attempts ("ignore previous instructions", fake tool calls) that must not change the output schema or trigger tools.
3. **Spend breaker:** a global AI spend breaker with a daily platform cap and a per-tenant cap (config). Design exactly per wave.md "Contract stubs / B": Valkey keys, the `AI_SPEND_CAP_REACHED` error code with `data.scope`, and the `ai_spend_cap_tenant`/`ai_spend_cap_platform` alerts. Checked before each call, cheap (a Valkey `GET`). Demo workspaces already use the mock (T-6-5 / T-6-4) and never touch the counters.
4. **Tests:** a unit test for every route that the blocks are applied, and breaker tests for both scopes (cap not hit, tenant cap hit, platform cap hit, alert emitted once per day).
