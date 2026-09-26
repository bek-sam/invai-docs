# T-8-5: Eval harness (B-48)
Evidence: decision 0007 (AI model policy).

Owned files (wave.md "File ownership and batches", batch 1, parallel with T-8-2 and T-8-3): new `invai-backend/evals/**`; the `scripts.evals` line in `package.json`; the new step in `.github/workflows/ci.yml`. Read-only on `src/ai/**` and `src/modules/ai/**`.

## Acceptance criteria
1. **Harness:** `invai-backend/evals/` with `evals/run.ts` and one eval set per AI route (listing copy, trademark judge, personalization check, assistant tools; at least 10 cases each, scrubbed of PII).
2. **Scoring and output:** each case is scored by schema validity plus rule checks, or an LLM judge where needed. The run prints pass rate, cost and latency per route.
3. **Mock mode:** CI already runs with no `ANTHROPIC_API_KEY` (see `.github/workflows/ci.yml`), so `env.mocks.ai` is `true` there and the harness runs against the mock and checks the plumbing automatically; the same is true for a local run without a key. With a key, it runs for real.
4. **Command:** `pnpm evals` (script: `"evals": "tsx evals/run.ts"`) is documented in the repo README, wired into CI right after the `test` step, and runs against `pnpm run --if-present`. There's a baseline results file checked in.
