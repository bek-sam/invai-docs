# T-27-1: Image-generation provider (mock default, OpenAI GPT Image behind a flag) with caps

| Field | Value |
|---|---|
| Wave | 27 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008, phase B) |
| Spec | `specs/listing-photos.md` |
| Owner | ai-engineer |
| Reviewer | reviewer (fable) |
| Co-reviewers | security-reviewer (opus): new outbound provider path, spend controls, what leaves InvAI |
| Risk flags | ai, outbound, payments (spend) |
| Model | opus |

## Read first
- `.claude/agents/ai-engineer.md`, `ai-feature-with-evals`; decisions 0007, 0021, 0022, 0023; `waves/27/wave.md` "Agreed interfaces".
- `invai-backend/src/ai/{gateway,breaker,credits,models}.ts`, `src/ai/providers/openai.ts` and `openai-provider.test.ts` (stubbed-fetch pattern), `src/env.ts`.
- Installed `node_modules/openai` (images API: `resources/images.d.ts`, edit with mask; model ids and size/quality options). Prices from the official pricing page on the day you read it: cite URL and date.

## Owned paths (edit)
- `invai-backend/src/ai/**` (new `src/ai/images/**`), `invai-backend/evals/**`, `invai-backend/src/db/schema/ai.ts` (job kind `image_scene` if needed; enumText, no migration unless a column is added)
- Grant: `invai-backend/src/env.ts` + `src/env.test.ts`, only `IMAGE_GEN_PROVIDER` (`mock` | `openai`, default `mock`), `IMAGE_GEN_DAILY_CAP_PER_SHOP` (default 30), `IMAGE_GEN_MOCK_DRIFT` (accepted only when `NODE_ENV=test`); `invai-backend/.env.example` (those lines, commented, provider left `mock`). backend-foundation's file; keep to those lines.
- `invai-docs/build/runbook.md`: the three env vars and "how the owner turns real image generation on" (additive lines; docs-writer is told in the report).

## Read-only paths
- `src/modules/photos/**` (T-27-3), every other module, `src/integrations/**`, `invai-imaging/**`, `invai-web/**`, `invai-contracts/**`.

## Acceptance criteria
1. **Provider selection.** `getImageProvider(companyId)` returns the mock unless `IMAGE_GEN_PROVIDER=openai` **and** `OPENAI_API_KEY` is set **and** the company is not a sample workspace. A blank key counts as unset. Production with `IMAGE_GEN_PROVIDER=openai` and no key refuses to boot with a clear message.
2. **OpenAI provider.** Confirm in `node_modules/openai` (7.25) and the official docs: mask semantics (guidance only), allowed sizes, `input_fidelity`, and report them (plan review item 8). Uses the image edit endpoint with the base image and the mask (print area protected), the configured model and quality, `n=1`, no `user` PII; prices per image from a table in `models.ts` with the source URL and date; returns `costCents` from that table. HTTP layer stubbed in tests (request body inspected: mask present, prompt has the no-brand/no-likeness rules and "leave the print area blank", no design pixels sent beyond the blank garment base). Timeouts and 4xx/5xx map to the gateway's typed errors; no retry storms (at most one retry on 5xx).
3. **Mock.** Deterministic (same base + prompt → identical bytes), returns a recognisable scene (background, light, simple props) around the base at one of the real provider's output sizes, and also perturbs the whole frame slightly (like the real model re-rendering), while keeping the garment outline in place, `costCents=0`, `containsPerson` true for on-model/lifestyle-with-person scene kinds. For OpenAI, `containsPerson` comes from the requested scene kind (conservative), never from the output. `IMAGE_GEN_MOCK_DRIFT=1` (tests only) changes the protected print region.
4. **Caps before each call.** `assertImageGenAllowed` refuses with the contract's cap error when the shop has used its daily image cap (count from DB or a Redis counter keyed by company and UTC day, consistent with `breaker.ts`), with `CREDITS_EXHAUSTED` when credits are short, and with the platform cap error when the platform daily AI spend cap would be exceeded. The mock counts toward the shop cap too (so the UI can be tested), but never toward money spend. `recordImageGen` records spend (`recordSpend`) and an `ai_jobs` row (provider, model, cost) after each call.
5. **Scene prompts.** `buildScenePrompt` produces prompts that never include the design's text or brand words, never ask for a real person, celebrity, child or logo, and always ask for the print area left plain. An eval set (≥ 10 analyses including brand-like design text) checks those rules on the built prompts (deterministic, mock mode).
6. **No real spend by the team.** Nothing in code, tests, seed or scripts sets `IMAGE_GEN_PROVIDER=openai`. Runbook says the owner enables it (OI-25).

## Verification
- `pnpm vitest run --reporter=dot src/ai src/env.test.ts 2>&1 | tail -n 40`; once at the end the full `typecheck && lint && test` with pipefail and a log (Bash timeout 600000); `pnpm evals scene-prompts` (mock).
- Script exercise (not committed) on the dev DB with keys blanked: generate 2 mock scenes for a Desert Bloom base image, show the spend/cap counters; set the cap to 1 via env and show the second call refused.

## Out of scope
- Orchestration in the photos module (T-27-3), imaging compositing (T-27-2), any real API call (no key may be used by the team).

## Commit and report
- Commit own paths (stub `getImageProvider`/`assertImageGenAllowed`/`buildScenePrompt` first), co-author line from your instructions; don't push. Report `invai-docs/waves/27/reports/T-27-1.md` (≤ 60 lines, PIDs); reply ≤ 8 lines.
