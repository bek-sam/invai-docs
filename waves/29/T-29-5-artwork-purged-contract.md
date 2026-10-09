# T-29-5: Contract: `purged` artwork status (lands first)

| Field | Value |
|---|---|
| Wave | 29 |
| Scope ref | `always-in-scope: security / compliance` (S-56, B-293; needed by T-29-1) |
| Spec | `reviews/plan-architect.md` item 1 |
| Owner | architect |
| Reviewer | reviewer (opus, a different model from the author) |
| Co-reviewers | backend-foundation (sonnet) + web-engineer (sonnet, consumer) |
| Risk flags | contract (additive) |
| Model | sonnet |

## Owned paths (edit)
- `invai-contracts/src/schemas/personalization.ts` (`ITEM_ARTWORK_STATUSES`), `invai-contracts/src/schemas/orders.ts` (`ItemArtworkSummary.status`, ~:83)
- `invai-contracts/src/compat.ts` (`CONTRACT_VERSION`), `invai-contracts/package.json` (version 0.14.0), tests for these files, `README.md`/`CHANGELOG.md` if present; any test that pins the exact version (relax to "at least")

## Read-only paths
- every other repo (consumers are linked with `link:../invai-contracts`; their fixes are in T-29-1 for backend and T-29-3 for web)

## Depends on
- none. First card to commit in this wave.

## Interfaces promised
- `"purged"` appended (last) to `ITEM_ARTWORK_STATUSES` and to `ItemArtworkSummary.status`; nothing removed or renamed; minor bump to 0.14.0.

## Acceptance criteria
1. Given the contract, `ItemArtwork.status` and `ItemArtworkSummary.status` accept `purged`, and every old value still parses (test).
2. The `counts` record (`z.record(z.enum(...))`, exhaustive in zod 4) is noted in the report as a known consumer break: backend `personalization/service.ts:790` (T-29-1 fixes it). Run `pnpm typecheck` in invai-backend, invai-web and invai-floor after your commit and list every error with file:line in the report (expected: backend `:723`, `:790`; web and floor none).
3. A short doc comment on the enum says what `purged` means ("buyer text and art removed under the PII clocks; re-enter to print").

## Verification
- `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 40` in invai-contracts; consumer typechecks as in AC 2 (report only, don't fix).
- Commit only your paths; don't push (the tech lead pushes after the gate).

## Out of scope
- Any backend, web or floor change.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work.
