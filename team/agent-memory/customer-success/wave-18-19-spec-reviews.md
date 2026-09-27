---
name: wave-18-19-spec-reviews
description: Customer-success co-review outcomes for market-signals (wave 18) and weekly-digest (wave 19) specs, 2026-09-27
metadata:
  type: project
---

Reviewed and filed both as **approve-with-changes** on 2026-09-27:
- `invai-docs/waves/18/reviews/spec-market-signals-customer-success.md`
- `invai-docs/waves/19/reviews/spec-weekly-digest-customer-success.md`

Core blocking finding in both: outside-market signals in this build are mock-only (Google Trends, Pinterest, Amazon, Walmart, Jungle Scout all pending OI-9/OI-10/OI-11 and marketplace approvals), yet R2/R4 recommendations built on that mock data can reach a real pilot shop with only a small "Sample data" badge as disclosure. Recommended: either suppress those rules from firing on mock-only sources for real shops until a real provider connects, or move the disclosure into the action sentence itself (not just a badge). This risk is worse in weekly-digest's Market watch block because it's an unattended push (email/in-app card) rather than something the owner explicitly asked the assistant.

**Why:** both specs were owner-approved (OI-6, OI-7 on 2026-09-27) despite 0 pilot shops having asked — my job was checking whether a real shop would get a wrong/misleading answer, not re-litigating the owner's go-ahead.

**How to apply:** next spec review touching AI/market/assistant output, check whether any actionable claim can be sourced entirely from a mock/simulated provider and reach a real (non-sample) shop with only a badge as disclosure — that pattern is a recurring blocking-severity risk, not a one-off. See [[spec-review-lens]].
