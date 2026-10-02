---
name: openai-provider-facts
description: Non-obvious facts about the OpenAI provider (decision 0021) and OpenAI ids/prices as of 2026-10-01
metadata:
  type: project
---

2026-10-01 T-P8-ai-openai: OpenAI is the fallback provider (Anthropic key wins). Facts the next card needs:
- OpenAI's current family is GPT-6 (gpt-6-astra $10/$50, gpt-6.1-sol $2/$10, gpt-6-luna $0.10/$0.50 per MTok). WebFetch's summarizer mixed in old gpt-5.6 names; curl the raw page and grep model ids instead.
- OpenAI `input_tokens` INCLUDES cached tokens; our TokenUsage.tokensIn excludes them (subtract `cached_tokens`).
- AI keys are ignored under NODE_ENV=test (env.ts), so tests must set `env.OPENAI_API_KEY` + `env.mocks.ai=false` at runtime and spy the provider with `createOpenAiProvider(() => stubClient)`.
- `AiRefusalError.name` is "Error" (no name set): assert with instanceof.
- Evals can be run in openai mode without a key: `OPENAI_BASE_URL=http://127.0.0.1:<port>/v1` to a local stub.

**Why:** owner had no Anthropic key; OpenAI quality is unproven until a real `pnpm evals` run.
**How to apply:** before any OpenAI model change, re-check ids/prices from the raw docs page; compare evals vs the Claude baseline ([[model-upgrade]]).
