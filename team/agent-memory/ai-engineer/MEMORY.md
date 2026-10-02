# ai-engineer memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Never `git stash`, `reset` or `checkout --` in a shared tree; compare in your own worktree at the base commit.
- 2026-09-26 W8: Don't push. Only the tech lead pushes, after the gate (a builder once pushed 44 ungated commits).
- 2026-09-25 W3: Shared files: stage only your hunks (`git add -p` / `git apply --cached`), check `git diff --cached`, then commit.
- 2026-09-24 W2: Kill only PIDs you started (`lsof -ti :<your port>`); never `pkill`/`killall`.
- 2026-09-25 W6/7: Never run `pnpm` inside a worktree; call `node_modules/.bin/*` directly. Never re-link shared `node_modules`.
- 2026-09-25 W3: Poll long jobs inside your turn with short sleeps; don't end your turn to wait.
- 2026-09-24 v1: Check the installed library API in `node_modules` before writing code (oRPC 1.15, drizzle 0.45, Zod 4, TS 7, Better Auth 1.7 are newer than training data).
- 2026-09-26 W7: A `db/schema` change ships with its generated migration in the same commit, and you run the backend tests, not only typecheck (68 tests broke once).

## Learned on cards
- [Eval harness notes](eval-harness-notes.md) — run evals on your own test DB via NODE_ENV=test; evals/** isn't typechecked or linted
- [Market signals notes](market-signals-notes.md) — trademark screen threshold 60 for market terms, answer-check number sources, vitest/scratchpad debug tricks
- [Fallback must pass its own check](fallback-must-pass-own-check.md) — market answers need Sample data + date on every branch; baseline only from a fresh DB
- [Digest narrative notes](digest-narrative-notes.md) — T-19-2 validator word lists, breaker state on ai_jobs + Valkey, test DB gotcha
- 2026-09-30 T-A8: v6 analytics tools live in `src/modules/ai/analytics-tools.ts`, gated on `finance.read`; `systemContext()` has no permissions, so evals/tests must pass owner permissions (`permissionsFor("owner")`) or the tools vanish.
- 2026-09-30 T-A8: `mockProvider.assistant(run)` can be driven directly in a vitest (no gateway/credits) to check tool order and answer text; the dev API's tsx wrapper and node child are two PIDs (`lsof -ti :port` shows only the child).
- 2026-09-30 T-P1-3 (B-131): detrending `seasonalityIndex` with one OLS fit over the full series (per spec Step 3a) is correct, but fitting a trend line to an *exactly periodic, no-true-trend* fixture over several whole periods still yields a small nonzero edge-effect slope (the OLS boundary term), so a pre-detrending test's exact expected ratio needs loosening or re-pinning — don't expect bit-for-bit equality with the old raw month-mean formula.
- 2026-09-30 T-P1-3 (B-132): the Chrome `net::ERR_ABORTED` on a complete `ai.assistant.ask` stream is not fixable in backend or web app code — it's `@orpc/client`'s shared `AsyncIteratorClass` (`@orpc/shared` dist, `cleanup("next")` on natural completion) calling `toEventIterator`'s `reader.cancel()` even after `done:true`. Both the generator (`service.ts` `ask()`) and the server's `toEventStream` (`controller.close()` on done) are already correct. A real fix needs a patched `@orpc/client`, an architect-level cross-repo dependency call, not a card-level fix.
- 2026-09-30 T-P1-3 (B-135): backend-composed answer text (mock provider + every tool's code-written fallback `answer`, shown by `fallbackAnswer()` when the model's draft fails twice) is a separate surface from `ASSISTANT_PROMPT`'s system text (the real model's own prose). Stripping `**`/`_` from the former needs no eval; changing the latter bumps the prompt version and needs a real-model eval (`ANTHROPIC_API_KEY`), which wave.md fenced as owner-only — don't touch the system prompt for a markdown-only fix.
- 2026-10-01 T-P4-4 (decision 0020): `src/modules/analytics/finance-testkit.ts`'s `addDesign`/`addOrder` write `profitLines` rows directly with chosen `revenue`/`isReprint`/`designId` — the fastest fixture for any AI-module test needing specific profit-line shapes (already used by `analytics-tools.test.ts`).
- 2026-10-01 T-P4-4: `analyst-queries.ts`'s cross-listing-gaps query gates on `having count(*) >= MIN_UNITS(3)`; a 2-unit reprint fixture needs a 3rd supporting unit to clear that unrelated gate before a filter-removal bug becomes observable. `assistant-tools.ts`'s `topDesigns` has no such gate but also returns no unit count (`id`/`name`/`channel` only) — exporting it and adding a `units` field was the only way to prove the fix without a flaky ranking-tie test.
- 2026-10-01 T-P7-5: to test the real-provider gateway path without a key, flip `env.mocks.ai=false` via a mutable cast (`env` is `as const`, mutable at runtime) and `vi.spyOn(anthropicProvider, "assistant")`; `spendCaps()` reads `env.AI_DAILY_*` on each call. `mockProvider` is typed `Omit<AiProvider,"assistant"> & {assistant: typeof mockAssistant}` so tests calling it directly don't see provider-internal `round` events.
- [OpenAI provider facts](openai-provider-facts.md) — 2026-10-01 T-P8-ai-openai: GPT-6 ids/prices, token accounting, test stubbing, evals via local stub
