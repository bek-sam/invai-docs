# T-P7-5: The assistant re-checks the spend caps before every tool round and records spend per round (B-115)

| Field | Value |
|---|---|
| Wave | P7 |
| Scope ref | `always-in-scope: security` (LLM10 unbounded consumption, research 12 §1.9; B-115 third gap) |
| Spec | backlog B-115; `waves/17/reviews/T-17-3-security-reviewer-r1.md` §4 (Loop limits); `invai-backend/src/ai/breaker.ts`, `credits.ts`, `gateway.ts:113-161, 233+`, `providers/anthropic.ts:95-156` |
| Owner | ai-engineer |
| Reviewer | reviewer (sonnet) |
| Co-reviewers | security-reviewer (fable) |
| Risk flags | payments (AI spend) |
| Model | opus |
| Depends on | plan review (architect on the mid-run stop) |

## Owned paths (edit)
- `invai-backend/src/ai/**` (gateway, breaker, credits, providers, their tests)

## Read-only paths
- `invai-backend/src/modules/ai/**` beyond reading (if the router must change, stop and report), `invai-contracts/**`, every other repo.

## Today
`runAssistant` checks credits (≥ 1) and `assertSpendAvailable` once before the tool loop; the provider then runs up to `ASSISTANT_MAX_ITERATIONS` (10) model rounds; `recordSpend` and the credit charge happen once at the end (`finishJob`). One question can run all 10 rounds after the platform or shop cap is already spent.

## Architect ruling R3 (`reviews/plan-architect.md`, applied before start)
- The SDK runner only sends the next request when pulled. After each round's final message the provider yields an internal `round {usage, model, stopReason}` event; the gateway acts on it and never passes it to the service.
- Check only when `stopReason` is `tool_use` or `pause_turn`. On a trip: close the generator, `finishJob` with the usage so far (status done, `stopReason: "spend_cap"`), rethrow without `failJob` overwriting it.
- The error stays `ORPCError AI_SPEND_CAP_REACHED` (`breaker.ts:139`), mapped to `{type:"error", code:"spend_cap"}` by `modules/ai/service.ts:1320`. (Web shows the English message and ignores `code`: backlog row for web-engineer, not this card.)
- Spend: after each round, record cumulative cost minus what is already recorded; `finishJob` records only what is left (never below 0). Never add up rounded per-round costs.
- Credits: charge once at the end; between rounds check `assertCredits(tokensToCredits(usageSoFar) + 1)`.

## Acceptance criteria
1. Before each model round after the first, the gateway (not each provider separately) re-checks the platform and shop daily caps with `assertSpendAvailable`, counting the spend of the rounds already made in this run.
2. Spend is recorded per round (`recordSpend` with that round's cost), not only at the end, so a parallel question sees it; the total recorded for a run equals what was recorded before this change for the same token usage (no double count: test it).
3. When a cap is hit mid-run, the run stops before the next model call and ends cleanly: the stream sends what was answered so far plus the existing typed spend-cap error the UI already maps (no new contract code; if one is needed, stop and report), the job is finished with the real usage charged, and a critical alert follows the existing breaker path.
4. Credits: if the shop's credit balance would go below zero by the next round's minimum (use the existing `assertCredits` rule), stop the same way. Say in the report how you count a round's cost before it runs (or why you check after).
5. Mock provider runs behave as today (no spend recorded, no checks that would block the golden path's step 12).
6. Tests (vitest on `invai_test`): a fake provider with 3 rounds where the cap trips after round 1 → exactly 1 model call after the trip is refused, usage charged for rounds made, stream ends with the typed error; a run under the cap → identical result and totals to before; mock provider → no breaker call. Each new test red on a64533e (say how you showed it).

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint 2>&1 | tail -n 20`, `pnpm vitest run src/ai --reporter=dot 2>&1 | tail -n 20`, then the full `pnpm test 2>&1 | tail -n 20` once at the end (explicit 600000 ms timeout).
- Live: `PORT=3175 REDIS_URL=redis://localhost:6379/10 pnpm dev:api` on the shared dev DB (read-only use), ask the assistant one question as `owner@desertbloom.test` (mock provider) → answered as before. Refused case: a role without assistant permission gets FORBIDDEN.

## Out of scope
- Prompt or model changes, the iteration limit, credit prices, Message Batches, the market or digest AI routes.

## Rules
- Role file `.claude/agents/ai-engineer.md`; run `threat-model-change` first (short result at the top of the report). Memory: `/Users/bekbolsun/invai/.claude/agent-memory/ai-engineer/`.
- Other agents at the same time: qa-engineer (`invai-web/e2e/**`, its own scratch stack on :3171 and Valkey 12), product-designer (`invai-ui`), platform-sre (hooks). Don't touch their files or ports.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; stop your API on :3175 (and its tsx watch parent) before you hand back. Record every PID you start and list it (stopped) in the report.
- Trim output. Report (≤ 60 lines) to `invai-docs/waves/P7/reports/T-P7-5.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
