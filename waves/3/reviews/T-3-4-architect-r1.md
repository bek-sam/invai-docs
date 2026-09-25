# Review of T-3-4 (round 1): architect co-review of the contract stubs

- Reviewer: architect (co-review, on a different model from the stub author) on Opus 5.5
- Author of the stubs: architect, commit `06e62a3` (trailer: Claude Sonnet 5). The consumers are backend-foundation's `97651a0` / `a6ea3a1`.
- Verdict: **approve** (for the contract). The web consumer finding is tracked in the web-engineer and reviewer files.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show 06e62a3` | 4 files, +21/−4: doc comments on `channels.importCsv` and `shipping.batchBuy`; `ImportReport.status` enum plus `jobId`; `BatchBuyResult.status` |
| contracts `tsc`, `biome check .`, `vitest run` | clean; 4 files, 31 tests passed |
| backend `tsc` / web `tsc` / floor `tsc` against `06e62a3` | all exit 0 |
| backend `vitest run` | 59 files, 414 tests passed (includes `authz.test.ts`, which walks `listProcedures()`) |
| Consumer grep: `batchBuy`, `importCsv`, `ImportReport`, `BatchBuyResult` in `invai-web/src`, `invai-web/e2e`, `invai-floor/src` | consumers: `web shipping.tsx:131`, `web settings/channels.tsx:217,260`, `web e2e/api-golden-path.spec.ts:65`; none in floor |
| Live | `batchBuy` returned `status: "queued"` + `jobId`. `importCsv` (1,200 rows) returned `status: "queued"`, `jobId === importId`. `channels.imports` later returned `status: "completed"` with `jobId` set. The small-file path (golden path step 2, Etsy CSV) returned the completed report, and the step passed. |

## Contract fit
| Check | Result |
|---|---|
| Additive | Yes. `"queued"`/`"running"` are appended at the end of the `ImportReport.status` enum. `jobId` is `Id.nullable().optional()`. `BatchBuyResult.status` is `z.enum(["completed","queued"]).optional()`. No procedure, route, permission or error was changed or removed. |
| Deviation from wave.md | `wave.md` specified `.default("completed")`; the stub uses `.optional()`, documented as "absent means completed". Acceptable, and arguably safer: `.default` would make the output type's `status` required and break `shipping/service.ts`'s old sync `batchBuy`, which builds the object without it. The web consumer handles it correctly (`res.status !== "queued"` treats absent as completed). |
| Every consumer handled | `shipping.tsx`: updated the same day under the named grant (see web-engineer finding 1 for its failure paths). `settings/channels.tsx`: the ≤300-row inline path keeps the finished-report behaviour, and a large file renders as zeros, which the r1 plan review accepted (poll wiring deferred to B-85). `api-golden-path.spec.ts`: uses a small fixture, so it stays on the inline path. Floor: no consumer. |
| Old clients (one version behind) | oRPC clients don't validate outputs, so an old web receiving `"queued"` renders zeros rather than crashing. |
| Invariant "async work returns `JobRef { jobId }`" | Both results carry `jobId`. The poll target `production.jobs.get` exists, `Job.kind` already includes `csv_import` and `batch_labels`, and `JOB_STATES` gives the web a closed set of terminal states. |
| Permissions | No new procedure. Polling reuses `production.read`, and every role holding `shipping.buy` (owner, admin, office, packer) or `channels.import` (owner, admin, office) also holds `production.read` (`roles.ts`). So no role can start a job it can't poll. |
| Internal events | `channels.import_requested`, `shipping.batch_requested`, `artwork.render_requested` are backend-internal outbox names, not in contracts `Events`. This follows the existing `sheet.regenerate_requested` precedent. Fine. |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| Contract part of 1 and 3 (async results) | Yes | The shapes match the r1 plan review, apart from the documented `.optional()` deviation. Consumers typecheck; behaviour verified live. |

## Blocking findings
None for the contract.

## Checks
- [x] Only `invai-contracts/src/{contract,schemas}/{channels,shipping}.ts` changed.
- [x] Nothing outside scope; no new procedure.
- [x] Contract tests pass. No contract test was added for the new enum values (optional note 1).
- [x] No tenancy surface. Money unchanged (`totalPostage` in cents).
- [x] No ADR needed. This applies the existing "async work returns a job id" invariant.

## Optional notes (not blocking)
1. Add a round-trip test in contracts: `ImportReport.parse({... status: "queued", jobId })`, and `BatchBuyResult` with and without `status`. This pins the additive shape.
2. The `BatchBuyResult` doc should say that once the batch is always a job, `results`/`labeled`/`failed`/`totalPostage` are always empty or zero. Also add a follow-up, through `contract-deprecation`, to either drop `"completed"` or mark the sync fields deprecated. Otherwise new consumers will keep branching on a path the server never takes.
3. `Job` carries no postage or per-order outcome, so the web fans out to `shipments.get` for each label (web-engineer note 2). Consider an optional `summary`/`totals` object on `Job` (additive) in a later wave.
4. `job.progress` realtime exists. Documenting it as the preferred progress channel next to `production.jobs.get` in both procedure docs would stop consumers from polling.
