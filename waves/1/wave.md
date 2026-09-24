# Wave 1: safe to put real keys in

- Dates: 2026-09-24 →
- Goal (user outcome): an owner can add real keys without InvAI faking success. Production refuses to run on mocks, webhooks are verified before anything else happens, tenants never spend InvAI's money, invites work, and a fresh production DB has its reference data.
- Plan reviewed by: product-manager (see `reviews/plan-product-manager-r1.md`), architect (see `reviews/plan-architect-r1.md`)

## Cards
| Card | Owner | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|
| T-1-1 | backend-foundation | reviewer + security-reviewer | auth, pii | done (approved r2) |
| T-1-2 | integrations-engineer | reviewer + security-reviewer, backend-foundation | webhooks, migration | done (approved r1) |
| T-1-3 | integrations-engineer | reviewer + security-reviewer, backend-foundation, architect (contract field) | payments, migration | planned |
| T-1-4 | backend-foundation | reviewer + security-reviewer, product-designer | auth, pii, ui | done (approved r2) |
| T-1-5 | ai-engineer | reviewer + backend-foundation | migration | done (approved r2) |

## Parallel work rules for this wave
- **Test databases.** Each card runs backend tests against its own test DB, so parallel runs don't truncate each other:
  ```
  TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_test_t1<k>
  TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_test_t1<k>
  ```
- **Shared dev DB.** Nobody runs `db:reset` on it during the wave. Only the integration gate does.
- **Migrations.** T-1-2 and T-1-3 may each add one. If the drizzle journal collides, the later card regenerates its own migration.
- **Ports.** Each card runs its own API on `PORT=31<k>0` when it needs one.

## Agreed interfaces (stubs committed first)
- `sendMail({ to, subject, text, html })` in `integrations/vendors/mailer.ts`. Signature unchanged. T-1-1 changes its config source; T-1-4 calls it.
- `env.isProd` and the new `env.allowMocks` (T-1-1). Other cards read them and don't redefine them.
- `ensureReferenceData(db)` (T-1-5), called at the end of `runMigrations`.
- A new optional, additive `idempotencyKey` field on `ReceiveInput` in `invai-contracts/src/schemas/inventory.ts`, needed for T-1-3's `receivePo` idempotency (AC3). `invai-contracts/**` is architect-owned; the architect commits this one-field stub before T-1-3's build starts, per the plan-architect review.
- `modules/channels/sync.ts` (`verifyWebhook`, `processWebhook`, `completeShopifyOAuth`) and `modules/channels/jobs.ts` are granted to T-1-2 for this card only (see its owned-paths note); the rest of `modules/**` stays read-only for integrations-engineer.

## Integration gate
- [x] Fresh reset, migrate (0000–0008, reference data 471 marks / 5 plans), seed (imaging up, worker stopped)
- [x] `run-golden-path` passes: API 13/13, browser 15/15, floor 1/1 (`gate.md`)
- [x] `pnpm build` passes in backend, web, floor
- [x] Invite flow screenshots in `gate/` looked at by the tech lead
- [x] Pushed to `main`: backend `34ed022…d97cd3c`, contracts `1a22b29`, `a3b4067`, web `d6336e0`, `dc9f655` (the wave 2 stubs were reviewed separately in `waves/2/reviews/T-2-0-stubs-reviewer-r1.md`)

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
| 1 of 5 (T-1-2) | no canary planted | 0 so far | 0 | ~25 min build + ~10 min review per round | ~250k build, ~150k per review round |

## Retro
- What slipped: nothing was cut. Four of five cards needed a second round, and every reviewer catch was real:
  - whitespace-only keys passed the production guard;
  - production POs to suppliers with no API were marked submitted;
  - a test's scratch DB name collided between parallel runs;
  - invite mail was sent inside a transaction.
- Lessons added (`team/lessons.md`): commit with an explicit pathspec in a shared index; drizzle re-runs a migration whose journal timestamp changed; never `pnpm install` in a shared repo from a review worktree (a reviewer briefly broke the contracts symlink).

## Follow-ups found during the build (to the backlog at retro)
- `ETSY_WEBHOOK_SECRET` and `env.mocks.etsy` belong in `env.ts`, not in the production-required keys until Etsy approves (T-1-2 reads `process.env` directly for now). Owner: backend-foundation.
- Contract `PO_STATES` lacks `submitting`, so the API shows it as `draft`. Add it as an additive change, plus a web badge. Owner: architect + web-engineer.
- A PO stuck in `submitting` isn't flagged to anyone; it needs an alert. Owner: backend-engineer (inventory).
- Remove the unused `env.mocks.supplier` and `SS_ACTIVEWEAR_*` env keys. Owner: backend-foundation.
- Runbook: an Etsy webhook row, and the new env keys from T-1-1. Owner: docs-writer (B-106).
- The integration gate must run `pnpm db:migrate` (0006–0008) on the dev DB.
- The `user.invited` event needs a `userId` that doesn't exist before the invite is accepted. Change it to `{orgId, invitationId}` (architect). Nothing listens to it yet.
- `settings/vendors.tsx`: map `UPSTREAM_FAILED` to a translated message (web-engineer).
- `pnpm i18n` in invai-web regenerates the catalogs lossily and drops hand-kept keys (web-engineer, B-93).
- No company-language setting: invite emails follow the inviter's `users.locale`, which the web never sets (B-91).
- Reference data (T-1-5 review):
  - Take a Postgres advisory lock around migrate and reference data, because concurrent migrates on a brand-new DB race on `CREATE EXTENSION`.
  - Marks removed from the list are never deleted.
  - Every deploy overwrites hand-edited plan prices; document this in the runbook.
  - Move `PLAN_CATALOG` into a pure `billing/catalog.ts`.
  Owner: backend-foundation.
- Webhooks (T-1-2 review):
  - Give the Shopify mock adapter the same per-adapter `isProd` guard as Etsy's (defense in depth).
  - A delivery row can stay stuck at `received` after an enqueue failure followed by a later crash; the purge job should flag it.
  Owner: integrations-engineer.
- Mailer: add a real send timeout inside `mailer.ts` (the T-1-4 invite flow stops waiting after 15 s, but a late send can still deliver a dead link). Owner: backend-foundation.
- `tenancy/security.test.ts` should call `inviteTeammate` (the full flow) instead of `inviteUser` (first step only). Owner: security-reviewer.
- Invitations: add a unique constraint on pending (organization_id, lower(email)) so a double-click can't send two emails; show "an earlier invite is still pending" in the UI (B-92). Owner: backend-foundation + web-engineer.
- Now that contracts have `submitting`, the backend should return it (`inventory/service.ts:852` maps it to draft). Owner: backend-engineer (inventory).
- The web receive form should send `idempotencyKey` (B-86). Owner: web-engineer.
