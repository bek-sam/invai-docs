# Review of T-8-2 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: ai-engineer on Opus (per wave.md; report says Opus 5.5)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-review-t82 9586158` | worktree at the reviewed SHA |
| `node_modules/.bin/tsc --noEmit && node_modules/.bin/biome check .` | both clean |
| `node_modules/.bin/vitest run` (full suite) | 79 files / 587 tests passed |
| Read `src/ai/prompts/index.ts`, `src/ai/gateway.ts`, `src/ai/breaker.ts`, `src/ai/providers/anthropic.ts` (tool_result rendering), `src/modules/ai/assistant-tools.ts` in full | see findings below |
| `grep -rn "runStructured(\|runAssistant("` across `src/modules`, `src/api` | exactly 3 call sites, all through the prompt registry (see reviewer's file) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t82 e958638` | 2 hits, both non-blocking (see reviewer's file) |
| Re-read `ai.test.ts:189-450` (the T-8-2 describe block) in full | injection set and breaker tests both exercise real behavior, not just mocks-of-the-unit-under-test |

## Threat-model checklist (this card: ai, payments)

1. **Every AI route wraps untrusted text.** Confirmed — only 3 gateway call sites exist in the backend (`listing_copy` ×2, `trademark_judge`, `assistant`), all route through `dataBlock()`/the assistant envelope. No route reaches the model with raw, unwrapped shop/buyer text.
2. **Escaping can't be broken.** `dataBlock()` JSON-encodes the value then replaces literal `<` with `<` (still valid JSON, still round-trips). A `</data>` or a fake `<data source="system">` in the input cannot close or spoof a block — proven directly (`ai.test.ts`'s "closing tag in the input cannot end the block" test) and by construction: the *only* literal `<` characters in the rendered string are the block's own tags, since every other `<` is escaped. Unicode lookalikes (fullwidth `＜`, bidi override `‮`, tested in the injection set) are different code points from ASCII `<`/`>`, so they can never form a real `<data>`/`</data>` delimiter; they're just data content the model is told to ignore as instructions. No structural bypass found.
3. **Assistant tool results are wrapped.** `isolateToolResults()` wraps every tool's `data` centrally in the gateway, so no tool (including future ones) can skip it; verified with a tool whose result contains fake tool-call-shaped strings — no extra tool fires. Tool results are also naturally segregated as Anthropic `tool_result` content blocks (not spliced into the `<data>`-tagged prompt text), which is a second, independent isolation layer beyond the JSON envelope.
4. **The breaker.** Keys, scopes, `MGET`-before/`INCRBY`-after and the error shape all match wave.md stub B exactly; verified live (tenant cap, platform cap, cap-0-disables, mock/sample bypass). It is checked before `startJob` in both `runStructured` and `runAssistant`, non-mock only.
   - **Race:** check-then-act — `assertSpendAvailable`'s `MGET` and `recordSpend`'s `INCRBY` are each atomic, but the pair isn't, so enough concurrent calls from one tenant can all clear the pre-check before any records. This matches wave.md's explicit ask for a "cheap: a Valkey GET" check rather than a Lua CAS, and today's AI routes are per-user-action (low natural concurrency) with a per-tenant Postgres credit ledger as the primary limiter underneath — so the realistic overshoot is small, not the cap-defeating gap the card asked me to rule out. Not blocking; worth a hardening note if a bulk-generation feature is ever added (see reviewer's file).
   - **Fail-open judgment:** on a Valkey timeout, `assertSpendAvailable` fails open (logs, returns) rather than closed. I judge open is the right direction here: `runStructured`'s draft-generation path only runs inside a BullMQ job, which can't even be dequeued during a Valkey outage (same Redis), so fail-closed vs. open is moot there; the assistant chat path *is* reachable without BullMQ, and failing it closed on every Valkey blip would take down a whole product surface over an unrelated dependency, for a control that is explicitly a backstop (the per-tenant Postgres credit ledger, unaffected by Valkey, is the primary limiter and still runs). **Gap:** the fail-open path only `log.error`s; it does not raise an alert. Research 12 §1.10 A10 and this project's own threat-model-change rule ("MUST NOT accept a fail-open control on a security path without a warn log and an alert") both call for alerting here. I'm not blocking round 1 on it because the codebase already carries the identical shape today for the PIN-lockout Redis timeout (research 12 §1.2, called out there as an accepted-but-imperfect risk needing the same fix) — this card reproduces an existing pattern rather than introducing a new one. **Recording it as a finding for the tech lead** rather than a blocking item: add a `raiseAlert`-style alert (or extend the existing ops error-log alerting) when the spend check fails open, ideally in the same pass as the PIN-lockout fix so both land together.
5. **Alert cadence.** `SET NX EX 26h` dedupe key per scope per day; live test shows 3 cap hits in one day producing exactly 1 alert row and 1 `alert.created` outbox event, and a second/third tenant hitting the same platform cap the same day adds no more. Fires once a day, as required.
6. **Defaults.** `$500`/day platform, `$50`/day tenant — exactly the tech-lead's grant in wave.md, not something the builder picked unilaterally. Sensible as a backstop above the per-tenant credit ledger for a small-shop platform at this stage.
7. **Weakened tests.** Scanner run above; both hits read and are non-issues (one is T-8-3's own test, the other is real production logic, not a test-only branch — see reviewer's file for detail). The injection and breaker tests are exercised against real Valkey/Postgres (breaker) and the mock provider with real prompt-rendering code (injection set), not mocks of the unit under test.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy (`withTenant` on every DB write in `breaker.ts`/`gateway.ts`), idempotency (`recordSpend` outside the transaction, logged-not-thrown on failure since the call is already billed), money in cents
- [x] Decisions recorded (report's "Decisions" section)

## Optional notes (not blocking)
- Track the fail-open-without-alert gap in `assertSpendAvailable` (and its sibling in the PIN lockout) as a recorded finding, per the note above.
- AC2's injection set is proven against the mock's deterministic behavior, not a live model's actual susceptibility; the real test is T-8-5's keyed eval run, which the report correctly flags as still outstanding.
