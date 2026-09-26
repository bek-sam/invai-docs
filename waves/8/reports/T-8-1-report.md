# T-8-1 report: Etsy listing rules (B-14)

**Status:** done, ready for review (compliance-officer co-review: marketplace-policy, ai).
**Commits:** contracts `49f229a`, backend `bb075e8`, web `5c6ab28` (none pushed).

## What changed

**`invai-contracts/src/schemas/ai.ts`**
- `AssistantEvent`'s error code gained `"spend_cap"` (was `credits_exhausted | rate_limited |
  refusal | internal`), per wave.md's note that T-8-1 should give the assistant a proper code for
  `AI_SPEND_CAP_REACHED` instead of `internal`.

**`invai-backend/src/ai/validators/listing.ts`**
- **AI disclosure (AC1):** `AI_DISCLOSURE` reworded to Etsy's current Creativity Standards
  wording and cited inline: *"Sellers must disclose within their listing description if an item
  is created with the use of AI."* — https://www.etsy.com/legal/creativity. `etsy.com` 403s
  automated fetches, so this was confirmed from the Wayback snapshot taken **2026-08-28**
  (`http://web.archive.org/web/20260828105429/https://www.etsy.com/legal/creativity`). The new
  wording talks about the *design* ("This design was created with the use of AI...") and is never
  framed as "AI-made product" — production (the DTF print and press) is disclosed separately by
  `PARTNER_DISCLOSURE`, also reworded to match the same page's "designed by a seller" section.
  Both constants are now `en / es` bilingual strings (agent-brief's en+es rule; the web renders
  `ValidationIssue.message` raw with no i18n lookup, so this validator embeds both languages in
  one string rather than requiring a contracts/web change).
- **`production_partner_ids` (AC2):** new error `production_partner_required` (Etsy only, field
  `productionPartner`) when `content.productionPartner === null`. Exactly per wave.md Contract
  stubs / C — `companies.settings.productionPartner` and `ListingContent.productionPartner` were
  already stubbed by the architect (`e958638`/`4f4efcd`); this card wires the validator gate.
- **Title rules (AC3):** kept the existing generic 140-char `title_max_140` (already Etsy-correct
  via `CHANNEL_RULES.etsy.listing.titleMax`), and added two Etsy-only errors:
  - `title_all_caps`: any word of 4+ letters that's fully uppercase, one error per title naming
    every offending word. Etsy has no documented numeric cap here — its own guidance just says
    ALL CAPS "looks spammy" (Seller Handbook "New Guidance for Listing Titles", Wayback snapshot
    **2025-12-02**) — so InvAI enforces that literally (zero allowed) but exempts words of 3
    letters or fewer so real acronyms/sizes (`XL`, `DTF`, `US`) never trip it.
  - `title_repeated_phrase`: any 3-word phrase (case/punctuation-insensitive) that recurs anywhere
    in the title, matching the same Seller Handbook's "Try not to repeat words" / "unnecessary
    repeated words or phrases" guidance. A longer repeat always contains a repeated 3-gram, so
    this catches every "3-or-more-word" case with one check.
  - Each is its own error (one issue per rule), bilingual message, so a test can assert on `rule`
    and count.

**`invai-backend/src/modules/ai/service.ts`**
- `generationContext`/`toContent` now fill `ListingContent.productionPartner` from
  `companies.settings.productionPartner.name` at generation time (never model-generated),
  replacing the `TODO(T-8-1)` stub.
- `exportCsv()`'s Etsy branch: dropped the hard-coded `"DTF transfer printer"` string for the real
  `content.productionPartner`, and added a `production_partner_ids` column sourced from
  `company.settings.productionPartner.etsyPartnerId` (blank until the Etsy adapter is authorized —
  no live ids yet, per wave.md). `ExportRow` gained an optional `etsyPartnerId`; `exportCsv` stays
  a pure function of its rows. `exportListingsCsv` and `publishDraft` fetch the company's
  `etsyPartnerId` once and thread it through `variantRowsForDraft`.
- `ask()`'s error mapping now yields `"spend_cap"` for an `AI_SPEND_CAP_REACHED` ORPCError instead
  of falling through to `"internal"`. (No web change needed: `assistant.tsx` renders `ev.message`,
  not `ev.code`.)

**`invai-backend/src/ai/ai.test.ts` / `src/modules/ai/service.test.ts`** (pre-existing files/blocks
I don't own outright, but had to touch — see Known gaps)
- Updated the shared `base` listing fixture and the mock-provider round-trip test to give Etsy a
  `productionPartner`, since `production_partner_required` now fires on `null`.
- New cases: production-partner-required (and that other channels never gate on it), an all-caps
  title, a repeated-3-word-phrase title, and a clean title using short acronyms/sizes.
- `service.test.ts`: the shared test company now has a production partner configured (mirrors a
  real shop's Settings); the Etsy export test asserts the new `production_partner`/
  `production_partner_ids` columns, plus a new test that sets an `etsyPartnerId` and confirms it
  round-trips through the CSV.

**`invai-web`** (web-settings hunk, granted on this card)
- `src/routes/_app/settings/company.tsx`: Company Settings > Profile gained a "Production
  partner" name field and an optional Etsy-partner-ID field (shop orgs only), wired to
  `me.updateOrg`. en/es strings added to `src/i18n/en.ts` / `src/i18n/es.ts`.

## Decisions
- **Bilingual messages inline, not a schema change.** `ValidationIssue.message` is `z.string()`
  and the web renders it as-is (`drafts.$draftId.tsx`); there's no locale on `Context`/
  `TenantContext` to thread through, and changing the contract shape or the web's rendering was
  outside this card's owned files. I embedded `"${en} / ${es}"` in the message instead of adding a
  `{en, es}` field — same approach the codebase already uses in a couple of spots (`DEMO_NAMES`).
  I only bilingual'd the title rules and `production_partner_required` (this card's ACs); the
  pre-existing description/tags/bullets/price messages are untouched and stay English-only.
- **`title_all_caps` threshold = 0 extra words, not "more than N".** Etsy's own guidance has no
  number; I read "no all-caps words beyond Etsy's limit" as "none, beyond the acronym/size
  exemption" rather than picking an arbitrary N. Flagging this as a judgment call for the
  compliance-officer review.
- **AI disclosure is still unconditional for Etsy**, regardless of whether a given design was
  actually AI-made — that trigger logic predates this card and is out of scope; I only fixed the
  wording. Worth a follow-up: today every Etsy listing gets an AI-use disclosure even for 100%
  hand-made designs, which is over-disclosure, not under.
- **AC4 (trademark notice) is T-8-4's, not touched.** My card lists it as an acceptance criterion,
  but wave.md's file ownership gives `trademark.ts`, the gate checks, and all `invai-ui`/`invai-web`
  files to T-8-4, which lands after this card. I didn't add a "notice" anywhere in my owned files;
  nothing here regresses it.

## Verification
- `pnpm typecheck` and `pnpm lint` clean in `invai-contracts`, `invai-backend`, `invai-web`.
- `invai-web`: `pnpm build` succeeds (pre-existing >500kB chunk warning, unrelated).
- Backend focused run (`invai_test_t81`, Redis `/1`): `src/ai/ai.test.ts`,
  `src/modules/ai/service.test.ts`, `src/modules/channels/listings.test.ts` — **50/50 passed**.
- Backend full `vitest run` (same DB/Redis): **583/590 passed**. The 7 failures are all in
  `src/modules/channels/shopify.test.ts` / `webhooks.test.ts` (Shopify OAuth-state races and
  connection-link-expiry assertions) — confirmed pre-existing by stashing my diff and re-running
  just those two files: identical 5 failures with none of my changes applied. Nothing in `src/ai`
  or `src/modules/ai` touches Shopify OAuth.
- **No buyer email (AC5):** `grep -rniE "buyer.*email|buyerEmail"` and a search for
  `sendMail|sendEmail|mailer` across `src/ai/**` and `src/modules/ai/**` both return nothing.
- Dropped `invai_test_t81` after the runs; no processes left running.

## Known gaps and cross-card notes
- **Touched two shared test files I don't exclusively own** (`src/ai/ai.test.ts`'s pre-existing
  "channel validators"/"mock provider" blocks, and `src/modules/ai/service.test.ts`'s "ai module"
  describe) because my validator change would otherwise break their existing assertions
  (`production_partner_required` firing on the shared `null`-partner fixtures). I did not touch
  T-8-2's or T-8-3's own `describe` blocks in `ai.test.ts`.
- **T-8-4 lands next** (batch 2, sequenced after this card) and will re-touch `service.ts`'s
  `approveDraft`/`publishDraft`/`exportListingsCsv`/`trademarkCheck` for the trademark gate — my
  diff there is limited to the `exportCsv`/`variantRowsForDraft`/`etsyPartnerId` threading, so it
  shouldn't conflict, but flagging the shared surface.
- **Web settings field is new UI, not in this card's original file list** — used the grant
  explicitly given in this task's brief ("the web settings hunk is granted (en/es)") because
  without it `companies.settings.productionPartner` had no way to be set outside a raw DB write,
  which would make `production_partner_required` unreachable-fixable for a real shop.
