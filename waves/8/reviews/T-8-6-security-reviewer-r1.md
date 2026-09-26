# Review of T-8-6 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: (architect/backend-foundation) on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `perl -e 'alarm 120; exec @ARGV' pnpm typecheck` (invai-backend) | clean |
| `perl -e 'alarm 120; exec @ARGV' pnpm lint` (invai-backend) | clean (biome, 290 files) |
| `pnpm vitest run src/api/orpc.test.ts src/modules/orders/import.test.ts src/modules/channels/shopify.test.ts` | 3 files, 24 tests passed |
| `git show aa13ec0` (full diff, all 8 files) | reviewed line by line |
| `git show aa13ec0 -- src/modules/orders/import.test.ts src/modules/channels/shopify.test.ts` | reviewed new test bodies |
| grep for other callers of `importNormalizedOrders` and other free-text carrier fields | only `sync.ts` (CSV/poll/webhook) and tests call it; `trackingCode`/`carrierShipmentId` are carrier-issued identifiers, not free-form caller text |

## Security focus areas (per OI-5 / card)

**1. Is the in-place mutation safe (no shared/frozen objects), and where does it run relative to validation and the guard?**
Two different mutation styles, both safe:
- `orpc.ts`'s `sanitizeInput`: `Object.assign(input, sanitizeDeep(input))`. Only the *top-level* object is mutated; every nested value is a brand-new tree from `sanitizeDeep` (pure — verified: it builds `map`/`Object.fromEntries` output, never writes into its argument). Traced oRPC's actual execution order in `node_modules/@orpc/server` (`Builder.input()` sets `inputValidationIndex` relative to the *contract* builder's middleware count, which is 0 before any `.use()`; `enhanceRouter` — what `implement(contract)` + `pub`'s `.use()` chain goes through — adds the impl's middleware count on top of that). Net order: `sanitizeInput` → `guard` → Zod validation → handler. So the object being mutated is the raw per-request JSON body, freshly deserialized by the transport layer for this request only — never a shared singleton, never `Object.freeze`d, and there is no other outstanding reference to it that expects unsanitized values. Running before `guard` (permission checks) and before validation means an attacker can't use a NUL byte to slip past sanitization into any check or handler.
- `import.ts`: `const n = sanitizeDeep(parsed.data)` — doesn't mutate `parsed.data` at all, just rebinds `n` to a new sanitized tree. No mutation-safety question here at all.
- `tracking.ts`: `sanitizeText(t.status_detail)` on a local field, same — no mutation of shared state.

**2. Is legitimate Unicode left alone?**
`UNSTORABLE = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g` strips only C0 controls (excluding tab/LF/CR) and DEL. `LONE_SURROGATE` only matches a high surrogate not followed by its low partner, or a low surrogate not preceded by its high partner — legitimately paired surrogates (emoji, supplementary-plane CJK, etc.) are untouched by construction (negative lookahead/lookbehind on the pair). Accented Latin, CJK, RTL scripts, combining marks, ZWJ sequences: none touched. Confirmed via the regex definitions in `src/lib/text-safety.ts`; no test explicitly round-trips an emoji/CJK string, but the regex is unchanged from T-8-2's gateway version, which has been running in production paths since then without reported false-positive stripping.

**3. Is every ingestion path covered — CSV, poll, webhooks, EasyPost?**
- CSV, API poll, and (Shopify/Etsy-style) webhooks: all funnel through `importNormalizedOrders`, confirmed the only production caller is `sync.ts`, which the report states calls it from the CSV run, the poll loop, and the webhook handler.
- EasyPost: `normalizeEasypostTracker` sanitizes `statusDetail` before it reaches `shipments.statusDetail`. This is the field the card names.
- oRPC-originated text (dashboard/API-key callers): `sanitizeInput` middleware, every procedure built on `pub`/`authed`.
- Not covered, by explicit scoping in the report: Stripe billing webhook metadata, and channel-specific fields outside `NormalizedOrder`/`EpTracker` that were not confirmed to write free-form caller text to a text/jsonb column. This is a reasonable, stated boundary (matches "don't block on theoretical cases"), not a silent gap.

**4. Double-sanitizing bugs?**
`sanitizeText`/`sanitizeDeep` are idempotent: stripped characters are gone, and a lone surrogate becomes U+FFFD, which itself doesn't match `LONE_SURROGATE` on a second pass. A value that passes through both `sanitizeInput` (if a CSV/webhook payload also happens to arrive via an oRPC-input string field somewhere) and `importNormalizedOrders`'s `sanitizeDeep` would be sanitized twice with no different outcome than once. No evidence of a case where the two sanitizers disagree on what's "safe" — they share the exact same functions from `text-safety.ts`, not independent copies.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | see focus area 1 and 3 above |
| 2 | yes | see focus area 3 |
| 3 | yes | ran `orpc.test.ts`, `import.test.ts` (new case), `shopify.test.ts` (new case) — all pass, all assert the DB column is clean |
| 4 | yes | `ai/gateway.ts` still calls into the shared functions for AI vars and assistant input/output |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior through real paths (real router call, real signed webhook delivery, real import pipeline), not mocks of the sanitizer itself
- [x] Tenancy / idempotency / money / en-es — n/a to this change
- [x] Decisions recorded — OI-5

## Optional notes (not blocking)
- Same note as the primary reviewer: `orpc.ts`'s comment says the middleware sees "the validated input" — traced execution order says sanitization actually runs before Zod validation, which is the safer order (bad bytes never reach a validator or the handler) but the comment is technically backwards. Cosmetic; doesn't change the security conclusion.
- No test explicitly proves legitimate Unicode (emoji, CJK, RTL) survives `sanitizeText` unchanged; the regex construction makes this a low-risk gap (unchanged from the already-shipped T-8-2 gateway sanitizer), but a future round could add one assertion of this to close the theoretical gap.
