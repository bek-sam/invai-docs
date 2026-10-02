# T-26-3: AI design analysis for listing photos, and attaching photos to a listing draft

| Field | Value |
|---|---|
| Wave | 26 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008) |
| Spec | `specs/listing-photos.md` |
| Owner | ai-engineer |
| Reviewer | reviewer (fable) |
| Co-reviewers | backend-foundation (sonnet, migration) |
| Risk flags | ai, migration |
| Model | opus |

## Read first
- `.claude/agents/ai-engineer.md`, playbook `ai-feature-with-evals`; decisions 0007, 0017, 0021, 0022, 0023 (if committed).
- `invai-backend/src/ai/{gateway,models,credits,breaker}.ts`, `src/ai/providers/{types,anthropic,openai,mock}.ts`, `src/ai/prompts/index.ts`, `src/ai/validators/listing.ts`, `src/modules/ai/service.ts` (draft shape, `mockupKeys`, disclosures, `toContent`), `src/db/schema/ai.ts`, `evals/`.
- Installed SDKs: `node_modules/@anthropic-ai/sdk/resources/messages` (image content blocks), `node_modules/openai` (Responses API image input). Check limits (image bytes/pixels) there or in official docs, and say which.
- `wave.md` "Agreed interfaces"; contract `invai-contracts/src/contract/photos.ts` (T-26-1) for `DesignPhotoAnalysis`.

## Owned paths (edit)
- `invai-backend/src/ai/**`, `invai-backend/src/modules/ai/**`, `invai-backend/evals/**`
- `invai-backend/src/db/schema/ai.ts`: credit kinds `photo_image` and `photo_scene` (mirror of the contract's `CREDIT_KINDS`, ~line 175), the AI job kind for the analysis, the new `listing_drafts.image_disclosures` column (jsonb, default `{aiGenerated:false, syntheticPerformer:false}`), and a partial unique index on `ai_credit_ledger (company_id, ref_type, ref_id) WHERE ref_type LIKE 'photo_%'`; migration `pnpm db:generate --name ai_photos`, committed in your **first** commit together with the stubs, **before** T-26-4 generates its migration (journal order). backend-foundation co-reviews this migration.

## Read-only paths
- `invai-backend/src/modules/photos/**` (T-26-4), `src/integrations/**`, `src/db/**` except `schema/ai.ts`, `invai-contracts/**`, `invai-imaging/**`, `invai-web/**`.

## Depends on
- T-26-1 contract for the analysis and draft shapes. Start with the stubs below as soon as it lands.

## Interfaces promised (commit stubs first, in your first commit, so T-26-4 can build)
- `analyzeDesignForPhotos(companyId, userId, { designId, previewKey, palette, designName, tags }) -> Promise<DesignPhotoAnalysis>` in `src/modules/ai/photo-analysis.ts`. No transaction is held across the model call (pattern: `generateDraft`, `service.ts` ~450); T-26-4 calls it from a job on the `ai` queue.
- `attachPhotosToDraft(tx, ctx, { draftId, imageKeys, aiGenerated, syntheticPerformer }) -> Promise<ListingDraft>` in `src/modules/ai/service.ts` (or a sibling file).
- `PHOTO_TEMPLATE_CREDITS = 1`, `PHOTO_SCENE_CREDITS = 10` exported from `src/ai/models.ts` (or `credits.ts`), and credit kind `photo_image`.

## Acceptance criteria
1. **Vision route.** A new AI route (for example `photo_analysis`) with its prompt in `src/ai/prompts`, a Zod output validated by the gateway, per-route model and effort in `models.ts` for Anthropic and OpenAI, and image input support added to the providers (image bytes or a presigned URL of the design's small preview, never the full print file; never buyer data). The model returns: style, niche/audience, detected text, color description, recommended blank colors (name + `#rrggbb` + reason), scene suggestions (kind, description, `containsPerson`), alt text per channel (plain, ≤ 250 characters, no keyword stuffing, no claims), and image order per channel (list of views). Untrusted design text stays inside the data block (prompt-injection rule).
2. **Deterministic mock.** With no AI key (and always for sample workspaces), the mock returns a stable analysis derived from the palette, name and tags (same input → same output), recommends colors that contrast with the art, and labels itself as sample (`source: "mock"`).
3. **Gateway controls apply.** Credits are asserted and charged through the gateway (`ai_jobs` row, `tokensToCredits`), spend caps (`assertSpendAvailable`) are checked first, a refusal or bad output maps to the usual typed error, and no PII is sent.
4. **Evals.** `evals/` gains a photo-analysis set of at least 12 cases (light art, dark art, text-heavy, multi-color, transparent background, a design with a brand-like word) with checks on schema validity, that recommended colors avoid light-on-light/dark-on-dark against the palette, alt text length and no banned claims. `pnpm evals photo-analysis` passes in mock mode; real-model mode is the owner's run later (state it).
5. **Attach.** `attachPhotosToDraft` appends the keys to the draft's `mockupKeys` (no duplicates, order kept, max as the channel allows: Etsy 20), refuses images whose channel doesn't match `draft.channel` (BAD_REQUEST), stores the image disclosures in `listing_drafts.image_disclosures` (never in `content`, which `regenerateDraft`/`toContent` rebuilds), and when `aiGenerated` the Etsy CSV export (`exportCsv`, ~line 771) appends a separate en/es `IMAGE_AI_DISCLOSURE` sentence ("Some product photos are AI-generated scenes; the design is our own." — compliance-officer checks the wording in wave 27) without reusing `AI_DISCLOSURE`. It sets the draft's image disclosures (`aiGenerated` → the Etsy AI disclosure is set for that draft; `syntheticPerformer` recorded for Amazon), writes an audit row, refuses another tenant's draft with NOT_FOUND and a draft in `publishing` with CONFLICT. Disclosures, once set by an AI image, are not cleared by attaching template images later.
6. Tests: unit tests for the mock determinism, validator rejections, the provider image-input request body (stubbed HTTP, as in `openai-provider.test.ts`), attach idempotency and tenancy.

## Verification
- `pnpm vitest run --reporter=dot src/ai src/modules/ai 2>&1 | tail -n 40` while building; once at the end `set -o pipefail; pnpm typecheck && pnpm lint && pnpm test > /tmp/t263.log 2>&1; echo $?; grep -nE 'FAIL|Error' /tmp/t263.log | head -n 30; tail -n 15 /tmp/t263.log` (Bash timeout 600000).
- `pnpm evals photo-analysis` (mock) output in the report.
- Exercise: a small script (`pnpm tsx`, not committed) calling `analyzeDesignForPhotos` for a seeded Desert Bloom design inside `withTenant`, on the dev DB, AI keys blanked (`OPENAI_API_KEY= ANTHROPIC_API_KEY=`): show the analysis and the credit ledger row.

## Out of scope
- The photos module, jobs and tables (T-26-4). The image-generation provider (wave 27, T-27-1). Any change to listing-draft prompts.

## Commit and report
- Commit only owned paths (stubs first, then the rest), message ending with the co-author line from your instructions. Don't push; only the tech lead pushes after the gate. Never print a key.
- Report: `invai-docs/waves/26/reports/T-26-3.md` (verify-and-report, at most 60 lines, PIDs started/stopped); reply in at most 8 lines.
