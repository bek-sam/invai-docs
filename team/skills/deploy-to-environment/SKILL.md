---
name: deploy-to-environment
description: Owner-triggered deploy of an InvAI release to an AWS stage (staging or production) with SST. Checks the owner's go-ahead, the release record and the open prerequisites from research 11's gap list, then guides the owner's deploy command, post-deploy checks and rollback. Only the human owner starts this playbook.
disable-model-invocation: true
---

# Deploy to an environment

A release reaches a stage only when the owner said go for that exact version and stage, every blocking
prerequisite is closed or explicitly accepted, and the result is checked and recorded.

## When to use
- The owner invoked this playbook for a named version and stage.
- Never on an agent's own initiative, never as part of another playbook. Agents prepare (`release-checklist`);
  the owner deploys.

## Steps
1. **Confirm the go-ahead.** Find the owner-inbox entry for this version and stage
   (`grep -n "Deploy v" invai-docs/owner-inbox.md`). It must be `status: answered` with a yes for this exact
   stage. No entry or no yes → stop.
2. **Confirm the release record.** `invai-docs/ops/releases/<version>.md` (from `release-checklist`) exists,
   every gate is ticked, and the SHAs still match `git -C <repo> rev-parse origin/main` for all repos.
   Anything moved → back to `release-checklist`.
3. **Check the prerequisites.** Go through `prerequisites.md` (this folder) row by row against the current
   code, and write each row's status into the release record. As of 2026-09-24, **G1 (RLS off in AWS), G2
   (Valkey cluster mode), G3 (no migrate step) and G4 (HTTP only) are open**, so:
   - production: blocked until they are done;
   - staging: allowed only with synthetic data, and only if the owner accepted each open row in the inbox
     entry;
   - any release with a pending migration: blocked until G3 is done (there is no verified way to run
     migrations against RDS yet).
4. **Local checks** (any agent may run these):
   ```
   export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
   cd invai-infra && pnpm install --frozen-lockfile && pnpm typecheck && pnpm lint
   ```
5. **Preview the change** (needs the owner's AWS credentials, so the owner runs it):
   `cd invai-infra && pnpm exec sst diff --stage <stage>`. Read it together: nothing should be replaced or
   removed that holds data (RDS, bucket). Production has `removal: "retain"` and `protect: true`; a planned
   replacement of `Db` or `Files` stops the deploy.
6. **Secrets** (owner): `pnpm exec sst secret list --stage <stage>` shows `BetterAuthSecret` and
   `FieldEncryptionKey` set. Agents never see or type secret values.
7. **Deploy** (owner only; `.claude/hooks/guard-bash.py` blocks agents). One of:
   - from the owner's machine: `! cd invai-infra && pnpm deploy:staging` or `pnpm deploy:prod` (the `!` prefix
     runs it as the owner);
   - through CI, once section B of `prerequisites.md` is done: Actions → Deploy → `workflow_dispatch` with the
     stage, or a `v*` tag push for production.
8. **Check it right away** (agents can help once the owner shares the output URLs `api`, `web`, `floor`):
   ```
   curl -s <api>/health        # ok:true, db:true, redis:true; mocks as expected for the stage
   curl -s -o /dev/null -w '%{http_code}\n' <web>
   curl -s -o /dev/null -w '%{http_code}\n' <floor>
   ```
   Then sign in with a staging test account and open Today, Orders and a gang sheet. On staging with synthetic
   data, the API golden path can run against it:
   `E2E_API_URL=<api> E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` in `invai-web` (only after a synthetic
   seed; never against real shop data).
9. **Watch for 30 minutes.** 5xx rate, p95 latency, job failures, parked outbox events (`define-slo`,
   `add-observability`; until alarms exist, the owner checks CloudWatch service metrics and logs by hand).
10. **Roll back** if the health check fails, the golden path fails, or the SLO fast-burn signal fires:
    redeploy the previous release's SHAs the same way (step 7), following the release record's rollback plan.
    Data problems → `backup-restore-drill` steps and `incident-response`.
11. **Record it.** In the release record: who deployed, when, the stage, the outputs, check results, and any
    rows accepted by the owner. Add an `ops` decision with `record-decision` if a prerequisite was accepted as
    a risk.

## Rules
- MUST NOT start without the owner's answered inbox entry for this exact version and stage.
- MUST NOT run `sst deploy`, `sst remove`, `pnpm deploy:*`, push a `v*` tag or set secrets as an agent. The
  hook blocks these; don't look for a way around it.
- MUST NOT load real shop data into staging or production before section C of `prerequisites.md` is done and
  the owner approved it.
- MUST NOT deploy production while G1 is open: RLS would not protect tenants.
- MUST NOT remove the mock providers; a stage with empty integration secrets runs on mocks by design.

## Done when
- The release record shows the deploy (time, stage, SHAs, operator), every prerequisite row's status, and
  post-deploy check results.
- Health, web and floor URLs returned ok/200, and the 30-minute watch found no rollback signal (or the
  rollback is recorded).
- Accepted risks are recorded as decisions and linked to the inbox entry.

## References
- `prerequisites.md` (this folder)
- `invai-docs/research/11-platform-scale-playbook.md` §0, §4.2, §7, §10
- `invai-docs/build/runbook.md` §7; `invai-infra/sst.config.ts`; `invai-infra/.github/workflows/deploy.yml`;
  `invai-infra/package.json` (`deploy:staging`, `deploy:prod`)
- Related: `release-checklist`, `backup-restore-drill`, `incident-response`, `escalate-to-owner`
