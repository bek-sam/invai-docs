# T-P1-3: AI and market polish, publish concurrency test

| Field | Value |
|---|---|
| Wave | P1 (carries T-23-4, never started) |
| Scope ref | `product/scope.md#mvp-in` items 13, 16; `always-in-scope: bug` |
| Spec | backlog B-114, B-131 (`specs/market-signals.md` Step 3a), B-132, B-135, B-165, B-192, B-229 part 2 |
| Owner | ai-engineer |
| Reviewer | reviewer (opus); it checks the B-131 hunk against `specs/market-signals.md` Step 3a |
| Co-reviewers | none (decision 0019: the author is the prompt owner) |
| Risk flags | ai |
| Model | sonnet |

## Owned paths (edit)
- `invai-backend/src/ai/**`, `invai-backend/src/modules/ai/**`, `invai-backend/evals/**`
- Grant: `invai-backend/src/modules/market/signals.ts`, `compute.ts` (+ their tests), for B-131 only

## Read-only paths
- `invai-web/**` (if B-135 needs a web change, write it as a note for the tech lead; don't edit web), `invai-backend/src/test/**` (T-P1-1), `src/modules/catalog/**` (T-P1-4), everything else.

## Acceptance criteria
1. B-192: the seasonality tool never prints an act-by date in the past; a peak under way uses "season is on now" wording (en and es).
2. B-135: assistant answers render cleanly. Pick the backend side (the model and mock emit plain text, no `**`/`_`), unless you show that's worse; the "Demo mode" footer is translated under es.
3. B-132: the assistant stream closes cleanly (no `net::ERR_ABORTED` in Chrome on a complete answer). If the fix belongs in web, say so with file:line instead.
4. B-114: mock follow-up "And only Etsy?" after an ads question re-scopes the ads tool.
5. B-165: the eval harness deletes its throwaway tenant on exit (also on failure).
6. B-131: the seasonality index is computed on detrended data per the spec step; engine tests show a rising niche no longer reads as seasonal.
7. B-229 part 2: `publish.acceptance.test.ts` "two concurrent publishes land on the same key" compares object keys, not signed URLs; nothing else in the test is loosened.
8. AI tests and mock evals green; the `publish` test passes 5 times in a row under the full suite load.

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint 2>&1 | tail -n 20`
- `pnpm test src/ai src/modules/ai src/modules/market --reporter=dot 2>&1 | tail -n 20`; the mock evals command from `evals/README` (or `package.json`).
- An API on your own port (`PORT=31xx pnpm dev:api`, record the PID): ask the assistant as owner@ in en and es (curl), show the answer text has no markdown markers and the footer is in Spanish.
- If T-P1-1 isn't committed when you start, pin your own test DB and Redis DB (`team/agent-brief.md`).

## Out of scope
- B-134 shared ConfidenceBadge (product-designer, invai-ui). Any web change. New AI routes or model changes.

## Budget
- About 3 hours. Stop and tell the tech lead if blocked for 30 minutes.

Commit only your paths. Don't push. Report: `invai-docs/waves/P1/reports/T-P1-3.md`.
