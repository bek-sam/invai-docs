# Review of T-P2-2 (round 2)

- Reviewer: reviewer on Opus 5.5. Author: backend-engineer (catalog). Commits reviewed: f6002ff, 79906a5 (9338944 is another card's; not reviewed).
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (invai-backend @79906a5) | exit 0, `Checked 456 files`, no errors |
| `pnpm test src/modules/{catalog,orders,production} src/integrations/imaging src/db/rls-coverage.test.ts src/api/authz.test.ts --reporter=dot` | 21 files, 140 tests passed |
| `jobs.imaging-down.test.ts` on `git archive f6002ff` in /tmp | **red**: "promise resolved `{ placements: 1 }` instead of rejecting" (old client placeholdered) |
| r2 `service.test.ts` on f6002ff | 10/10 green: replace-clears is gap-closing (no fix needed), as the report says |
| `scan-test-weakening.sh invai-backend f6002ff` | 0 assertions removed, 26 added; hits are `vi.mock` of the imaging client (dependency) and 9338944's today spies |
| tsx script, real client, own imaging on :8023 (stopped; port free) | default call (seed shape), imaging up: real 465x512 preview; default, closed port: 64x64 placeholder; `allowPlaceholder:false`, closed port: throws (status 0) |

## Round 1 findings
| # | Closed? | Evidence |
|---|---|---|
| (b) job-path placeholder | Yes | `client.ts:323` rethrows before `checkHealthy()` when `allowPlaceholder` is false; `service.ts:378-383` always passes false; the option is stripped from the HTTP body (`client.ts:318`). Red/green test above. 4xx/422 path unchanged (warn, null key). Matches the tech lead ruling. |
| (a) AC0 wording | Yes | Report AC0 now says "not reproduced" and lists the limits |
| (d) red before fix | Yes | Imaging-down test red on f6002ff with the real client (only the URL is mocked). Replace-clears test added (`service.test.ts:246`); green on base is fine because it is a T-P1-4 regression test, not a fix |

## service.test.ts mock
Mocks `imaging.preview` (an external dependency, not the unit under test). Every pre-existing assertion is unchanged: key prefix, same key on retry, BAD_REQUEST for a foreign key, NOT_FOUND cross-tenant. Before this change those tests passed only through the client's placeholder (no imaging in plain test runs), so nothing they proved is lost. The real-client behavior is covered by `client.test.ts` and `jobs.imaging-down.test.ts`.

## Seed
`db/seed/builder.ts:535` is unchanged and uses the default (`allowPlaceholder` true). With imaging up it renders real previews (shown above). With imaging down the seed skips sample art (`rendered=false`) and never calls `preview`, so `previewKey` stays null. That is the behavior from before this card, not a regression; the client placeholder stays for direct callers (mock kept).

## Checks
- [x] Owned paths only (r2: client.ts, catalog/**). Scope held. No migration.
- [x] Tenancy: `isCompanyKey` on both keys is unchanged; `withTenant` throughout. Idempotency: same jobId and deterministic key.

## Optional notes (not blocking)
- `jobs.imaging-down.test.ts` is red on base only when MinIO is up. Without MinIO, the old placeholder `putObject` would also throw.
- Scratch objects `00000000-…-0a2b/{design,preview/design}/review-r2*.png` remain in local MinIO bucket `invai-local`. They are harmless and outside any real tenant.
