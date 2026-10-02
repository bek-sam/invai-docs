# T-P8-ai-openai: OpenAI as a second real AI provider (Anthropic first, then OpenAI, then the mock)

| Field | Value |
|---|---|
| Wave | P8 (side card; the P8 tech lead owns the other cards in this folder) |
| Scope ref | `product/scope.md` items 10 and 13 (AI listing drafts, AI assistant). No new feature: a second backend for the same routes. Owner request 2026-10-01 (no Anthropic key yet, use OpenAI). |
| Owner | ai-engineer |
| Reviewer | reviewer (primary); security-reviewer co-review (new external sub-processor; scrubbed shop text reaches a new provider) |
| Risk flags | ai, pii (new sub-processor), dependency (`openai` npm package) |
| Model | opus |

## Read first
- `.claude/agents/ai-engineer.md`; decision `0007-ai-model-policy.md`; `src/ai/gateway.ts`, `src/ai/providers/{types,anthropic,mock}.ts`, `src/ai/models.ts`, `src/ai/assistant-rounds.test.ts` (T-P7-5 round events).
- Installed SDK: `invai-backend/node_modules/openai` (7.25.0): `resources/responses/responses.d.ts`, `helpers/zod.d.ts`.
- OpenAI model ids and prices, checked 2026-10-01: developers.openai.com/api/docs/models and /api/docs/pricing.

## Owned paths (edit)
- `invai-backend/src/ai/**`, `invai-backend/evals/**`
- `invai-backend/src/env.ts` (only `OPENAI_API_KEY`, `mocks.ai`, the production AI-key rule), `invai-backend/src/env.test.ts` (new cases only). backend-foundation's file: granted by this card, change kept to those lines.
- `invai-backend/src/db/schema/ai.ts` (`ai_jobs.provider` gains `openai`; `enumText` is plain text, no migration)
- `invai-backend/package.json`, `invai-backend/pnpm-lock.yaml` (adds `openai` only)
- `invai-backend/.env.example` (one `OPENAI_API_KEY=` line and a comment)
- `invai-docs/decisions/0021-openai-provider.md` + its index row; `invai-docs/build/runbook.md` (AI env vars); `invai-docs/ops/cost-estimate-aws.md` (OpenAI price rows); `invai-docs/legal/subprocessors.md` and `legal/es/subprocessors.md` (one OpenAI row marked DRAFT for compliance-officer to confirm). Runbook, cost doc and legal rows are additive lines the owner asked for; their owners (docs-writer, platform-sre, compliance-officer) are told in the report

## Read-only
- Every other path; `invai-infra/**` (an SST secret for `OPENAI_API_KEY` is a platform-sre follow-up), `invai-contracts/**`, `invai-web/**`.

## Acceptance criteria
1. Given only `OPENAI_API_KEY` is set, when any AI route runs for a normal shop, then `src/ai/providers/openai.ts` answers it through the Responses API, and `ai_jobs.provider = openai`, `model` = the OpenAI model, cost priced from `MODEL_PRICES`.
2. Given both keys, Anthropic answers. Given neither, the mock answers and `env.mocks.ai` is true. A sample workspace always gets the mock.
3. Production boots with either AI key; with neither, it refuses (unless `ALLOW_MOCKS=true`), as today.
4. Structured output: the prompt's Zod schema is sent as a strict JSON schema and the result is parsed with Zod; a refusal raises `AiRefusalError`, a cut-off raises `AiOutputError`; both map to `UPSTREAM_FAILED`.
5. Assistant: tool calls run the same read-only, tenant-scoped tools, at most `ASSISTANT_MAX_ITERATIONS` rounds, text streamed, a `round` event after every model round so the T-P7-5 spend caps stop a run before the next request.
6. Same safety: PII is scrubbed by the gateway before the request body is built (test inspects the HTTP body), untrusted text stays inside the data blocks, `store: false` on every request.
7. `pnpm evals` prints `mode: openai` with only `OPENAI_API_KEY`; `pnpm evals assistant` stays 42/42 in mock mode.
8. Docs: ADR 0021, runbook env vars, cost doc rows, sub-processor DRAFT row.

## Verification
- `pnpm vitest run --reporter=dot src/ai src/env.test.ts src/modules/ai/service.test.ts`, then once `pnpm typecheck && pnpm lint && pnpm test` (timeout 600000) in `invai-backend`, each piped to `tail -n 40`.
- `pnpm evals assistant` (mock), and a dry `pnpm evals` start with a fake `OPENAI_API_KEY` against an unreachable base URL to see the mode line (no real call, no key printed).
- Tests stub the HTTP layer (a `fetch` handed to the real SDK client): structured happy path, refusal, max tokens, a two-round tool loop, a spend cap stopping round 2, run twice.

## Out of scope
- Real-model eval runs (no key yet: the owner runs `pnpm evals` once the key is in `.env`), SST secret wiring, any prompt text change, Batch API for OpenAI, web changes.

## Report
- Final message to the caller (verify-and-report, at most 60 lines). Commit own paths only; no push.
