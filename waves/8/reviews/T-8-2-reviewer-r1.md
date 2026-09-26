# Review of T-8-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: ai-engineer on Opus (per wave.md; report says Opus 5.5)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-review-t82 9586158` | worktree at the reviewed SHA |
| `node_modules/.bin/tsc --noEmit` | clean, no output |
| `node_modules/.bin/biome check .` | "Checked 268 files in 294ms. No fixes applied." |
| `node_modules/.bin/vitest run` (full suite, `invai_test_t82`, Valkey `/2`) | 79 files / 587 tests passed, 135s — matches the report's 79/587 |
| `git diff 874bb7f 9586158 -- src/ai/ai.test.ts` (T-8-3's commit vs T-8-2's) | only insertions + import restructuring; no line of T-8-3's block removed or weakened |
| `git diff 874bb7f 9586158 -- src/env.ts` | exactly the two new env vars, matches the tech-lead grant in wave.md |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t82 e958638` | 2 hits, both read and non-blocking (below) |
| `git -C invai-contracts grep -n "ai_spend_cap"` | confirms `ALERT_KINDS` already carries `ai_spend_cap_tenant`/`_platform` from the architect's contract-stub commit `4f4efcd`; T-8-2 correctly didn't need a contracts change |
| `git show 9586158 --stat` | only `src/ai/ai.test.ts`, `src/ai/breaker.ts` (new), `src/ai/gateway.ts`, `src/ai/prompts/index.ts`, `src/env.ts` — all owned or granted |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Delimited data blocks for every untrusted field | Yes | `dataBlock()` in `prompts/index.ts:34` used for design/blank/shop_brief/validation_errors (`listing_copy`), listing_text/candidate_marks (`trademark_judge`); assistant tool results wrapped by `isolateToolResults()` (`gateway.ts:147`) into a JSON envelope, and `ASSISTANT_PROMPT.system` explicitly names the envelope and says never to obey it. Only 3 call sites into the gateway exist in the whole backend (`service.ts:437/444` listing_copy, `service.ts:1042` assistant, `trademark.ts:141` trademark_judge) and all three route through the prompt registry's `user()` renderer, so nothing bypasses `dataBlock`. |
| 2. Injection test set, schema/tool-invariant | Partially — proven against the mock, not a live model | `ai.test.ts:202` INJECTIONS (7 strings: ignore-previous, DAN, `</data>` breakout, XML/JSON fake tool_use, fake "Assistant:" turn, null+bidi override) never leak outside a data block for either prompt, block counts balance, output schema keys unchanged, and no extra tool call fires for the assistant. The report is upfront that a real-model run needs `ANTHROPIC_API_KEY` and is deferred to T-8-5's eval harness — a disclosed, reasonable gap given no key exists in this environment. |
| 3. Spend breaker per contract stub B | Yes | `breaker.ts` matches stub B's keys, `MGET`/`MULTI INCRBY`+`EXPIRE 26h`, error shape, tenant-checked-first, dedupe via `SETNX`-style `SET NX`. Verified live against real Valkey+Postgres: tenant cap hit → 429 with exact `data`, 1 alert + 1 outbox row across 3 hits; platform cap hit blocks a third tenant, 1 alert total across 3 companies; cap 0 disables a scope; mock/sample calls never touch counters even with the tenant counter pre-set to 1e9. |
| 4. Tests: per-route data-block unit tests + both-scope breaker tests | Yes | Both present and passing, see above. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` — `ai.test.ts`, `breaker.ts`, `gateway.ts`, `prompts/index.ts`, `env.ts`; the last is under the wave.md grant)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — scan hits reviewed individually (below)
- [x] Tenancy / idempotency / money in cents / en-es — `recordSpend` runs after the `withTenant` transaction commits (side effect outside the DB transaction, per the hard rule); money is in integer cents throughout; alert text is English-only, matching the existing pattern for every other alert in `today/service.ts` (not a regression this card introduces)
- [x] Decisions recorded — report's "Decisions" section covers mock-skips-breaker, fail-open, platform-alert-target, JSON-envelope-not-XML

### Test-weakening scan, read in full
1. `models.ts` / `MODEL_PRICES[id]).toBeTruthy()` flagged — this is T-8-3's own test line, not T-8-2's owned block; out of scope for this review.
2. `gateway.ts`: `if (provider.name !== "mock") await assertSpendAvailable(...)` flagged as a "test-only branch" pattern — it isn't one. It's the production rule from wave.md stub B ("Sample workspaces... never touch these counters"), exercised by the "mock calls neither read nor move the counters" test, not a hack added to make a test pass.

## Optional notes (not blocking)
- `breaker.ts`'s check-then-act shape (MGET before the call, INCRBY only after it finishes) is an inherent TOCTOU gap: enough concurrent calls from one tenant can all pass the pre-check before any of them records spend, so the cap can be overshot by up to (in-flight calls × per-call cost). This is the design wave.md asked for ("cheap: a Valkey GET"), and current AI routes are triggered per user action with low natural concurrency, so today's exposure is small — but if a bulk/looped listing-generation feature ships later, this is worth a hardening pass (a Lua CAS, or capping concurrent "running" ai_jobs per tenant).
- `assertSpendAvailable`'s Valkey-timeout fail-open logs an error but does not raise an alert (see the security-reviewer file for the fuller take — the PIN-lockout code has the identical shape today, so this isn't a new pattern, but it's still worth a tracked finding).
