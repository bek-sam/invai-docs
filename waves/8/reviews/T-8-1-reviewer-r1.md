# Review of T-8-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: ai-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show --stat 49f229a` | 1 file, `src/schemas/ai.ts`, additive enum change only |
| `git -C invai-backend show --stat bb075e8` | 4 files: `src/ai/ai.test.ts`, `src/ai/validators/listing.ts`, `src/modules/ai/service.test.ts`, `src/modules/ai/service.ts` — all within owned paths |
| `git -C invai-web show --stat 5c6ab28` | 3 files: `src/i18n/en.ts`, `src/i18n/es.ts`, `src/routes/_app/settings/company.tsx` — the granted web-settings hunk |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend e0937cd` (parent of bb075e8) | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-contracts 4f4efcd` | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web 74fa8b4` | no hits |
| `invai-contracts`: `pnpm typecheck && pnpm lint && pnpm test` | clean; 4 test files, 31 passed |
| `invai-backend`: `pnpm typecheck && pnpm lint` | clean |
| `invai-backend`: focused `pnpm test -- src/ai/ai.test.ts src/modules/ai/service.test.ts src/modules/channels/listings.test.ts` (own DB `invai_test_t81r`, Redis `/1`) | 584/591 passed — the 7 failures are all in `shopify.test.ts`/`webhooks.test.ts` (see Shopify OAuth investigation below); everything in `src/ai`/`src/modules/ai` passed |
| `invai-backend`: full `pnpm test` x2 more (same DB/Redis) | 595/595, then 595/595 — both fully clean |
| `invai-backend`: `node_modules/.bin/vitest run src/modules/channels/shopify.test.ts src/modules/channels/webhooks.test.ts` x3 in isolation | 23/23 all three times |
| `invai-backend`: `pnpm run --if-present evals` | 51/51 plumbing across `listing_copy`, `trademark_judge`, `assistant` (personalization_check still skipped, B-101) |
| `invai-web`: `pnpm typecheck && pnpm lint && pnpm test && pnpm build` | all clean; 76/76 tests; build succeeds with the same pre-existing >500kB chunk warning |
| New-test-fails-on-base-code: archived parent commit `e0937cd`, dropped in the new `src/ai/ai.test.ts`, ran `vitest run src/ai/ai.test.ts` | both new AC2/AC3 cases FAIL on base code (`production_partner_required` / `title_all_caps` absent) — real coverage |
| `grep -rniE "buyer.*email\|buyerEmail" src/ai src/modules/ai` and `grep -rniE "sendMail\|sendEmail\|mailer" src/ai src/modules/ai` | both empty |
| Live fetch `https://www.etsy.com/legal/creativity` | 403, confirming the author couldn't fetch it live either |
| Live fetch `http://web.archive.org/web/20260828105429/https://www.etsy.com/legal/creativity` | 200; matches the exact snapshot cited in code comments; wording quoted below |

## Etsy policy wording check
Fetched the cited Wayback snapshot myself (`archive.org/wayback/available` confirms it's genuinely the closest snapshot to today). Exact text on the page:
- AI disclosure: "Sellers must disclose within their listing description if an item is created with the use of AI." — matches `AI_DISCLOSURE`'s citation and framing (the *design*, seller-prompted, never "AI-made product").
- Production partner: "Sellers must disclose that an item is made by a production partner, and provide accurate information about where the item will ship from." — `PARTNER_DISCLOSURE`'s wording covers the partner disclosure but not the ship-from-location clause; see optional note below (pre-existing, out of this card's ACs).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. AI disclosure describes the design, not "AI-made product", wording from Etsy's current policy, cited | Yes | `AI_DISCLOSURE` text verified against live Wayback snapshot above; en/es both present; `withDisclosures` unchanged in scope of trigger logic (author's own noted gap, pre-existing, out of scope) |
| 2. `production_partner_ids` in export, `production_partner_required` gate | Yes | `service.ts` diff: `ExportRow.etsyPartnerId`, `exportCsv` Etsy branch adds `production_partner_ids`; validator adds the error on `productionPartner === null`; `service.test.ts` new tests assert both the blank and the populated case round-trip through the CSV |
| 3. Title rules: 140 max, all-caps threshold zero beyond acronyms, 3-word repeat ban, en/es, one issue per rule | Yes | `title_max_140` unchanged (pre-existing, correct); `title_all_caps`/`title_repeated_phrase` added, Etsy-only, each its own `rule`; verified with base-code test-fail proof above; `ai.test.ts` new case checks a clean short-acronym title passes |
| 4. Trademark notice on flagged listings | N/A here | Card lists it, but wave.md's file ownership gives `trademark.ts`/gate checks/UI to T-8-4 (batch 2, after this card). Confirmed no "notice" code added in this diff; nothing regresses it |
| 5. No buyer email | Yes | grep for `buyer.*email`/`buyerEmail`/`sendMail`/`sendEmail`/`mailer` across `src/ai/**` and `src/modules/ai/**`: empty both ways |
| 6. Validator tests per rule + existing evals pass | Yes | New cases for production-partner-required, all-caps, repeated-phrase, clean acronym title, plus a missing-`productionPartner` draft case; evals 51/51 plumbing, unaffected |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — contracts: `src/schemas/ai.ts`; backend: `src/ai/validators/listing.ts`, `exportCsv`/`ExportRow`/`variantRowsForDraft` in `src/modules/ai/service.ts`, their test files; web: the granted settings hunk. `src/modules/tenancy/service.ts`'s `updateOrg` (listed on the card) was already done by the architect in `e958638`, not touched again here — correctly flagged in the report.
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — scan script clean in all three repos; new tests fail on base code (see above)
- [x] Tenancy / idempotency / money in cents / en+es — n/a for tenancy/idempotency here (no new tables, no side effects); en/es present on every new validator message and every new web string
- [x] Decisions recorded where needed — the report's "Decisions" section covers the bilingual-inline-string call and the all-caps-threshold-zero judgment call; both reasonable and documented

## Shopify OAuth-state investigation (7 failures)
File: `src/modules/channels/webhooks.test.ts`, `describe("Shopify OAuth state")` (the three tests: "expires after 10 minutes", "can be used only once, even by two callbacks racing", "a failed completion burns the state too"), plus a related failure inside `src/modules/channels/shopify.test.ts`'s `install()` helper (`describe("Shopify webhook subscriptions and disconnect")`, line ~155/210) which also calls `completeShopifyOAuth`.

- `git log` on `src/modules/channels/sync.ts`, `shopify.test.ts`, `webhooks.test.ts` shows no wave-8 commit touches any of them — confirms these tests are untouched by T-8-1 (or any other wave-8 card).
- Isolating the two files (`vitest run src/modules/channels/shopify.test.ts src/modules/channels/webhooks.test.ts`), run 3x back to back: 23/23 passed every time.
- Full `pnpm test`, run 3 times total on my own DB/Redis (`invai_test_t81r`, `/1`): the first run showed the same 7 failures the author saw; the next two runs were 595/595 clean.
- The failing run coincided with another agent's full `vitest run` (`invai-backend-review-t82-r2`) executing concurrently against the same shared Postgres/Valkey container; once that finished, my repeated full runs came back clean.
- Conclusion: **flaky, not real.** The failures are a resource-contention/timing race that only surfaces when multiple full-suite runs hit the shared Postgres/Valkey at once (plausible given `completeShopifyOAuth`'s wall-clock TTL check and the deliberate two-callback race in "can be used only once"), not a defect in T-8-1's diff. Matches the author's own finding (stashed diff, isolated files, still failed → confirmed pre-existing) and adds the missing piece: it's load-triggered, not deterministic. Non-blocking for this card. Worth a backlog item (parallel to the B-17/B-18 note already on T-8-2 for shared-infra alerting) to either give full-suite runs more DB/Redis headroom or make the OAuth-state test's timing assertions load-tolerant — flagging to the tech lead, not a fix for this card.

## Optional notes (not blocking)
- `PARTNER_DISCLOSURE` still doesn't include the "where the item will ship from" clause Etsy's policy also asks for, and is still applied unconditionally regardless of `printsInHouse` (rules.md's M-23 issue). Pre-existing (same gap in the string it replaced) and outside this card's ACs — flagged for a follow-up card, not this one.
- `AI_DISCLOSURE` is still unconditional per the author's own note (every Etsy listing gets it, even a fully hand-made design) — an over-disclosure risk rather than under-disclosure, pre-existing and out of scope, already logged in the report.
- The bilingual `"${en} / ${es}"` inline convention is a reasonable stopgap given `ValidationIssue.message` is a raw `z.string()` with no locale threading today, but it means both languages always show together rather than switching by locale like the rest of the app. Worth a contracts-level fix eventually (`{en, es}` field) — not blocking here.
