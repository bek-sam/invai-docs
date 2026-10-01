# Review of T-P1-4 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-engineer (catalog) on Opus 5.5 (card said sonnet; `files` flag: security-reviewer co-review still required)
- Verdict: approve (commit invai-backend 7247b32)

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (invai-backend) | tsc clean; biome 453 files, no fixes |
| `pnpm test src/modules/catalog src/modules/orders src/integrations/imaging src/db --reporter=dot` (own per-run DB) | 22 files, 103 passed (includes rls-coverage); placeholder-fallback test logged "fetch failed" and passed |
| `scan-test-weakening.sh invai-backend 7247b32~1` | 0 assertions removed, 17 added; hits: `vi.mock` of the imaging client in jobs.test (a dependency, not the unit) and a `toBeTruthy` followed by an exact `toMatch`. Not blocking |
| psql read-only on dev DB | `design_files`: 40 rows, 40 preview keys, 40 under `<company_id>/preview/design/` |
| `mc cat` one preview key from MinIO, `file` | PNG 458 x 512 RGBA (longest side 512) |
| Fail-without-change | jobs.test imports `renderDesignPreviewsJob`, which doesn't exist on 7247b32~1, so it can't pass on the base |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | jobs.ts:43-57: a `render`-queue job subscribed to `design.updated` (qaRequested), not inline. Key `designPreviewKey(companyId, fileId)` is deterministic (service.ts:331), so a rerun overwrites one object. The jobs.test two-run test asserts the same out_key and one row. The relay's `relayJobId` falls back to the event id after completion, so a later replace still runs |
| 2 | Yes | service.ts:229-230: a replace deletes and reinserts the `design_files` rows, and `preview_key` (schema/catalog.ts:61) defaults to null. The author's curl showed null, then set ~4 s later. No test covers this (note 2) |
| 3 | Partial, gap is honest | mapping.ts:114 copies `file?.previewKey` at mapping time. "Filled in later" isn't wired, and the report says so. The gap is smaller than it reads: order-detail.tsx:261 falls back to the design's `placements[0].previewKey`, so the drawer still shows a thumbnail |
| 4 | Yes (by code + dev DB) | Seed order: designs (builder.ts:488-557) render the preview before orders (~955). I did not reseed. Dev DB has 40/40 from the author's job run |
| 5 | Yes | client.ts:299-318: any failure writes a 64 px placeholder PNG to out_key. client.test's unreachable-host case passed in my run |
| 6 | Yes | jobs.test and service.test: company B's design under A's tenant gives NOT_FOUND |
| 7 | Yes | service.ts:347-353 checks `isCompanyKey` on fileKey and outKey per file, before `imaging.preview`. service.test gives BAD_REQUEST for a foreign fileKey. The seed builds both keys from its own shopId |

## Blocking findings
none

## Checks
- [x] Only owned paths changed. 8 files: catalog/** owned. In client.ts, only the preview method, its placeholder helper and imports. In mapping.ts, only the artworkPreviewKey line. In the seed, only the preview import, map and key lines.
- [x] Nothing outside scope: no web, imaging, migration or contract change.
- [x] Tests exercise the behavior, and none were weakened.
- [x] Tenancy: `withTenant` in the job, no new `withSystem`, no new tables. Idempotent: a deterministic key plus an UPDATE by file id. Money and copy: n/a.
- [x] Decisions: none needed. The in-client fallback is explained in the report.

## Optional notes (not blocking)
1. client.ts:303 falls back on **any** error (422, a 5xx, a timeout, 429s used up), not only "imaging down". The job then saves a gray placeholder as the real `preview_key`, and nothing re-renders it when imaging recovers. The comment at service.ts:340 ("until imaging is back") isn't true. Suggested follow-up: re-render placeholder previews when imaging comes back, or fall back only when imaging isn't configured.
2. No test covers AC2 (preview cleared on replace) or AC3 (mapping copies the preview). It works today only because of the delete and reinsert at service.ts:229. Add regression tests.
3. Each replace creates new file ids, so old preview objects are left in S3. Storage grows, but there is still only one object per file.
4. The job holds a tenant transaction open across the imaging call (timeout up to 120 s). This is the same pattern as `runDesignQa`, and the same open-transaction-across-slow-call issue from the idempotent-job playbook.
5. On a fresh seed, history orders (around 4k) and personalized items get no `artworkPreviewKey`. Only live, non-personalized items do. Drawers are still covered by the web fallback in AC3. The commit message says "mapped order items get it too", which overstates this.

PIDs: none started (listeners on 3142 and 3157 belong to other agents and were left alone).
