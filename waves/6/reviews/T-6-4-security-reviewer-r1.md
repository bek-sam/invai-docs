# Review of T-6-4 (round 1) — security-reviewer co-review

- Reviewer: security-reviewer on Sonnet 5
- Author: ai-engineer (backend `0e2822e`) on Opus
- Verdict: **approve**

Risk flags: AI spend / cost control (AC7), stream lifecycle / billing correctness (B-101). This
co-review uses `threat-model-change`'s lens; the full command table is in
`T-6-4-reviewer-r1.md`, not duplicated here.

## 1. What changes
`aiProvider()` becomes `aiProvider(companyId)` and consults `isSampleWorkspace(companyId)`
(T-6-5's helper, reused not reimplemented) to force the mock provider for any sample workspace
even if `ANTHROPIC_API_KEY` is set. `finishJob`'s cost check now keys off `result.model ===
MOCK_MODEL` instead of `env.mocks.ai`, so a sample workspace's cost is $0 regardless of *why* it
got the mock. Separately, `runAssistant`/`ask()` now close their generators and charge tokens on
client disconnect instead of leaving the `ai_jobs` row stuck `running`. No new tables, no new
webhooks, no new public endpoints.

This directly closes the gap `T-6-5-security-reviewer-r1.md` §6 flagged as a "new finding for
`security/v1-review.md`": *"AI spend from a sample workspace is unguarded... Anthropic calls
(listing drafts, assistant) use the platform key regardless of demo status."* That finding should
be marked resolved once this card ships.

## 2. Entry points
| Entry point | Who can call it | Tenant comes from | Guard |
|---|---|---|---|
| `ai.listings.generate`/regenerate, `ai.assistant.ask`, trademark check | user, `ai.listings.manage`/`ai.assistant.ask` | session `ctx.companyId` | `aiProvider(meta.companyId)` on every call site (`gateway.ts:138,184`), no caller can pass a different company's id — `meta.companyId` comes from `ctx`, not input |
| Assistant stream teardown on disconnect | oRPC `eventIterator`, not user-triggered | same session | `runAssistant`'s `finally` closes the provider generator and calls `finishJob` unconditionally; `ask()`'s outer `finally` mirrors it |

All inputs on these paths are unchanged Zod-validated contract inputs; nothing new here is
attacker-controlled beyond what already existed.

## 3. Data touched
No new PII, no new logging beyond existing patterns. `usageSoFar`/token counts are internal
accounting numbers, not user content.

## 4. Threats
| # | Threat | This change | Control (file:line) | Gap? | Test |
|---|---|---|---|---|---|
| 8 | Abuse without limits / real money from a sample workspace | the card's whole point for AI spend specifically | `aiProvider` (`gateway.ts:28-30`), `finishJob` cost check (`gateway.ts:107`) | none for the guard itself. **Unrelated residual gap, not introduced by this card:** the Shopify CSV variant-option bug (`T-6-4-reviewer-r1.md` blocking finding #1) is a correctness issue, not a security one — no cost/tenancy exposure from it. | `service.test.ts`'s AC7 case: flips `env.mocks.ai=false`, proves sample company still gets mock, real company gets `anthropic`; fails on pre-card code (confirmed by running it against `git archive 3feb9ff`) |
| 8b | Billed-but-uncharged tokens (platform pays Anthropic, shop's credit ledger never debited) | fixed for the between-turns and single-turn-complete cases | `runAssistant`'s `finally` (`gateway.ts:190-199`), `ask()`'s mirrored `finally` (`service.ts:1067-1073`) | **Residual, non-blocking:** a disconnect mid-turn (the common real-world case for a long streamed answer) still under-counts — `usageSoFar` only reflects the last *completed* tool-loop turn, not partial output from an interrupted one. The report is honest about this trade-off (rejected rewriting `.return()`'s value from `finally` because it can swallow a real thrown error and trips `noUnsafeFinally`); verifying Anthropic's actual billing behavior on a client-aborted stream isn't possible without a live key in this environment. Recommend a follow-up card once real-key testing is available, not a blocker here — this is strictly better than the prior "never charged, job stuck running forever" bug. | no automated test for the mid-turn-abort case specifically (would need to simulate an abort while inside the anthropic provider's own `for await` — not practical against the mock) |
| 9 | Fail-open | `isSampleWorkspace` DB read fails | unchanged from T-6-5 — throws, doesn't fail open (per T-6-5's own review) | none new | — |
| 10 | Double side effect | disconnect fires `finishJob` twice (once from a real completion racing the teardown) | `settled` flag in both `runAssistant` and `ask()` guards the `finally` branch so it only fires once; `gen.return()` on an already-finished generator is a no-op | none | covered indirectly by the AC7/disconnect unit tests; no dedicated "disconnect races completion" test, but the `settled` guard is straightforward to read correctly |

Everything else in the template (1–7) is not applicable: no new webhook, no new foreign-id/S3-key
input, no new injection surface, no cross-tenant read path (companyId always comes from session).

## 5. Worst outcome
Before this card: any sample workspace with `ANTHROPIC_API_KEY` set (or once one gets set
platform-wide) could spend against the real model with no cap — the exact gap T-6-5 flagged and
deferred. After this card: closed for every AI route (listings generate/regenerate, trademark
judge, assistant), verified by a test that fails on pre-card code. The residual mid-turn-disconnect
under-counting is a billing-accuracy nit, not a new abuse path — it doesn't let a sample workspace
spend real money (it's still forced to mock), it only means a *real* company's disconnect mid-answer
might undercharge that company's own credits slightly, which is a minor internal-accounting gap,
not a security issue.

## 6. Decisions and follow-ups
- No blocker from a security standpoint. Approving this card's AI-spend and stream-billing changes
  on their own merits.
- Recommend closing out `T-6-5-security-reviewer-r1.md` §6's "AI spend unguarded" finding as
  resolved by this card, and opening a new low/medium follow-up for mid-turn disconnect token
  accounting (not tenancy, not cross-shop — internal cost-accuracy only).
- This card's overall verdict is blocked by `T-6-4-reviewer-r1.md`'s Shopify CSV finding, which is
  outside this review's scope (no security/tenancy/cost dimension to it).
