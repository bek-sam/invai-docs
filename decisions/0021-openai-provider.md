# 0021: OpenAI is a second real AI provider, used only when there is no Anthropic key

- Status: proposed (2026-10-01), architect to accept
- Type: architecture
- Supersedes: none. Narrows 0007 (Claude stays the default and the eval baseline).

## Context
The owner has no Anthropic key yet and asked to run the AI features on OpenAI meanwhile (request
2026-10-01). The gateway already isolates providers behind `AiProvider` (`invai-backend/src/ai/providers/types.ts`);
the mock is chosen when no key is set. OpenAI's Responses API offers what the gateway needs: strict JSON
schema output, function calling, streamed text, reasoning effort per request, token usage with cached
tokens, `store: false`. Ids and prices checked on developers.openai.com/api/docs/models and /pricing
on 2026-10-01. Card `waves/P8/T-P8-ai-openai.md`; author ai-engineer; reviewers reviewer and security-reviewer.

## Decision
- **Selection order** (`gateway.ts` `aiProvider()`): `ANTHROPIC_API_KEY` set → Anthropic; else
  `OPENAI_API_KEY` set → OpenAI; else the mock. A sample workspace always gets the mock.
  `env.mocks.ai` is true only when neither key is set. Production boots with either key.
  Under `NODE_ENV=test` both keys are ignored, so no test run reaches a paid model.
- **Models** (`models.ts` `OPENAI_ROUTES`): `gpt-6.1-sol` for listing copy (effort medium), trademark
  judge (low), assistant (high) and digest narrative (low); `gpt-6-luna` with reasoning `none` for the bulk
  `market_niche` route. Same `max_output_tokens` as the Claude routes. Prices in `MODEL_PRICES`
  (Sol $2 / $0.10 cached / $10 per MTok; Luna $0.10 / $0.01 / $0.50).
- **Same controls on both providers:** the gateway scrubs PII, isolates untrusted text in data blocks
  and tool results, meters `ai_jobs` and credits, and applies the spend caps per round (T-P7-5). The OpenAI
  provider sends `store: false`, checks the response status (refusal, content filter, cut-off, failed) before
  reading output, and parses every answer with the prompt's Zod schema. Stop reasons are mapped onto the
  existing vocabulary (`end_turn`, `tool_use`, `max_tokens`, `refusal`).
- **Quality is unproven.** The prompts were written and tuned on Claude. Before a real shop uses OpenAI,
  the owner runs `pnpm evals` in openai mode and the ai-engineer compares it with the Claude baseline
  (model-upgrade gates: no drop on trademark recall, evasions or injection; overall within 2 points).

## Consequences
- The platform works with real AI on an OpenAI key alone; adding an Anthropic key later switches every
  route back to Claude with no code change.
- OpenAI becomes a sub-processor of scrubbed shop text (not buyer PII): compliance-officer confirms the
  draft row in `legal/subprocessors.md` and OpenAI's data terms; security-reviewer co-reviews.
- No server-side refusal fallback on OpenAI (Anthropic-only feature); a refusal surfaces as `UPSTREAM_FAILED`.
- Not covered yet: the Batch API for OpenAI, an SST secret for `OPENAI_API_KEY` (platform-sre), and cache-write
  tokens are priced at the input rate (1.25x on OpenAI, a small undercount, same as the Claude provider).
- Enforced by `src/ai/openai-provider.test.ts` (stubbed HTTP: selection, PII scrub in the request body, strict
  schema, refusal, cut-off, tool loop, spend cap between rounds, run twice) and `src/env.test.ts`.
