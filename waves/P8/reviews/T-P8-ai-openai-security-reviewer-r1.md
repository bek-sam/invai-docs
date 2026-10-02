# Review of T-P8-ai-openai (round 1)

- Reviewer: security-reviewer on Fable 5.1
- Author: ai-engineer on Opus
- Verdict: approve (one Low hardening finding, S-49 proposed, owner ai-engineer; not blocking)
- Reviewed: invai-backend adf0e25, invai-docs e7b50f4 only.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (backend) | tsc clean; biome 467 files, no fixes |
| `pnpm vitest run src/ai/openai-provider.test.ts src/env.test.ts src/db/rls-coverage.test.ts src/api/authz.test.ts` | 4 files, 45 passed |
| `pnpm audit --prod` | 2 advisories (1 low, 1 moderate), both esbuild under `better-auth>drizzle-kit/vitest` (known S-32); none in `openai`'s tree |
| `scan-test-weakening.sh invai-backend origin/main` | hits only the intended `isTest` key-drop in `env.ts` and eval mode branches; no loosened test |
| Proof script: `NODE_ENV=test OPENAI_API_KEY=sk-proof OPENAI_BASE_URL=http://127.0.0.1:9/v1 tsx -e` calling `openaiProvider.structured` directly | `env.OPENAI_API_KEY: undefined`, yet the client was built and tried to connect (`APIConnectionError`), so the SDK took the key from `process.env` (see finding) |
| Dependency: `node_modules/openai/package.json` | 7.25.0, Apache-2.0, no install scripts; `pnpm-workspace.yaml` unchanged (no release-age exclusion, no `allowBuilds` entry); lockfile committed |
| Read: `openai.ts`, gateway diff, `env.ts` diff, `isolateToolResults`, SDK `client.js:178,228`, `internal/utils/log.js` (redacts `authorization`), `evals/lib/mode.ts` | notes below |

## Acceptance criteria (security scope)
| # | Met? | Evidence |
|---|---|---|
| 2 | yes | selection + sample-workspace tests pass (`openai-provider.test.ts:188,197`) |
| 3 | yes | `env.test.ts` new cases pass; `missingProductionKeys` accepts either key, blank OpenAI key still counts as missing |
| 4 | yes | `text.format` strict json_schema asserted; refusal/incomplete/failed checked before output (`checkStop`); Zod `safeParse` on the answer |
| 5 | yes | tool args validated with the tool's Zod schema before `run`; tool errors returned generically; `round` yielded before the next request; spend-cap test shows round 2 never requested |
| 6 | yes | request body asserted free of email/phone/street and injection string inside `<data source="listing_text">`; `store:false` on structured and assistant bodies; tool result sent back as `{source:"tool_result:<name>", data}` |
| 8 | yes | ADR 0021, runbook rows, cost rows, DRAFT sub-processor rows en/es (`[COUNSEL: ...]` markers for compliance-officer) |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git show --stat`: src/ai, evals, env.ts/env.test.ts lines granted, schema/ai.ts, package.json, lock, .env.example; docs: card, ADR + index row, runbook, cost doc, legal rows)
- [x] Nothing outside scope (no prompt text change, no contract or web change)
- [x] Tests exercise the behavior through the real SDK with a stubbed `fetch`; `vi.spyOn(openaiProvider, ...)` only swaps the singleton's client, not the unit under test
- [x] Tenancy: tools stay the gateway's tenant-scoped read-only tools; `prompt_cache_key` is shared across shops but OpenAI prefix caching returns only exact-prefix matches (no content crosses tenants); no new tables, no `withSystem`
- [x] Decision 0021 recorded and indexed

## Optional notes (not blocking)
1. **S-49 (Low, hardening, owner ai-engineer):** `src/ai/providers/openai.ts:42` passes `apiKey: env.OPENAI_API_KEY`, which is `undefined` under `NODE_ENV=test`; `openai` 7.25 then falls back to `process.env.OPENAI_API_KEY` (`client.js:178`), and `env.ts:9` loads `.env` into `process.env` for every non-production run. The gateway path is safe (mock under test, proven by the suite), but any test or script that calls `openaiProvider` directly would use the developer's real key and spend it on synthetic text. Same pre-existing pattern at `anthropic.ts:27`. Fix: build the client only when `env.OPENAI_API_KEY` is set (throw a clear error otherwise), and the same for Anthropic; then the ADR sentence "no test run reaches a paid model" is fully true. I will add the S-49 row to `security/v1-review.md` in my next commit.
2. `maxRetries: 2` on a paid structured call can bill twice after a timeout (same as the Anthropic provider); fine for now, note for cost-review.
3. `run.context` goes as a `developer` message (higher authority than user text). It is gateway-built and scrubbed, so equivalent to the Anthropic system block; keep it that way if context ever includes shop-authored text.
