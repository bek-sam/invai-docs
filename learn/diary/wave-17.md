# Wave 17 — the assistant as the shop's business analyst

**Dates:** 2026-09-27.

## What was built
- **T-17-1** Assistant tool names in the contract (architect): the AI assistant's callable
  tools get real, typed names in `@invai/contracts`, not ad-hoc strings.
- **T-17-2** Analyst tools: `compare_periods`, `get_ad_performance`, `get_design_insights`,
  `get_fulfillment_health` (ai-engineer): four new tools the assistant can call to answer
  real business questions, flagged for tenancy and AI risk.
- **T-17-3** Assistant loop and prompt v4: tool memory, shop context, language, analyst
  mode (ai-engineer): the assistant remembers which tools it already called in a
  conversation, knows which shop it's talking to, and answers in the right language.
- **T-17-4** Assistant screen: new tool chips and starter questions, en/es (web-engineer):
  the web UI surface for all of the above.

## Why
Through wave 16 the assistant (built earlier, per module 07) could answer simple
questions. Wave 17 is the shift from "a chatbot that knows some facts" to "a business
analyst that answers 'why', 'are my ads worth it', 'which designs to push' and 'what
should I do this week' with evidence" — the exact framing in the wave's own goal. That
means giving it real analytical tools (period comparison, ad performance, design
insights, fulfillment health) instead of just read access to raw data.

## What went wrong
- This wave shares the memory-location mistake described in wave 16's entry: agents
  working on waves 16 and 17 together wrote memory files into `invai-docs/.claude/` and
  `waves/17/.claude/` instead of the real `.claude/agent-memory/` path, because the tech
  lead's shell had started inside an `invai-docs` subfolder. The fix (start every agent
  from the `invai/` root, backed by a `PreToolUse` hook) is recorded against this wave
  jointly with wave 16 in `team/lessons.md`.
- T-17-2 and T-17-3 both carry `tenancy` and `ai` risk flags — giving the assistant tools
  that read a shop's ad spend, design performance and fulfillment data means every one of
  those tools has to prove it can't leak another tenant's numbers, on top of proving it
  answers correctly.

## What the team learned
- New assistant "tools" are, mechanically, just more oRPC-style calls with a tenancy
  boundary — the same `withTenant` discipline that protects every other endpoint has to
  extend to anything the AI model is allowed to invoke on the shop's behalf, which is why
  T-17-2 carries the same risk flags a normal backend card would.
- The repeated memory-path mistake (first wave 16, then still happening here) is the
  clearest example in this project of why a *written* fix sometimes isn't enough on its
  own — the real fix landed as a hook, not a repeated reminder, once the same mistake
  recurred across two waves in a row.

## Files to look at
- `invai-contracts/src/schemas/ai.ts` (`AssistantEvent.tool_call.name`) — T-17-1.
- `invai-backend/src/modules/ai/assistant-tools.ts` — the four new analyst tools (T-17-2).
- `invai-backend/src/ai/prompts/index.ts` (assistant prompt v4), `src/ai/gateway.ts`
  (assistant path) — T-17-3.
- `invai-web/src/routes/_app/assistant.tsx` — the new tool chips and starters (T-17-4).
- `invai-docs/team/lessons.md` (2026-09-26/27, "Wave 16/17" row).
