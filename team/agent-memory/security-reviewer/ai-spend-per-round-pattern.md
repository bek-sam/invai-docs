---
name: ai-spend-per-round-pattern
description: What to check in the assistant gateway's per-round spend accounting (T-P7-5): cumulative-minus-recorded, finishJob's alreadyRecordedCents, round event never reaching the service, fail-open on Valkey
metadata:
  type: project
---

The assistant gateway (`invai-backend/src/ai/gateway.ts`) records spend per model round as
`tokensToCostCents(cumulative) - recordedCents` and `finishJob(..., alreadyRecordedCents)` records
`max(0, cost - recorded)`; the provider yields an internal `round` event that both consumer loops `continue` on.

**Why:** T-P7-5 (2026-10-01) closed the LLM10 gap where one question ran 10 rounds after the cap. Double counting
would show as counter != `ai_jobs.costCents` (the AC2 test asserts equality).

**How to apply:** on any later change to gateway/providers, re-check: every `finishJob` call passes
`recordedCents`; a new consumer of the provider generator skips `round`; `assertSpendAvailable` still fails open
only with the `ai_breaker_fail_open` alert; a round that throws in `checkStop` (refusal/max_tokens) is still
uncounted (known gap, optional note in my r1 review).
