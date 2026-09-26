# Review of T-8-6 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: (architect/backend-foundation) on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `perl -e 'alarm 120; exec @ARGV' pnpm typecheck` (invai-backend) | clean, no errors |
| `perl -e 'alarm 120; exec @ARGV' pnpm lint` (invai-backend) | `biome check .` — 290 files, no issues |
| `pnpm vitest run src/api/orpc.test.ts src/modules/orders/import.test.ts src/modules/channels/shopify.test.ts` | 3 files, 24 tests passed (5.3s) |
| `git show aa13ec0 --stat` / per-file diffs | 8 files, all under `invai-backend`, all serve AC1–AC4 |
| Read `node_modules/@orpc/server/dist/index.mjs` (`Builder.use`/`.input`) and `dist/shared/server.DEBcqOjg.mjs` (`executeProcedureInternal`, `enhanceRouter`) | traced actual middleware order (see below) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Shared transform, every oRPC string sanitized, once | yes | `src/lib/text-safety.ts` (`sanitizeText`/`sanitizeDeep`) is the one definition; `sanitizeInput` middleware attached on `pub` (`os.use(sanitizeInput).use(guard)`) covers every procedure built off `pub`/`authed`. Traced `@orpc/server`'s `Builder.input()` (sets `inputValidationIndex = middlewares.length` at the point `.input()` is called on the *contract* builder, where middlewares.length is 0) and `enhanceRouter` (adds the impl's `newMiddlewareAdded` to that index when `implement(contract)` wraps the contract procedure with `pub`'s middlewares). Net effect: `inputValidationIndex` ends up *after* `sanitizeInput` and `guard` in the final chain, so **`sanitizeInput` runs on the raw, not-yet-validated input**, then `guard`, then Zod validation, then the handler. Confirmed behaviorally too: the new `orpc.test.ts` calls the real router end to end and gets a clean stored value. |
| 2. Webhook/CSV paths use the same helper | yes | `importNormalizedOrders` (`src/modules/orders/import.ts:137`) does `sanitizeDeep(parsed.data)` right after `NormalizedOrderSchema.safeParse`. It's the one pipeline `sync.ts` calls for CSV, API poll and webhooks (only caller besides tests, confirmed by grep). EasyPost's `statusDetail` (`src/integrations/carriers/tracking.ts:98`) gets its own `sanitizeText` call, the other webhook path writing free text to a column. |
| 3. Tests: NUL through a procedure, CSV row, webhook, none crash | yes | `orpc.test.ts` (`ai.listings.create`, real router via `call()`), `import.test.ts` (CSV-parsed order through `importNormalizedOrders`), `shopify.test.ts` (signed webhook through the real delivery path). All three assert the stored column is clean, not just "didn't throw". Ran all three — pass. |
| 4. Gateway/`ask()` sanitizers stay | yes | `ai/gateway.ts` keeps calling `sanitizeDeep`/`sanitizeText` on AI vars and assistant input/output; it now re-exports from `text-safety.ts` instead of owning the regex, so existing importers (`ai.test.ts`, `modules/ai/service.ts`) are unaffected. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — `git show --stat` is all 8 files under `invai-backend` (`src/lib`, `src/api`, `src/ai`, `src/modules/orders`, `src/integrations/carriers`, 3 test files); matches T-8-6's backend/architect ownership.
- [x] Nothing outside scope — every changed file serves AC1–AC4; no drive-by changes.
- [x] Tests exercise the behavior, and none were weakened — all three are new, assert real stored DB values through real call paths (router `call()`, real webhook delivery, real import pipeline), not just "no throw". No `.skip`/`.only`/loosened assertions found in the diff.
- [x] Tenancy / idempotency / money / en-es — not applicable; this is a text-sanitization change, no new tables, no money, no user-facing copy.
- [x] Decisions recorded where needed — OI-5 records the tech lead's decision to fix this as one class at the boundary; the report's "Decision" section explains middleware-vs-schema-helper with a concrete reason (every contract `.input()` is `z.object`/union, confirmed by grep).

## Optional notes (not blocking)
- The in-code comment in `orpc.ts` calls the middleware's input "the validated input" — per the trace above, it actually runs *before* Zod validation (on the raw parsed body), not after. Functionally this is the better order (bad bytes are stripped before validators see them, turning a would-be DB crash into, at worst, a clean 400 rather than a 500), but the comment's ordering claim is inaccurate. Worth a one-line comment fix in a future pass; not a correctness issue since the mutated object is a fresh per-request deserialization, never shared or frozen, so the in-place `Object.assign` is safe either way.
- Not exhaustive by design (Stripe metadata, TikTok/Amazon/Walmart channel-specific fields beyond `NormalizedOrder`) — matches the review norm of not blocking on theoretical, unconfirmed write paths. Author's report names this gap explicitly.
