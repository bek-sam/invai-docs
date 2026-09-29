# 0017: Listing attributes are one string map at the API and in the database; the model's list is transport only

- Status: accepted (2026-09-28), T-22-1 (B-167), architect; T-22-5 (backend-engineer, ai-engineer co-review) applies it
- Type: architecture

## Context
`ListingContent.attributes` in `@invai/contracts` (`src/schemas/ai.ts`) is `Record<string, string>`
("material" → "cotton"), and `listing_drafts.content` in `invai-backend/src/db/schema/ai.ts` stores
the same shape with a column default of `attributes: {}` baked into an applied migration. The AI
route's structured output, `ListingCopy` in `invai-backend/src/ai/prompts/index.ts`, returns
`attributes: { key, value }[]` instead, because a JSON schema for a model can't describe a map
with open keys. `invai-backend/src/modules/ai/service.ts` `toContent()` folds the list into the
map. Backlog B-167 called this a drift and T-13-3 tried to align the contract to the list; that
broke `src/api/orpc.test.ts` because the DB default still produced `{}`, and the work was reverted
(`waves/13/reports/T-13-3-report.md`). Changing the API shape is a breaking contract change for
web and any future partner API; changing the DB default needs a migration and a backfill. Nothing
in web reads `attributes` today (no consumer would benefit from the list). Decided by the
architect on T-22-1; reviewed by reviewer and ai-engineer.

## Decision
1. The one shape for listing attributes at the API (`ListingContent.attributes`) and at rest
   (`listing_drafts.content.attributes`) is `Record<string, string>`, keyed by the channel
   attribute name. It is not changed to a list.
2. The `{ key, value }[]` list exists only as the model's structured-output transport
   (`ListingCopy`). It is folded into the map exactly once, at the AI boundary
   (`toContent()` in `modules/ai/service.ts`), and never stored, returned or validated elsewhere.
3. Folding rule: keys are trimmed; an empty key is dropped; on duplicate keys the first wins.
   The backend test for `toContent` asserts these three cases (T-22-5, ai-engineer's grant).
4. No migration: the existing column default `{}` is already the decided shape.
5. Any future need for ordered or repeated attributes (for example an Amazon attribute that takes
   several values) gets a new optional field (for example `attributeList`) through
   `add-contract-procedure`, never an in-place change of `attributes`.

## Consequences
- B-167 closes without a contract or DB change; web and floor are untouched.
- T-22-5 makes the folding rule explicit and tested in `toContent` (its grant into
  `modules/ai/service.ts`, co-reviewed by ai-engineer) and removes the "drift" wording from the
  backend's `ListingContent` type comment if any.
- The contract's doc comment on `attributes` points here so the next reader doesn't reopen it.
- Enforced by: `invai-contracts/src/p2-sweep.test.ts` (rejects a list for `attributes`) and the
  backend `toContent` test.
