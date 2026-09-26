# T-8-1: Etsy listing rules (B-14)
Evidence: `research/10-marketplace-engineering-rules.md` (Etsy section, M-23 to M-26), backlog B-14.

Owned files (wave.md "File ownership and batches", batch 2, runs before T-8-4): `src/ai/validators/listing.ts`; the `exportCsv()` function (Etsy branch) in `src/modules/ai/service.ts`; the `ExportRow`/`ListingContent.productionPartner` type; `src/modules/tenancy/service.ts`'s `updateOrg`. The tenancy-module and contracts touch is outside `src/ai`/`modules/ai` — flag it to the architect.

## Acceptance criteria
1. **AI disclosure:** it describes the **design** being AI-assisted, per Etsy's Creativity Standards. It's never framed as "AI-made product", and the wording comes from Etsy's current policy (cite it).
2. **`production_partner_ids`:** required for a POD/DTF shop. Design exactly per wave.md "Contract stubs / C": `companies.settings.productionPartner`, `ListingContent.productionPartner`, and the Etsy validator's `production_partner_required` error when it's null. The export CSV includes it (name and, when set, the Etsy partner id).
3. **Title rules:** 140 characters maximum; no all-caps words beyond Etsy's limit; and no 3-or-more-word phrase repeated verbatim (case-insensitive) anywhere in the title. The validator reports each rule violation in en/es, one issue per rule so a test can assert on `rule` and count.
4. **Trademark notice:** a listing that the trademark check flags (`riskScore >= 25`) shows the notice.
5. **No buyer email:** nothing in the AI or listing flows emails Etsy buyers (grep proof).
6. **Tests:** validator tests for every rule (including a title with a repeated 3-word phrase, and a draft missing `productionPartner`), and the existing evals still pass.
