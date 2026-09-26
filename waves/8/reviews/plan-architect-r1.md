# Wave 8 plan review — architect, round 1

Verdict: **approve, with the file-ownership split and contract stubs added to `wave.md` and the cards**

## Read-only findings (`src/ai/**`, `src/modules/ai/**`)
- `src/ai/gateway.ts` is the one choke point every AI call passes through (`runStructured`, `runAssistant`) — right place for the spend-breaker check (T-8-2), before `provider.structured`/`provider.assistant`.
- `src/ai/models.ts` already centralizes model ids and `tokensToCostCents`/`tokensToCredits` (0007's "one config file" rule); T-8-3 extends it to a real price table instead of adding a second one.
- `src/modules/ai/trademark.ts`'s `combineRisk` already implements the 60/25 score bands T-8-4's card wants — the gap is enforcement (currently only a soft check in `approveDraft` with an `acknowledgeRisk` bypass) and the missing review record, not the scoring math.
- `src/modules/ai/service.ts` (1,212 lines) is the real risk: it's the only file five different concerns (drafts CRUD, generation, approve/reject, publish, CSV export, trademark check, assistant, credits) all live in, and it's the one file two cards (T-8-1, T-8-4) both need to touch.
- No breaker, no production-partner setting, no review-record columns exist yet anywhere in the codebase — all three are new, not extensions of something partial.

## File-ownership split
Three cards (T-8-2, T-8-3, T-8-5) touch entirely disjoint files (`gateway.ts`+`prompts/`+`assistant-tools.ts` / `models.ts`+`mock.ts`+`credits.ts` / a brand-new `evals/` tree) — these run as the "3 builders at once" batch with zero grants needed, aside from splitting `ai.test.ts` by `describe` block.

T-8-1 and T-8-4 both land in `service.ts`, but in disjoint functions (`exportCsv()` vs. `approveDraft`/`publishDraft`/`exportListingsCsv`/`trademarkCheck`). They aren't split into a second parallel batch, though, because T-8-4's gate must re-check `ListingContent`/`ExportRow` shapes that T-8-1 is changing (adding `productionPartner`) — a real ordering dependency, not just a textual-conflict risk. Sequenced: T-8-1 then T-8-4. T-8-1 also reaches outside `src/ai`/`modules/ai` into `src/modules/tenancy/service.ts` and `@invai/contracts` for the settings field; called that out on the card since it's a cross-module/contract change (change order: contracts → backend).

## Contract stubs (exact, in `wave.md`)
- **Review record (T-8-4):** three nullable columns on `listing_drafts`, a `trademarkReview` shape in contracts, a `recordTrademarkReview` procedure with a required note, and enforcement that always re-reads the *current* trademark field rather than an approval-time snapshot — closes the bypass gap product flagged.
- **Breaker error codes (T-8-2):** one ORPC code `AI_SPEND_CAP_REACHED` (429) with `data.scope` distinguishing platform vs. tenant, Valkey key layout and TTL, and reuse of the existing `alerts`/`ALERT_KINDS` contract (two new kinds) instead of inventing a new alert path.
- **Production-partner setting (T-8-1):** follows the existing `printsInHouse` settings-jsonb pattern exactly, so `updateOrg` and its test (`org-settings.test.ts`) are the template rather than a new mechanism.

## Eval harness and CI
Location is correct as specified (`invai-backend/evals/run.ts`). CI mode: verified `.github/workflows/ci.yml` carries no `ANTHROPIC_API_KEY`, so the harness's mock-mode path needs no new environment wiring in CI — just the `scripts.evals` entry and one step after `test`.

No DB or code changes were made in this review; the review record's migration and the breaker's config are left for the T-8-4/T-8-2 builders to generate. Approved.
