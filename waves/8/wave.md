# Wave 8: AI and marketplace compliance

- Goal: AI listings are safe to publish on Etsy, Amazon and TikTok. Untrusted text can't steer the model, AI spend can't run away, and every AI route is measured.
- Rules: `team/agent-brief.md` (decision 0011).

## Cards
| Card | Owner | Co-reviewers | Flags | Model |
|---|---|---|---|---|
| T-8-1 Etsy listing rules (B-14) | ai-engineer | compliance-officer | marketplace-policy, ai | sonnet |
| T-8-2 Prompt isolation and global AI spend breaker (B-15) | ai-engineer | security-reviewer | ai, payments | opus |
| T-8-3 AI cost table and mock hardening (B-45) | ai-engineer | data-analyst | ai | sonnet |
| T-8-4 Trademark-risk gate (B-46) | ai-engineer + web-engineer | compliance-officer, product-designer | marketplace-policy, ui | sonnet |
| T-8-5 Eval harness (B-48) | ai-engineer | qa-engineer | ai | sonnet |

All five cards are in `src/ai/**` and `modules/ai/**`, so the plan review must split the file ownership. See "File ownership and batches" below; run 3 builders at once per batch.

## File ownership and batches

**Batch 1 — 3 builders in parallel, zero shared files:**
| Card | Owns |
|---|---|
| T-8-2 | `src/ai/gateway.ts`, `src/ai/breaker.ts` (new), `src/ai/prompts/index.ts`, `src/modules/ai/assistant-tools.ts`, its cases in `src/ai/ai.test.ts` |
| T-8-3 | `src/ai/models.ts`, `src/ai/providers/mock.ts`, `src/ai/credits.ts` (test-only), its cases in `src/ai/ai.test.ts` |
| T-8-5 | new `invai-backend/evals/**`, the `scripts.evals` line in `package.json`, the new step in `.github/workflows/ci.yml` |

`ai.test.ts` is shared by T-8-2 and T-8-3: each adds its own `describe` block: don't touch the other's.

**Batch 2 — after batch 1 lands, T-8-1 then T-8-4 (sequenced, not split):**
Both touch `src/modules/ai/service.ts` and the `ExportRow`/`ListingContent` shape T-8-4's gate re-checks at publish/export time, so T-8-1 must land first.
| Card | Owns |
|---|---|
| T-8-1 | `src/ai/validators/listing.ts`, the `exportCsv()` function (Etsy branch) in `src/modules/ai/service.ts`, the `ExportRow`/`ListingContent.productionPartner` type, `src/modules/tenancy/service.ts`'s `updateOrg` (new settings field) — flag the tenancy-module and contracts touch to the architect, it's outside `src/ai`/`modules/ai` |
| T-8-4 | `src/modules/ai/trademark.ts`, the gate checks inside `approveDraft`, `publishDraft`, `exportListingsCsv`, `trademarkCheck` in `src/modules/ai/service.ts`, plus its `invai-ui`/`invai-web` files (outside this repo's split) |

T-8-4 must re-check the draft's **current** `trademark` field at publish/export time, not the value cached when it was approved.

## Contract stubs

### A. Trademark review record (T-8-4)
- New nullable columns on `listing_drafts` (T-8-4 generates the migration; not created by this review): `trademark_reviewed_by uuid references users(id)`, `trademark_reviewed_at timestamptz`, `trademark_review_note text`.
- `@invai/contracts` `ListingDraft` gains `trademarkReview: { reviewedBy: string; reviewedAt: string; note: string } | null`.
- New procedure `ai.listings.recordTrademarkReview({ id, note })`: 409 unless `trademark.riskLevel === "medium"`; `note` required (min 3 chars); sets `trademarkReviewedBy = ctx.userId`, `trademarkReviewedAt = now()`, `trademarkReviewNote = note`; audit-logs `listing_draft.trademark_review` with `{riskScore, note}`.
- Enforcement (re-checked live, every call, in `approveDraft`, `publishDraft`, `exportListingsCsv`):
  - `riskScore >= 60`: always throws `ORPCError("HIGH_TRADEMARK_RISK", { status: 409 })`. No `acknowledgeRisk` override anywhere — drop the current bypass in `approveDraft`.
  - `25 <= riskScore < 60` and `trademarkReview` is null: throws `ORPCError("TRADEMARK_REVIEW_REQUIRED", { status: 409, data: { riskScore } })`.
  - `riskScore < 25`: no gate.

### B. Spend-breaker error codes and counters (T-8-2)
- Valkey (the existing `redis` client in `src/lib/queues.ts`), keys `ai:spend:platform:<YYYY-MM-DD>` and `ai:spend:tenant:<companyId>:<YYYY-MM-DD>`: `INCRBY` the call's `costCents` in `finishJob`, `GET`-checked before every `provider.structured`/`provider.assistant` call, `EXPIRE` 26h on first write. Sample workspaces (already forced to the mock) never touch these counters.
- Config in `src/env.ts`: `AI_DAILY_PLATFORM_CAP_CENTS`, `AI_DAILY_TENANT_CAP_CENTS`.
- One error code, both scopes: `new ORPCError("AI_SPEND_CAP_REACHED", { status: 429, message: "AI spend cap reached; try again after it resets", data: { scope: "platform" | "tenant", capCents, spentCents, resetAt } })`.
- Admin alert: add `ai_spend_cap_tenant` and `ai_spend_cap_platform` to `ALERT_KINDS` (contracts, severity `"critical"`), `emit(tx, companyId, "alert.created", ...)` once per scope per day (`SETNX` a `ai:spend:alerted:<scope>:<key>:<date>` flag to dedupe).

### C. Production-partner setting (T-8-1)
- `companies.settings` jsonb, same pattern as `printsInHouse`: `productionPartner: { name: string; etsyPartnerId: string | null } | null`. `updateOrg` accepts it; the read side maps `row.settings?.productionPartner ?? null`.
- `@invai/contracts` `ListingContent` gains `productionPartner: string | null`, filled in at generation time from the company setting — never model-generated.
- `validateListing` (Etsy only) adds error `production_partner_required` when `content.productionPartner` is null.
- `exportCsv()`'s Etsy branch: drop the hard-coded `"DTF transfer printer"` string, use `c.productionPartner`; add a `production_partner_ids` column from `company.settings.productionPartner.etsyPartnerId` (blank until the Etsy adapter is authorized — no live IDs yet).

## Eval harness and CI

- Location matches T-8-5's card exactly: `invai-backend/evals/`, entry point `evals/run.ts`, one eval set per route.
- CI mode: `.github/workflows/ci.yml` sets no `ANTHROPIC_API_KEY`, so `env.mocks.ai` is already `true` there — the harness runs in mock mode automatically, no new CI plumbing needed for that part. T-8-5 adds: a `scripts.evals` entry in `package.json` (e.g. `"evals": "tsx evals/run.ts"`), and a `pnpm run --if-present evals` step in `ci.yml` right after the existing `pnpm run --if-present test` step. A real (keyed) run only ever happens locally/manually.

## Numbers
- Test DB `invai_test_t8<k>`.
- API port `31<k>8`.
- `REDIS_URL` `/<k>`.
- **Grant (tech lead, 2026-09-26):** T-8-5 may edit `invai-backend/.github/workflows/ci.yml` (one eval step in mock mode) and the `package.json` scripts.
- **Grant (tech lead, 2026-09-26):** T-8-2 may add `AI_DAILY_PLATFORM_CAP_CENTS` and `AI_DAILY_TENANT_CAP_CENTS` to `src/env.ts` (defaults $500 and $50). T-8-1 should give the assistant a `spend_cap` error code instead of "internal".
