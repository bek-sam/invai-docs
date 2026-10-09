# T-30-1: Gang-sheet print files, orphan renders and shared buyer photos follow the buyer-text clocks

| Field | Value |
|---|---|
| Wave | 30 |
| Scope ref | `always-in-scope: compliance` (Amazon DPP "PII deleted 30 days after delivery", decision 0027 known gaps) and `security` (S-59 Low) |
| Spec | decision 0027 (`decisions/0027-buyer-text-retention.md`), backlog B-300, B-301, B-304; `waves/29/reports/T-29-1.md`; `waves/29/reviews/T-29-1-{compliance-officer,security-reviewer}-r1.md` |
| Owner | backend-engineer (area: privacy) |
| Reviewer | reviewer (fable) |
| Co-reviewers | security-reviewer (opus), compliance-officer (sonnet) |
| Risk flags | pii, files, tenancy, data deletion, floor-correctness |
| Model | opus |

Role file: `.claude/agents/backend-engineer.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-engineer/` (read MEMORY.md first; T-29-1 notes are there).

## Owned paths (edit)
- `invai-backend/src/modules/privacy/**` except `security.test.ts`
- `invai-backend/src/modules/privacy/security.test.ts`: **grant, one change only**: the S-59 case at line ~119 flips from `it.fails(` to `it(` once your fix makes it pass. Nothing else in that file.
- `invai-backend/src/modules/orders/jobs.ts`: only `PII_OBJECT_KINDS`, `purgePiiObjects`, `purgeBuyerPiiJob` and the purge result type; `src/modules/orders/purge.test.ts`
- `invai-docs/decisions/0031-print-files-and-orphan-renders.md` (new, status `proposed`; security-reviewer and compliance-officer accept it) and its index row in `invai-docs/decisions/README.md`
- Report: `invai-docs/waves/30/reports/T-30-1.md`

## Read-only paths
- `invai-backend/src/modules/production/**` (sheets, transfers), `personalization/**`, `vendors/**`, `src/lib/s3.ts`, `src/db/**`, every other repo. A gap there goes to your report under "Blocked by other owners".

## Depends on
- none. No contract change: `GangSheet.files.{pngKey,pdfKey,previewKey}` are already nullable and the web disables the download buttons when null (`invai-web/src/routes/_app/production/sheets.$sheetId.tsx:204`, vendor `sheets.$sheetId.tsx:167`). If you find you need a contract value, stop and tell the tech lead.

## Interfaces promised
- `purgeBuyerPiiJob` keeps its name and queue; its result gains `sheetFilesPurged`, `sheetsWaiting`, `orphanRendersDeleted`, `sharedPhotosKept` (counts only, no ids or keys in logs).

## Acceptance criteria
1. **Inventory first.** Before coding, list in the report every storage object kind that can hold rendered buyer text or a buyer photo, with the column(s) that point at it and the clock that removes it after this card: at least `sheet` (png, pdf), sheet `preview`, personalization `preview` (`personalization/service.ts:393`), `artwork`, `photo`, the `labels` kind (`production/floor.ts:1202`, `inventory/service.ts:1642`: say whether a caption can carry buyer text), vendor delivery files (`vendors/delivery.ts`), and anything else `objectKey(` writes. A kind you find that this card doesn't cover becomes a "Known gaps" line with an owner.
2. **Sheet print files (B-300).** Given a gang sheet holding at least one unit whose `order_items.artwork_status = 'purged'` (purged by any of the three 0027 clocks), and the sheet's status is `printed`, `shipped`, `received`, `cancelled` or `failed`, when the nightly purge runs, then the sheet's png, pdf and preview objects are deleted from storage first, then its three keys are set to null and any `files` rows for those keys are forgotten. The sheet row, its transfers, counts, cost and dates stay. The earliest unit's clock wins: one purged unit is enough.
3. Given such a sheet still in `building`, `ready`, `printing`, `sent` or `acknowledged`, then its files are kept (the shop or vendor may still print it), it is counted in `sheetsWaiting`, and it is picked up on the first night after it reaches one of the states in AC2. A sheet with no purged unit (no personalization, or not yet on its clock) is never touched.
4. **Storage first, idempotent.** A sheet whose object delete fails keeps all three keys and is retried the next night (`failedFiles` counts it). A second run on the same data deletes nothing and changes no row. Runs per company inside `withTenant`; a test proves company B's sheet files survive when company A's job runs.
5. **Orphan renders (B-301).** Given objects under `{company}/artwork/` (and personalization previews, if AC1 shows they carry buyer text and nothing deletes them) that no row points at and that are older than 2 days, when the nightly purge runs, then they are deleted. "Points at" must cover every column that can hold such a key: grep all of `src/db/schema/**` for key columns and list them in the report (at least `item_artwork.file_key`/`preview_key`, `order_items.artwork_key`/`artwork_preview_key`, and any design, listing, mockup or `files` row that can store an `artwork/` key). A referenced object, or one younger than 2 days (a render in flight), is never deleted. One test per referencing column proves its object survives.
6. **Shared buyer photo (B-304, S-59).** Given a buyer-photo key used by two units' artwork values, when the first unit is purged, then the photo object is kept (counted in `sharedPhotosKept`) and deleted when the last unit using it is purged. The S-59 `it.fails` case in `privacy/security.test.ts` passes and is flipped to `it(` (the one-line grant).
7. **Floor correctness.** No sheet in AC3's states loses a file; no unit still in production loses its render (AC5's reference check). A test covers each.
8. **Decision 0031** (proposed) records AC2–AC6 as a rule with exact values (states, 2-day minimum age, earliest-clock rule), what is kept, and the remaining gaps (vendor copies outside InvAI, anything from AC1 left open). It narrows 0027's "Known gaps"; 0027 itself is not edited.

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint && pnpm test` (full suite once at the end, `set -o pipefail`, output to a log, timeout 600000).
- New tests red on `32113d7` (main before this card): show each with a worktree run or a mutation, in the report.
- Exercise for real: on a scratch DB (`invai_t30_1`, `REDIS_URL` on Valkey DB 12, `SEED_OUTPUT_FILE=/tmp/t30-1-seed.json`) or on `invai_test` fixtures with MinIO: a received sheet with a purged unit loses its 3 objects (HEAD 404) and keys; a `ready` sheet keeps them; an orphan render older than 2 days goes, a referenced one stays; a shared photo stays; a rerun prints all zeros. Never run the purge against the shared dev DB `invai`.
- Record every PID you start in the report and stop them all.

## Out of scope
- `audit_log` flag values (B-302), manual uploads outside the artwork prefix (B-303), purge-order notes (B-307), any web change, any contract change, re-rendering sheets without the text.

## Commit and report
- Commit only your paths (`git add <paths>`), message ends with the attribution line. Don't push; only the tech lead pushes after the gate.
- Report ≤ 60 lines in `verify-and-report` format, saved progress line by line as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
