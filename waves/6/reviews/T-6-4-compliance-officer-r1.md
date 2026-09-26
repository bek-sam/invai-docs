# Review of T-6-4 (round 1) — compliance-officer co-review

- Reviewer: compliance-officer on Sonnet 5
- Author: ai-engineer (backend `0e2822e`) + web-engineer (web `4817a72`) on Opus
- Verdict: **changes-required**

Scope per `listing-compliance-check`: the Etsy/Shopify CSV format and the AI disclosure. Evidence
run (`tsc`/`biome`/`build`/`vitest`) is shared with `T-6-4-reviewer-r1.md`, not re-run here.

## Checks (per [rules.md](../../../../.claude/skills/listing-compliance-check/rules.md))

| Check | Channel | Result | Evidence | Rule source | Fix owner |
|---|---|---|---|---|---|
| AI disclosure present in description | Etsy, Shopify, all | pass | `exportCsv`'s `description()` helper still joins `c.disclosures` into the CSV description column (`service.ts:670`); `finalizeDisclosures` in `src/ai/validators/listing.ts` (untouched by this diff) still appends `AI_DISCLOSURE`. Unchanged behavior, verified by diff — no file in the disclosure path was touched. | Etsy Creativity Standards; rules.md | — |
| Real SKU per variant, no placeholder | Etsy, Shopify | pass | `variantRowsForDraft` throws `badRequest` if no product/variant resolves; new tests fail on pre-card code (`DRAFT-${id.slice(0,8)}` path removed). Confirmed by running the new tests against `git archive 3feb9ff` — all 5 fail as expected. | card AC2 | — |
| Etsy CSV columns usable as a bulk upload | Etsy | pass, with a pre-existing caveat | Columns present: `title, description, price, quantity, sku, tags, materials, who_made, is_made_to_order, when_made, production_partner` — unchanged from before this card except now real per-variant. | research 10 §3 | — |
| Etsy production-partner field | Etsy | **fail (pre-existing, unchanged)** | `production_partner: "DTF transfer printer"` is a fixed string in every Etsy row (`service.ts:685`), same text present before this card (`git show 3feb9ff:...` has the identical line). Etsy requires the structured `production_partner_ids` field from `getShopProductionPartners`, not description/CSV text, and this text is actively wrong for a shop that prints in-house (M-23, already logged in rules.md). Not a regression from this card — AC2 only asked for real SKUs and the Shopify branch — but it's still shipping today and this is the compliance checkpoint for it. | rules.md M-23; research 10 §3 | ai-engineer, tracked separately from this card |
| **Shopify CSV columns usable as a bulk upload** | Shopify | **fail — new work, not usable** | The new Shopify branch (`service.ts:708-746`) never sets a real `Option1 Value` (or a second option for the other axis) on any row — it's hardcoded `""` on the handle's first row and omitted (defaults to `""`) on every continuation row. `variantRowsForDraft` (`service.ts:784-814`) even selects `colorCode`/`sizeCode` from `blankVariants` and then throws them away, returning only `sku`. Shopify's product importer needs the option value(s) to tell variants under one `Handle` apart; with every row sharing a blank option value, uploading this file to Shopify will not produce 36 distinct SKU'd variants — it will either error on duplicate combinations or collapse to one variant. This is the same finding as `T-6-4-reviewer-r1.md`'s blocking finding #1, from the compliance-format angle: **the columns do not match Shopify's current upload format well enough to function**, so this AC is not actually done despite passing tests (no test checks `Option1 Value`). | Shopify product CSV import spec | ai-engineer |
| Trademark check gating publish | all | not touched by this card | `combineRisk`/`trademark.ts` untouched by this diff; out of scope here. | rules.md | — |
| Human approval before publish | all | pass, unchanged | `publishDraft` still requires an `approved` draft and a connection before producing any CSV/publish attempt; dead API-publish branch removal doesn't change the approval gate. | rules.md; Amazon Agent Policy | — |
| No marketplace data used to train/tune | n/a | pass, unchanged | Nothing in this diff touches training/eval data paths. | R15 | — |

## Verdict rationale
Two findings, one new and blocking, one pre-existing and non-blocking for this card specifically
but worth re-flagging:
1. **Blocking:** the Shopify CSV branch (this card's own new work) doesn't carry real option
   values, so it fails the compliance bar of "columns match the current marketplace upload
   format" in a way that would produce a broken or silently-lossy upload for a real shop. Fix
   owner: ai-engineer (thread `colorCode`/`sizeCode` through to `Option1 Value`/`Option2 Value`).
2. **Not blocking this card, but re-logged:** Etsy's `production_partner` text field (M-23) is
   still wrong for in-house-printing shops. This was true before `0e2822e` and AC2 didn't ask for
   it to be fixed; leaving it open here rather than blocking on it, per the card's own scope, but
   it should get its own card since it's a live compliance gap on every Etsy export today.

## Rules re-checked against source (>60 days old per skill step 1)
`rules.md` is dated 2026-09-24 (1 day old at time of review) — no re-check against source needed
this round.
