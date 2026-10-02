# Review of T-P8-ai-openai (round 1)

- Reviewer: reviewer on Fable 5.1
- Author: ai-engineer on Opus
- Verdict: approve
- Commits reviewed: invai-backend adf0e25 + 3889bf6 (S-49 follow-up), invai-docs e7b50f4. Working tree clean at 3889bf6.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (at 3889bf6) | tsc clean; biome 467 files, no fixes |
| `pnpm vitest run --reporter=dot src/ai src/env.test.ts src/modules/ai/service.test.ts` | 10 files, 147 tests passed |
| `pnpm vitest run --reporter=dot` (full suite, at 3889bf6, nobody else running vitest) | exit 0; 182 files passed / 2 skipped; 1502 tests passed / 3 skipped / 1 todo (an earlier run overlapping the author's mid-review edits showed 1 failure; not reproducible once the tree was stable) |
| Step 8: `src/env.test.ts` copied onto `origin/main` archive | the 4 new "AI provider keys" cases FAIL on base code (14 others pass): the tests prove the change |
| `pnpm evals assistant` | `mode: mock (no ANTHROPIC_API_KEY or OPENAI_API_KEY)`, plumbing 42/42 |
| `OPENAI_API_KEY=sk-fake OPENAI_BASE_URL=http://127.0.0.1:9/v1 pnpm evals trademark_judge` | prints `mode: openai`; every case fails with "Connection error." only; the key never appears in output |
| `scan-test-weakening.sh invai-backend origin/main` | hits: `vi.spyOn(openaiProvider, …)` (injects a stub-fetch client into the same `createOpenAiProvider`, not a mock of the unit) and the `isTest` branches in `env.ts` (the deliberate "no paid model under test" control, tested). Removed assertions 0, added 72. No `.skip/.only`, no snapshot or config changes |
| `git diff --stat origin/main` both repos | every path inside the card's owned list (incl. the granted env.ts/env.test.ts, docs rows) |
| `grep CHECK drizzle/0000_init.sql` on `ai_jobs.provider` | plain `text DEFAULT 'mock'`, no CHECK: no migration needed, as the card says |
| `node_modules/openai` 7.25.0 `shared.d.ts`, `helpers/zod.js`, `lib/transform.js` | `ReasoningEffort` includes `'none'`; `zodTextFormat` (Zod 4 path) closes objects and throws on `.optional()` without `.nullable()`; prompt schemas in `src/ai/prompts/index.ts` use only `.nullable()`, so the strict schema is accepted; lockfile adds `openai` only (optional peers already present) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `openai-provider.test.ts` structured test: body hits `/responses`, `ai_jobs.provider=openai`, `model=gpt-6.1-sol`, `costCents=tokensToCostCents(u, model)`; `usageOf` subtracts `cached_tokens` from `input_tokens` (correct for OpenAI's usage shape); `priceFor` prices dated snapshots |
| 2 | yes | selection test (openai → anthropic when both keys → mock); sample-workspace test; `env.test.ts` dev cases |
| 3 | yes | `env.test.ts`: prod boots on OpenAI key alone with `"ai":false`; neither key → missing `ANTHROPIC_API_KEY` |
| 4 | yes | `text.format` `json_schema strict:true` asserted on the body; refusal → `UPSTREAM_FAILED` service `OpenAI`, job failed, 0 credits; cut-off and schema-invalid → `UPSTREAM_FAILED` |
| 5 | yes | two-round tool loop (tool events, streamed deltas, `function_call_output` in a data envelope); cap trips after round 1 with exactly 1 request; stops at `ASSISTANT_MAX_ITERATIONS`; reasoning items replayed with `include: ["reasoning.encrypted_content"]` for `store:false` |
| 6 | yes | body assertions: no email/phone/street in `input`, injection text inside `<data source="listing_text">`, `store:false` on structured and both assistant requests |
| 7 | yes | eval runs above |
| 8 | yes | ADR 0021 + index row, runbook env rows, cost rows, DRAFT sub-processor rows (en + es) in e7b50f4 |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy (gateway paths unchanged, `withTenant` in tests), idempotency (run-twice tests: two jobs, counter = sum), money in cents, en/es sub-processor rows
- [x] Decisions recorded (0021)

## Optional notes (not blocking)
- 0021 is `accepted` with type architecture but written by ai-engineer; the architect should confirm or it should read `proposed` (record-decision step 2).
- The SDK still honours `process.env.OPENAI_BASE_URL` (how the author drove the stub). An unexpected env var in a deployed stage would redirect scrubbed shop text; worth a one-line reject in `env.ts` or a note for platform-sre when the SST secret lands.
- `reasoning.effort: "none"` on `gpt-6-luna` and the Sol ids are unverified against the live API; the first real `pnpm evals` run should include `market_niche`.
