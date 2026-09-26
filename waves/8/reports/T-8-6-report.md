# T-8-6 report: NUL-safe text at the API input boundary (OI-5)

**Status:** done.
**Commit:** invai-backend `aa13ec0` (not pushed).

## What changed
| File | Change |
|---|---|
| `src/lib/text-safety.ts` (new) | `sanitizeText`/`sanitizeDeep`, moved out of `src/ai/gateway.ts` so the oRPC boundary and the order-import pipeline share one definition of "unstorable" (C0 controls except tab/LF/CR, DEL, lone UTF-16 surrogates → U+FFFD) instead of each growing its own regex. |
| `src/ai/gateway.ts` | Drops the local regex/functions; re-exports `sanitizeText`/`sanitizeDeep` from `../lib/text-safety` so every existing `from "./gateway"` import (`ai.test.ts`, `modules/ai/service.ts`) keeps working unchanged. Still applies them to AI vars and assistant input/output (defense in depth, per OI-5/AC4). |
| `src/api/orpc.ts` | New `sanitizeInput` middleware, attached first on `pub` (`os.use(sanitizeInput).use(guard)`), so every procedure's input is sanitized before the permission guard and every handler. |
| `src/modules/orders/import.ts` | `importNormalizedOrders` now does `const n = sanitizeDeep(parsed.data)` right after schema validation, before the first insert/update of the order's text. |
| `src/integrations/carriers/tracking.ts` | `normalizeEasypostTracker` sanitizes `statusDetail` before it's written to `shipments.statusDetail`. |
| `src/api/orpc.test.ts` (new), `src/modules/orders/import.test.ts`, `src/modules/channels/shopify.test.ts` | One NUL-byte regression test each (see below). |

## Decision: middleware in `orpc.ts`, not a contracts schema helper (AC1)
Every procedure's `.input()` across `@invai/contracts` is `z.object(...)` or a `z.union` of them — confirmed by grepping every `.input(` call in `contract/*.ts`; there is no bare-string or bare-array top-level input anywhere. That means the *validated* input a middleware sees is always a plain object. One middleware, attached once on `pub`, can therefore sanitize every procedure's input in place — far smaller than wrapping every `z.string()` call across `contracts/src/schemas/*.ts` in a `SanitizedString` helper (dozens of call sites, same outcome).

oRPC's `next()` only lets a middleware replace `context`, not `input` (checked in `@orpc/server`'s `MiddlewareNextFn` type and its `executeProcedureInternal` runtime: the same `currentInput` reference flows through every middleware and into the handler). So `sanitizeInput` doesn't try to swap the top-level object; it mutates the validated input's own enumerable properties via `Object.assign(input, sanitizeDeep(input))`. `sanitizeDeep` already builds the sanitized tree immutably; `Object.assign` just copies its top-level keys onto the object every downstream middleware and the handler already hold a reference to.

## Other text sources (AC2)
`importNormalizedOrders` (`src/modules/orders/import.ts`) is the one pipeline CSV import, the API poller and webhooks all call into (confirmed: `modules/channels/sync.ts` calls it from the CSV run, the poll loop, and the webhook handler). Sanitizing there once, right after `NormalizedOrderSchema.safeParse`, covers all three non-oRPC text sources without touching each adapter. The EasyPost carrier webhook (`tracking.ts`) is a separate write path (`shipments.statusDetail`) and got its own one-line fix.

Stripe billing webhooks and the Etsy webhook's own payload (it only carries a receipt id — the order fields come from `fetchOrder`, which flows through `importNormalizedOrders`) don't write free-form caller text to text/jsonb columns, so they weren't touched.

## Tests (AC3)
- `src/api/orpc.test.ts`: calls `ai.listings.create` through the real router (`call()` from `@orpc/server`, contract validation + `orpc.ts` middlewares, no HTTP layer needed) with `brief: "warm tone\u0000 for gift buyers"`. Asserts the draft is created and `listing_drafts.brief` is stored with the NUL stripped.
- `src/modules/orders/import.test.ts`: a CSV-parsed `NormalizedOrder` with `buyerNote` containing a NUL, through `importNormalizedOrders(..., { source: "csv" })`. Asserts the import succeeds and `orders.buyerNote` is clean.
- `src/modules/channels/shopify.test.ts`: a live, signed Shopify order webhook (`orders/create`) with `note: "Gift wrap please\u0000!!"`, through the real webhook path (signature check, adapter parse, `importNormalizedOrders`). Asserts it's handled and `orders.buyerNote` is clean.

**Proved these catch the regression, not just pass by construction:** created an isolated `git worktree` at the pre-fix commit (`6bfd318`, current `main` at the time — no revert or `git stash` in the shared tree), copied only the three new test files into it (none of the fix files), and ran them against a throwaway DB/Redis slot. All three failed there with Postgres `22021: invalid byte sequence for encoding "UTF8": 0x00` — `ai.listings.create` on `listing_drafts`, the CSV row on `orders`, the webhook on `orders`. Worktree and its DB were removed after.

## Verification
- `pnpm typecheck` and `pnpm lint`: clean.
- Full `vitest run` on `invai_test_t86`, `REDIS_URL` `/6`: **80 files, 602 tests passed** (108 s), including the 3 new tests.
- Test DB dropped at the end (drop was issued; see gap below).

## Concurrency note
While this was in flight, another agent landed uncommitted rate-limit work (T-12-3) in the same `src/api/orpc.ts`, interleaved with my `sanitizeInput` middleware in the shared working tree. Staged only my hunk via a hand-built blob (`git hash-object` + `git update-index --cacheinfo`, verified with `git diff --cached` showing exactly my lines and `git diff` still showing their untouched work) rather than `git add -p`, since both edits touched the same `pub = os.use(...)` line. The other 6 files I touched had no interference and were staged normally.

## Known gaps / cross-card notes
- `dropdb`/`psql` against `invai_test_t86` hung past the tool timeout during cleanup (likely load from other agents hitting the same Postgres container); the drop command was issued and moved to background. Worth the tech lead double-checking `invai_test_t86` is gone before the gate, or dropping it if not.
- Not exhaustive: didn't chase every carrier/webhook text field (e.g. Stripe metadata), only the ones with a confirmed direct write of free-form caller text to a text/jsonb column, matching the review's "don't block on theoretical cases" norm.
