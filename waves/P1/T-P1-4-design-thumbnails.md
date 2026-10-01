# T-P1-4: Design and order-item thumbnails (B-209)

| Field | Value |
|---|---|
| Wave | P1 |
| Scope ref | `always-in-scope: bug` (B-209, Medium) |
| Spec | backlog B-209 |
| Owner | backend-engineer (catalog) |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (sonnet), `files` flag (architect ruling 5) |
| Risk flags | files |
| Model | sonnet |
| Depends on | T-P1-1 committed (test isolation); T-P1-2's `/preview` commit (imaging) |

## Tech lead's root-cause notes (confirm them; `root-cause-bug`)
- Nothing ever writes `design_files.preview_key`: the dev DB has 40 design files and 0 preview keys. `catalog/service.ts` inserts at ~178/230 and updates at ~302 without it; the seed (`db/seed/builder.ts`) doesn't set it.
- The web list (`invai-web/src/routes/_app/catalog/designs.index.tsx:177`) shows `placements[0].previewKey` only; the detail page falls back to `fileKey`. Order items read `artworkPreviewKey`, which `orders/mapping.ts:~106` sets to null for non-personalized items.
- Imaging has no thumbnail route; T-P1-2 adds `POST /preview` (interface in `wave.md`).

## Owned paths (edit)
- `invai-backend/src/modules/catalog/**`
- Grants: `src/integrations/imaging/client.ts` (+ test), the `preview` method and its mock only; `src/modules/orders/mapping.ts`, the `artworkPreviewKey` assignment only; `src/db/seed/**`, only lines that set preview keys for seeded designs and order items.

## Read-only paths
- `invai-imaging/**` (T-P1-2), `invai-web/**`, `src/test/**` (T-P1-1), `src/ai/**`, `src/modules/ai/**` (T-P1-3), everything else.

## Acceptance criteria
1. When a design file is attached or replaced, a preview job (queue, not inline; rule 9) calls `imaging.preview` and stores `preview_key` (company-prefixed key from the existing key helper). Idempotent: re-running the job for the same file writes one preview and the same key, not a second object per run.
2. A replaced file clears the old preview key until the new one is ready (no stale thumbnail).
3. Order items for a mapped design get `artworkPreviewKey` from the design file's preview (at mapping time, and filled in when the preview lands later if that is simple; otherwise say how it fills).
4. The seed produces preview keys for all seeded designs (through the same imaging call, imaging up), so `/catalog/designs` on a fresh seed shows 40/40 real thumbnails.
5. The mock imaging client returns a valid small PNG key so the platform still works with imaging down.
6. Tenant isolation: a preview job for company A can't read or write company B's keys (test).
7. Imaging doesn't check company prefixes (S-11/S-12 model; T-P1-2 security review): the backend calls `isCompanyKey(companyId, key)` on both `file_key` and `out_key` before every `imaging.preview` call, and refuses otherwise (test).

## Verification
- `cd invai-backend && pnpm typecheck && pnpm lint 2>&1 | tail -n 20`; `pnpm test src/modules/catalog src/modules/orders src/integrations/imaging --reporter=dot 2>&1 | tail -n 20`
- Don't reseed the shared dev DB. Prove AC4 on a scratch DB copy (`team/agent-brief.md` "Scratch seed stacks", pin `REDIS_URL` to your own DB) or by running the preview job for the 40 existing dev designs through your own API/worker on `PORT=31xx` (record PIDs), then `select count(preview_key) from design_files` → 40.
- Sign in as office@ on your API, call `catalog.designs.list`, fetch one preview through the signed-URL path and check it's a PNG ≤ 512 px.
- The browser check of /catalog/designs happens at the gate.

## Out of scope
- Web changes (the list already reads `previewKey`). Imaging code. New migrations.

## Budget
- About 3 hours. Stop and tell the tech lead if blocked for 30 minutes.

Commit only your paths. Don't push. Report: `invai-docs/waves/P1/reports/T-P1-4.md`.
