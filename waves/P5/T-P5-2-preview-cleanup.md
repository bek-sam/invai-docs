# T-P5-2: A replaced design's old previews are removed when nothing uses them; a late preview reaches order items (B-233 rest)

| Field | Value |
|---|---|
| Wave | P5 |
| Scope ref | `always-in-scope: bug` (orphan preview objects pile up in storage on every artwork replace; an item mapped before its design preview existed keeps an empty thumbnail until remapped) |
| Spec | backlog B-233 (the parts left after T-P2-2: cleanup on replace, late-preview backfill); `waves/P1/reports/T-P1-4*.md`, `waves/P2/reports/T-P2-2*.md`; architect plan-review rulings in `reviews/plan-architect.md` |
| Owner | backend-engineer (area: catalog; orders mapping) |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (sonnet): files |
| Risk flags | files |
| Model | sonnet |
| Depends on | architect plan review (cleanup rule) |

## Owned paths (edit)
- `invai-backend/src/modules/catalog/**`
- `invai-backend/src/modules/orders/mapping.ts`, `mapping.test.ts`, and one new file `src/modules/orders/preview-backfill.ts` (+ `.test.ts`) if you need it

## Read-only paths
- `invai-backend/src/modules/orders/service.ts` and the rest of `modules/orders/**` (T-P5-4), `src/db/seed/**` (T-P5-1), `src/lib/**` (use `deleteObject`, `isCompanyKey` as they are), `src/db/schema/**`, `src/test/**`, every other repo

## Acceptance criteria
1. Given a design whose file is replaced (`catalog.updateDesign` with a new file, service.ts ~230), when the new previews are written, then each old preview object is deleted from storage **only if** no row still references that key (at least `order_items.artwork_preview_key`, `design_files.preview_key`; the architect's ruling lists the full set). A referenced old preview stays. The delete runs outside the DB transaction (after commit or in the job) and a storage error is logged and doesn't fail the update.
2. Only keys of the same company are ever deleted (`isCompanyKey`), and never an original art file, a sheet or a label.
3. Given an order item mapped while its design had no preview yet (`artworkPreviewKey` null, mapping.ts ~114), when the preview job writes the design's preview, then that item gets the preview key, without a remap. Items with their own artwork (personalized, templated) or an existing preview key are untouched. Running the job twice changes nothing more (idempotent), and it stays tenant-scoped (`withTenant`).
4. Tests: replace clears the old preview when unreferenced and keeps it when an item references it (the T-P1-4 AC2 gap); late preview backfills the item (AC3 gap); a second company's item with the same design id shape is untouched. Each new test is red on `origin/main` (19a85c3): say how you showed it.

## Verification
- `pnpm typecheck && pnpm lint 2>&1 | tail -n 20`; `pnpm vitest run src/modules/catalog src/modules/orders/mapping.test.ts --reporter=dot 2>&1 | tail -n 20` in `invai-backend` (plus your new test). The gate runs the full suite.
- Exercise for real: API on `PORT=3150`, Valkey DB 14, worker on the same, imaging stub or a scratch imaging port. As `designer@desertbloom.test`, replace a design's file; list the MinIO keys under that company's preview prefix before and after (counts only); check one referenced old key is still there. As `presser@` the replace is refused (FORBIDDEN).
- Don't reset the shared dev DB; any rows you change on it must be your own test design.

## Out of scope
- The seed (T-P5-1), new contract fields, a migration, sweeping old orphans already in storage (note the count in the report as a follow-up).

## Rules
- Role file `.claude/agents/backend-engineer.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-engineer/`.
- Other agents at the same time: backend-foundation on T-P5-1 (`src/db/seed/**`), architect on contracts, later backend-engineer T-P5-4 (`orders/service.ts`, `today/**`). Don't touch their files.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; don't end your turn with a run or a process going. Record every PID you start and list it (stopped) in the report.
- Trim output. Report (≤ 60 lines) to `invai-docs/waves/P5/reports/T-P5-2.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
