# T-P2-3: `settled()` reports its own timeout instead of swallowing it

| Field | Value |
|---|---|
| Wave | P2 |
| Scope ref | `always-in-scope: bug` (test that masked the P1 gate cause, `waves/P1/reports/gate-rootcause.md` §1 "Secondary") |
| Owner | qa-engineer |
| Reviewer | reviewer (sonnet) |
| Co-reviewers | none |
| Risk flags | none (test code only) |
| Model | sonnet |
| Depends on | T-P2-1 committed (otherwise the catalog page legitimately times out) and the :3000/:5173 slot free |

## Owned paths (edit)
- `invai-web/e2e/helpers/ui.ts` (the `settled()` helper only), plus any spec under `invai-web/e2e/` whose call site must pass an explicit longer timeout (say which and why).

## Read-only paths
- `invai-web/src/**` (T-P2-1), everything else.

## Acceptance criteria
1. `settled()` (`e2e/helpers/ui.ts:74-83`) no longer has `.catch(() => {})`. On timeout it fails with a message that names how many skeletons/spinners are still present and the URL.
2. No allow-list, retry, sleep or `.skip` is added anywhere (`run-golden-path` rules).
3. With T-P2-1 in, `pnpm e2e` (all web specs except the API golden path) passes on the dev DB; any spec that now fails is root-caused in the report with owner (not loosened).

## Verification
- `cd invai-web && pnpm typecheck && pnpm lint 2>&1 | tail -n 20`; `pnpm e2e --reporter=line 2>&1 | tail -n 30` on the API :3000 + web :5173 slot (start `dev:api`, `dev:worker`, web `dev`; record PIDs; stop them before reporting; don't reseed).

## Budget
- About 1 hour.

Commit only your paths in `invai-web`. Don't push. Report: `invai-docs/waves/P2/reports/T-P2-3.md` (at most 40 lines).
