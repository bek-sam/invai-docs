# T-8-3: AI cost table and mock hardening (B-45)

Owned files (wave.md "File ownership and batches", batch 1, parallel with T-8-2 and T-8-5): `src/ai/models.ts`, `src/ai/providers/mock.ts`, `src/ai/credits.ts` (test-only edits), its own `describe` block in `src/ai/ai.test.ts`.

## Acceptance criteria
1. **Cost table:** `tokensToCostCents` reads a per-model price table (config, with source and date), covering Opus, Sonnet and Haiku, cache read and write, and batch. There are no hard-coded Opus 5 prices. Check current prices through the `claude-api` skill or official docs.
2. **Mock:** the AI mock no longer throws on unknown prompts. It returns a schema-valid default and logs a warning.
3. **Credits:** credit charging uses the table. A test pins the cents for each model.
