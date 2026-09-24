---
name: model-upgrade
description: Change the Claude model, effort level or max_tokens for an InvAI AI route (or move a bulk route to Haiku or Sonnet) by running the route's eval set old vs new, comparing quality, cost per call and latency, and rolling out behind a flag. Use for "new model", "switch to Haiku", "cheaper model", "change effort", "model deprecation", "upgrade Claude".
---

# Model upgrade

A model or effort change ships only when the eval set shows equal or better quality at a known cost and latency, and it can be rolled back with a one-line change.

## When to use
- Anthropic releases a model, deprecates one, or changes pricing.
- A route's cost or latency is too high (`cost-review`, research 11 §8) and a cheaper tier might hold quality.
- Changing `effort`, `maxTokens` or the refusal fallback for a route.
- Owner: ai-engineer. data-analyst co-reviews the cost diff. A prompt text change is `ai-feature-with-evals`.

## Steps
1. **Invoke the `claude-api` skill** for the current model ids, pricing, effort and thinking options, deprecation dates and the refusal-fallback beta. Don't trust memory; decision 0007 fixes `claude-opus-5` as the default.
2. **Read** `src/ai/models.ts`: `DEFAULT_MODEL`, `ROUTES` (per-route `model`, `effort`, `maxTokens`), `REFUSAL_FALLBACK`, `tokensToCredits` and `tokensToCostCents`. **`tokensToCostCents` hard-codes Opus 5 list prices ($5 in / $25 out / $0.50 cache read per million)**; a different model needs per-model prices there or every `ai_jobs.costCents` is wrong.
3. **State the hypothesis** in the card: route, old → new (model, effort, maxTokens), expected cost and latency change, the quality bar (e.g. "trademark recall on known marks and evasions stays 100%").
4. **Run the eval set** for the route (`invai-backend/evals/<route>/`, to be created; format in `ai-feature-with-evals/eval-template.md`) with the old config, then the new, same cases, same prompt version. Needs `ANTHROPIC_API_KEY`; if none is available, escalate for an owner-run (`escalate-to-owner`). Run each case at least twice when outputs vary.
5. **Compare** in one table: pass rate overall and per tag, recall on risk tags, injection pass rate (must stay 100%), validator first-try pass rate, cost per call (median, p95), latency (median, p95), cache hit rate, refusal rate (`stopReason`).
6. **Decide** with these gates:
   - quality: no drop on risk tags (known marks, evasions, injection, PII refusal); overall within 2 points or better;
   - cost: report the monthly effect at current volume (from `ai_jobs` counts per route);
   - latency: interactive routes (assistant, single listing draft) must not get slower at p95.
   A failed gate means no change. Record the result either way.
7. **Change one line per route** in `ROUTES` (and prices in `tokensToCostCents` if the model changes). Keep the mock label `MOCK_MODEL` meaningful. Don't scatter model ids anywhere else (`grep -rn "claude-" src` should only hit `models.ts` and provider code).
8. **Roll out behind a flag**: pilot tenants first, then everyone, using the `feature_flags` / `isEnabled(flag, companyId)` helper (to be created, research 11 §4.3). Until it exists, ship to all at once only for bulk, non-interactive routes, and watch `ai_jobs` failures and cost for 48 hours.
9. **Record** the decision (`record-decision`): a new ADR if the default model or policy changes (supersedes 0007), otherwise a line in the wave file with the eval table.
10. **Watch after release:** failed `ai_jobs` rate, refusal rate, cost per call and cache hit rate per route for one week. Roll back by reverting the `ROUTES` line.

## Rules (MUST / MUST NOT)
- MUST NOT change a model or effort without the old-vs-new eval table in the report (decision 0007).
- MUST use Haiku or Sonnet only for bulk routes (tags, SKU suggestions, personalization checks, batch drafts), only after the eval shows equal quality.
- MUST keep per-route `maxTokens` and the global and per-tenant spend controls (`assertCredits`, the daily breaker from backlog B-15).
- MUST keep the server-side refusal fallback on and `stop_reason` checked.
- MUST NOT send any new data category to the provider as part of an upgrade (owner decision).

## Done when
- The eval table (old vs new) with cost, latency, cache hit and refusal rates is in the report and the wave file.
- `models.ts` changed in one place, with prices updated if the model changed; `pnpm typecheck && pnpm lint && pnpm test` pass.
- Rollout and rollback steps are written; data-analyst reviewed the cost diff.

## References
- `invai-docs/decisions/0007-ai-model-policy.md`
- `invai-backend/src/ai/models.ts`, `src/ai/gateway.ts`, `src/db/schema/ai.ts` (`ai_jobs`)
- `invai-docs/research/11-platform-scale-playbook.md` §8
- Related: `ai-feature-with-evals`, `cost-review`, `record-decision`
