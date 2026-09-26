# Wave 8 plan review — product-manager, round 1

Verdict: **approve, with edits applied to the cards**

## Scope check (`product/scope.md`)
- MVP item 10 ("AI listing drafts with validators, human approval and disclosure") and item 11 ("Trademark risk check") cover all five cards. No net-new scope; this wave hardens existing AI infra (0007) and closes marketplace-compliance gaps (Etsy AI disclosure, `production_partner_ids`, trademark gate). Nothing here needs a `scope-change-request`.
- "AI design generation" and direct marketplace APIs stay out of scope; none of the five cards touch either.

## Acceptance-criteria testability
- T-8-1 AC3 ("no repeated phrases") was not measurable — tightened to "no 3+-word phrase repeated verbatim, case-insensitive" so a test can assert on it directly. AC2 now points at the exact settings/contract shape (below) instead of "new field if needed".
- T-8-2, T-8-3 ACs were already testable; T-8-2 AC3 now cites the exact error code/scope so a breaker test has something concrete to assert.
- T-8-4 AC1/AC2 had a latent contradiction: the current code lets `acknowledgeRisk` bypass a high-risk score at `approveDraft`, but the card wants `>=60` to block publish/export unconditionally. Resolved: the bypass is removed, and the gate re-checks the draft's *current* `trademark` field at every call (approve, publish, export), not a value cached at approval time. Card AC1/AC4 updated accordingly.
- T-8-5 ACs were already testable once "CI mode" is pinned down (see below).

## Production-partner setting (T-8-1)
No POD-shop setting existed. Designed exactly in `wave.md`: `companies.settings.productionPartner: { name, etsyPartnerId | null }`, threaded through `ListingContent.productionPartner` and the Etsy CSV export, with a new validator error when it's missing. This is a real gap the acceptance criteria would otherwise have shipped without — Etsy requires the structured field, not prose.

## Eval harness and CI mode
Confirmed: `invai-backend/evals/` + `evals/run.ts` is exactly where T-8-5's own card puts it — no relocation needed. CI mode is **mock automatically**: `.github/workflows/ci.yml` sets no `ANTHROPIC_API_KEY`, so `env.mocks.ai` is already `true` there (same mechanism every other AI route uses). T-8-5 needs to add the `evals` script and a CI step, not new mock plumbing — added to the card.

## Sequencing risk called out to the architect
T-8-1 and T-8-4 both edit `src/modules/ai/service.ts`. I flagged this; the architect's split (batch by function, T-8-1 lands first) is the right call rather than trying to run all 5 cards in one 3-lane batch — the wave.md line "Run 3 builders at once" was underspecified about *which* three, and now says so per batch.

No scope, pricing or segment concerns. Approved.
