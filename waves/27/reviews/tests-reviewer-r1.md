# Review: security-reviewer marker tests, wave 27 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: security-reviewer (tests) / various fix authors
- Scope: invai-backend commits 2075e12, 6b3e25e, 87d26ed (security.test.ts additions) and the word-flip
  in fix commits dca1668, f65dd4e, 3a499e1
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show <fix-commit> -- <security.test.ts>` for dca1668, f65dd4e, 3a499e1 | Each diff is exactly one line, `it.fails(...)` → `it(...)`; no other edit to the test |
| `git show --stat` for 2075e12/6b3e25e/87d26ed | Each touches only its own `security.test.ts` file |
| `git show --stat` for dca1668/f65dd4e/3a499e1 | Fix commits touch source (client.ts, media.ts, openai.ts, caps.ts, types.ts, scenes.ts) plus their own `*.ts` tests (media.test.ts, images.test.ts) plus the one-word flip — no edits to any other security-reviewer file |
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/integrations/channels/shopify/security.test.ts src/ai/images/security.test.ts src/modules/photos/security.test.ts` | `3 passed (3)`, `9 passed (9)`, exit green (a harmless Vite-server close-timeout line follows, not a failure) |

## Checks
- [x] Only security-reviewer's own files changed by the reviewer's commits (`git diff --stat` per commit above)
- [x] Fix commits' edit to each `security.test.ts` is exactly the `it.fails`→`it` word, confirmed by diff
- [x] Tests assert real behavior, not unfalsifiable: shopify test counts actual mutation calls (`mutations===1`) and stored media length; images test checks Redis spend counters (`>=`) and that a 3rd call hits `IMAGE_DAILY_CAP_REACHED`; photos test counts provider calls vs billed `ai_jobs` rows with `costCents>0`
- [x] No mock of the unit under test: shopify stubs global `fetch` (external dependency), not `shopifyGraphql`/`media.ts`; images test stubs only the OpenAI HTTP client, not `recordImageGen`/`caps.ts`; photos test mocks `../../lib/s3` and only `getImageProvider` from `../../ai/images` (spreads the real module), leaving the actual unit under test — `scenes.ts`'s `ensureScene`/`recordImageGen` ordering — unmocked
- [x] No shared-state leak: photos test's hoisted `h` fixture is reset in a file-level `afterEach` (`h.on=false`, `store.clear()`, `vi.restoreAllMocks()`); images test restores `env` fields and `redis.del`s its keys in a `finally`; shopify test resets throttle/sleep and unstubs globals per test
- [x] Pre-fix state check: at 87d26ed (before dca1668/f65dd4e/3a499e1 respectively) each test is `it.fails`, consistent with genuinely failing on base code
- [x] Fix diffs are minimal and match what the test asserts (e.g. `scenes.ts` reorders `recordImageGen` before `putObject`; `shopifyGraphql` gains `retryServerErrors: false` on the media mutation; `caps.ts`/`openai.ts` add `mayBeBilled` and count failed-but-possibly-billed calls)

## Optional notes (not blocking)
- None.
