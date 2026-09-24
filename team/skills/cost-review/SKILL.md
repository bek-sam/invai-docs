---
name: cost-review
description: Monthly InvAI cost review. Cloud spend by service, AI tokens and cents per tenant and per route (with prompt-cache hit rate), label fees versus postage and carrier charges, and usage versus plan limits, turned into cost per shop against revenue per plan. Use monthly, before a pricing change, when AI or AWS spend jumps, or when someone asks "what does a shop cost us".
---

# Cost review

Every month we know what each shop costs to run (cloud, AI, labels) against what its plan earns, and any
runaway cost has an owner and a fix before it becomes a bill.

## When to use
- Monthly (research 11 §7.3, tech-lead checklist §9), by platform-sre with the data-analyst and ai-engineer.
- AI spend, an AWS bill or a single shop's usage jumps.
- Before a pricing or plan-limit change (input to `unit-economics-model` and `pricing-experiment`).

## Steps
1. **Open the record** `invai-docs/ops/cost-reviews/<YYYY-MM>.md` (folder to be created, platform-sre).
   Sections: cloud, AI, labels, usage vs plan, cost per shop, actions.
2. **Per-tenant drivers from the database.** Locally, or in AWS only with the owner's go-ahead:
   ```
   docker exec -i local-postgres-1 psql -U invai -d invai -v ON_ERROR_STOP=1 \
     -v period='<YYYY-MM>' -v since='<YYYY-MM-01>' -v until='<next month -01>' \
     < .claude/skills/cost-review/queries.sql
   ```
   It prints: usage vs plan (`usage` + `plans`), AI spend per shop and per route and model (`ai_jobs`), labels
   per shop (`labels`, cross-checked with `shipments`), stored bytes per shop (`files`), and background job
   time (`jobs`). On the mock provider AI `cost_cents` is 0 and model names start with `mock-`: say so instead
   of reporting "free".
3. **AI.**
   - Top 5 shops and routes by `ai_cents`. Compare credits used with `plans.ai_credits_per_month`.
   - Cache hit rate per route = `cache_read / (tokens_in + cache_read)` (the gateway stores cache reads
     separately from `tokensIn`, `src/ai/providers/anthropic.ts`). Below 50% on a route with a stable prefix
     is a finding for the ai-engineer (research 11 §8).
   - Bulk work that could use the Message Batches API (50% cheaper): overnight listing drafts, trademark
     re-checks.
   - Guards: per-tenant credits exist (`src/ai/credits.ts`); the global daily spend breaker doesn't yet
     (research 11 G18, backlog B-15). Anthropic workspace spend limits and separate staging/production
     workspaces are owner settings (research 12 §1.9).
   - Model or effort changes go through evals first (`decisions/0007-ai-model-policy.md`, `model-upgrade`).
4. **Labels.** InvAI earns `plans.label_fee_cents` per label (trial 0, starter 5, growth 4, pro 3, scale 2
   cents on 2026-09-24). Postage (`postage_cents`) is passed through. Compare fee revenue with what the
   carrier API charges InvAI per label: EasyPost is mocked today, so take its current pricing from EasyPost at
   review time and cite the page and date. Voided labels and refunds count against the fee.
5. **Cloud.** Nothing is deployed yet, so today this section lists the planned fixed costs from
   `invai-infra/sst.config.ts` (NAT EC2 instance, RDS Postgres, Valkey, ECS api (min 2 in production), worker,
   imaging at 2 vCPU / 8 GB, ALB, CloudFront for web and floor, KMS key, S3) with prices looked up at review
   time and cited. Once deployed, the owner pulls AWS Cost Explorer or the Cost and Usage Report grouped by
   service and `stage` tag. Split cost allocation data for ECS and tags per service are to be set up (research
   11 §7.3).
6. **Cost per shop.** Allocate shared cloud cost by driver (research 11 §7.3): DB by share of orders and jobs,
   compute by job seconds plus requests, S3 by bytes, and add each shop's own AI cents and carrier label
   charges. Put it next to plan revenue (`plans.price_monthly_cents` + label fee revenue). Flag any shop whose
   cost exceeds what its plan earns, and the top 5% of shops by cost.
7. **Findings and actions.** Each finding gets an owner role and a card: a cache-miss fix (ai-engineer), a
   noisy tenant (backend-foundation: quotas and fairness, B-20), a missing driver like render seconds or
   `tenant_usage_daily` (research 11 G19). Pricing or plan-limit changes are the owner's: `escalate-to-owner`
   with the numbers, via the PM (`pricing-experiment`).
8. **Share.** Summarize in plain language for the owner: total cost, cost per shop by plan, the biggest
   driver, and decisions needed. The data-analyst uses the record in `unit-economics-model`.

## Rules
- MUST cite a source and date for every price (AWS, Anthropic, EasyPost). Never estimate a price from memory.
- MUST NOT change prices, plan limits, spend limits or cloud resources as part of the review. Recommend; the
  owner decides.
- MUST NOT put buyer PII in the record; shop names are fine inside the team, ids in anything shared further.
- MUST NOT use `company_id` as a CloudWatch metric label for per-tenant cost; use logs, the database and the
  CUR (research 11 §5.2).

## Done when
- `invai-docs/ops/cost-reviews/<YYYY-MM>.md` has cloud, AI (per shop and route, cache hit rate), labels (fee
  revenue vs carrier charge), usage vs plan and cost per shop vs revenue, with the query output and cited
  prices.
- Every flagged shop or route has an action with an owner role and a card, or an owner-inbox entry for
  pricing.
- The owner has the plain-language summary.

## References
- `queries.sql` (this folder)
- `invai-docs/research/11-platform-scale-playbook.md` §7.3 (cost per tenant), §8 (LLM cost controls), G18, G19
- `invai-docs/research/12-security-quality-playbook.md` §1.9 (LLM10 unbounded consumption)
- `invai-backend/src/ai/credits.ts`, `src/ai/gateway.ts`, `src/ai/models.ts`; `src/db/schema/billing.ts`
  (`plans`, `usage`), `src/db/schema/shipping.ts` (`labels`, `shipments`)
- Related: `unit-economics-model`, `pricing-experiment`, `model-upgrade`, `define-slo`
