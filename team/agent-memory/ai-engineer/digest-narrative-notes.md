---
name: digest-narrative-notes
description: Wave 19 facts for the digest_narrative route - placeholder-only validator word lists, where outcomes live for the breaker, test and eval gotchas
metadata:
  type: project
---

- 2026-09-27 T-19-2: the digest summary validator (`src/ai/validators/digest.ts`) checks the model's own words with placeholders removed; lengths on substituted text. Word lists (numbers, direction, promise, market) are strict on purpose: in shadow a false reject only costs a template. Retune them from the real-model eval (OI-8), not by guess.
  **Why:** a design name like "...profit doubled" must only ever appear as a substituted value.
  **How to apply:** a test fixture's "good" text must avoid direction words too ("rising" in a market item fails); the language check needs enough function words per side or it ties and passes.
- 2026-09-27 T-19-2: breaker outcomes live on `ai_jobs.output.validation` (kind `digest_narrative`, failed jobs count as rejected), read cross-tenant with `withSystem`; the trip flag is Valkey `ai:digest_summary:breaker` with no TTL (a person clears it). `digestSummaryMode()` is async and fails closed to shadow.
- 2026-09-27 T-19-2: digest tests delete every `digest_narrative` ai_jobs row in `beforeEach` (global breaker window) — don't run a digest script against the same test DB while they run. See [[eval-harness-notes]], [[fallback-must-pass-own-check]].
