# T-13-3 report: contract drift cleanup (B-104, B-110)

Status: **stopped early on the tech lead's "pause to save usage" instruction.** Finished pieces are
committed and green; the attributes-shape item is reverted, uncommitted work left behind.

## Committed (green: typecheck + relevant tests pass in all four repos)

- `invai-contracts` `a2ef5d7`: removed `production.scanBatch` (ADR 0013 — never had a caller in
  any repo, checked against full git history, not just current contents) and the never-emitted,
  never-consumed `listing.synced` outbox event; added `Org.demoOwned` (sourced from
  `companies.demoOwnerUserId`); bumped `package.json`/`compat.ts`'s `CONTRACT_VERSION` to 0.4.0 and
  `CHANGELOG.md`. Not floor-facing, so `FLOOR_COMPAT_BASELINE` stays at 0.3.0.
- `invai-backend` `889c5aa`: dropped the `scanBatch` router handler; `toOrg` fills `demoOwned`;
  added `src/integrations/imaging/contract.test.ts` — generates each request Pydantic model's JSON
  Schema from the invai-imaging FastAPI app (`uv run python`, no server needed) and diffs it
  against the matching Zod schema in `client.ts` (TemplateSlot/SlotModel,
  RenderTemplate/TemplateModel, NestItem/NestItemModel, ComposePlacement+label/
  ComposePlacementModel+LabelModel). Response bodies aren't covered — every imaging endpoint
  returns a plain `dict` on the Python side, so there's no Pydantic response model to diff against.
- `invai-web` `819cd1f`: `isOwnDemo` now reads `me.org.demoOwned` instead of the
  `demo && slug === "demo-<id>"` heuristic.
- `invai-docs` `fa1e452`: ADR `decisions/0013-remove-scan-batch.md`; `waves/backlog.md` B-104/B-110
  marked done; `architecture.md`'s channels-module row corrected (it still named the removed
  `listing.synced`).
- Verified (no code change needed): `stock.changed` (realtime) is already published
  (`invai-backend/src/modules/inventory/ledger.ts`) and consumed
  (`invai-web/src/lib/realtime.ts`).

## Not finished — reverted, nothing left uncommitted

**Attributes shape** (`ListingCopy.attributes` vs `ListingContent.attributes`, one shape) was
implemented — contracts' `ListingContent.attributes` changed from `Record<string,string>` to
`{key,value}[]` to match the AI model's structured-output shape, plus the matching
`invai-backend` edits (`ai/service.ts`'s `toContent`/`exportCsv`, `db/schema/ai.ts`'s local
`ListingContent` type and default, `ai/ai.test.ts` fixtures) — but it broke
`src/api/orpc.test.ts`'s NUL-byte test: a freshly-inserted `listing_drafts` row still got
`attributes: {}` from Postgres's column-level `DEFAULT`, which is baked into an already-applied
migration and doesn't move just by editing the Drizzle schema source. A real migration
(`ALTER TABLE listing_drafts ALTER COLUMN content SET DEFAULT ...` or a data backfill) is needed
first. Rather than ship that half-finished, I reverted all four files
(`invai-contracts/src/schemas/ai.ts`, `invai-backend/src/modules/ai/service.ts`,
`invai-backend/src/db/schema/ai.ts`, `invai-backend/src/ai/ai.test.ts`) back to their committed
state with `git checkout --`, reran the full suite to confirm the regression is gone, and left
nothing uncommitted for this item — it needs to be picked up fresh (add the migration first, then
redo the schema/service/test edits above).

**Not touched at all:** the other 12 no-UI procedures (backlog B-112, correctly left open for
follow-up cards) — out of scope per the tech lead's decision in `wave.md`.

## Verification run before stopping
- `invai-contracts`: `tsc --noEmit` clean, `vitest run` 36/36 passed.
- `invai-backend`: `tsc --noEmit` clean; `vitest run src/api/orpc.test.ts src/modules/production/
  src/modules/tenancy/ src/integrations/imaging/` 106/106 passed (own test DB `t13_3_arch`, dropped
  before finishing — see below).
- `invai-web`: `tsc --noEmit` clean, `vitest run` 82/82 passed (full suite).
- `invai-floor`: `tsc --noEmit` clean, `vitest run` 96/96 passed (full suite; untouched by this
  card, confirms no accidental breakage).
- One pre-existing, unrelated flake seen in the full backend run: `src/auth.test.ts` password-reset
  mail-wait timeout — not touched by this card, not reproduced in the targeted reruns above.

## Cleanup
Own test DB `t13_3_arch` was in use on `local-postgres-1` at stop time; drop it with
`docker exec local-postgres-1 dropdb -U invai t13_3_arch` before the next agent needs a clean
Postgres. No other PIDs, worktrees or Redis DBs were held by this session.
