---
name: backup-restore-drill
description: Prove InvAI data can be restored — restore a Postgres backup into a fresh database, check counts, RLS and roles, boot the API on it, sign in, and record real RPO/RTO against the ≤5 min / ≤4 h targets. Local drill any time; the AWS point-in-time drill runs quarterly with the owner. Use for quarterly drills, before a pilot or SP-API application, and after backup changes.
---

# Backup restore drill

We know, with a timed and recorded run, that a backup turns back into a working InvAI with tenants still
isolated, and how long that takes.

## When to use
- Every quarter (research 11 rule 12; "an untested backup is not a backup").
- Before the first pilot on AWS and before the Amazon SP-API application (evidence).
- After changing backup retention, the RDS instance, migrations tooling or `local/init.sql`.
- Practice before an incident, so the steps aren't new under pressure.

## Targets (research 11 §7.2, stage "now")
- RPO ≤ 5 minutes (RDS point-in-time recovery).
- RTO ≤ 4 hours (restore to a new instance, repoint through SST).
- Valkey is rebuildable: jobs lost with it are re-driven from the outbox (script to be created, research 11
  §3.3).

## Steps: local drill (any agent; about 5 minutes)
Proves the dump/restore path, grants, RLS and the app. Run from the workspace root.
1. **Start the clock** and note the time. Check infra is healthy: `docker ps | grep local-postgres-1`.
2. **Take a backup** of the dev DB (read-only for others):
   ```
   docker exec local-postgres-1 pg_dump -U invai -Fc -d invai -f /tmp/drill.dump
   ```
3. **Restore into a new database:**
   ```
   docker exec local-postgres-1 createdb -U invai invai_restore_drill
   docker exec local-postgres-1 pg_restore -U invai -d invai_restore_drill --no-owner --role=invai /tmp/drill.dump
   ```
4. **Compare data.** The same query on both databases must match:
   ```
   for d in invai invai_restore_drill; do docker exec -i local-postgres-1 psql -U invai -d $d -Atc \
     "select (select count(*) from orders), (select count(*) from order_items), (select count(*) from audit_log), (select count(*) from pg_tables where schemaname='public' and rowsecurity)"; done
   ```
5. **Check isolation survived** the restore:
   ```
   docker exec -i local-postgres-1 psql -U invai -d invai_restore_drill -v ON_ERROR_STOP=1 < .claude/skills/tenant-isolation-audit/audit.sql
   ```
   Same expected results as `tenant-isolation-audit`.
6. **Boot the API on it** and sign in (own port, not 3000):
   ```
   export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
   cd invai-backend
   DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_restore_drill \
   MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_restore_drill \
   PORT=3190 pnpm exec tsx src/api/server.ts &
   curl -s localhost:3190/health                     # "ok":true,"db":true
   curl -s -H 'Content-Type: application/json' -H 'Origin: http://localhost:5173' \
     -d '{"email":"owner@desertbloom.test","password":"demo1234!"}' localhost:3190/api/auth/sign-in/email
   ```
   The sign-in returns the owner user. Stop the clock: that's the local RTO.
7. **Clean up:** stop the API (`lsof -iTCP:3190 -sTCP:LISTEN` → kill), then
   `docker exec local-postgres-1 dropdb -U invai --force invai_restore_drill && docker exec local-postgres-1 rm /tmp/drill.dump`.

## Steps: AWS point-in-time drill (quarterly, with the owner)
Real cloud accounts and a temporary instance cost money, so this is an `escalate-to-owner` entry first; the
owner runs the AWS commands.
1. Confirm the settings: backup retention (target 14 d staging, 35 d production; today the SST default is 7 d,
   research 11 G5), deletion protection, encryption, cross-region copy (Amazon wants geo-dispersed backups,
   research 12 §2.1).
2. The owner restores to a new instance at a chosen time in the window (RDS console or
   `aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier <id> --target-db-instance-identifier invai-drill-<date> --restore-time <ISO>`,
   with the stage's subnet group and security group). Note start and ready times.
3. Reach it through the VPC (`cd invai-infra && pnpm exec sst tunnel --stage <stage>`, owner) and run steps
   4–5 of the local drill against it. On staging only, boot the backend against it as in step 6.
4. The owner deletes the drill instance. Nothing from it is copied to a laptop if it holds real data.

## Record
Append to `invai-docs/ops/restore-drills.md` (to be created, platform-sre):
```
## <YYYY-MM-DD> <local | staging | production> drill
- Backup: <dump / PITR to time T>. Data loss window (RPO): <minutes>
- Restore time (RTO): <start → API healthy, minutes>
- Checks: counts match <yes/no>; audit.sql clean <yes/no>; health <ok>; sign-in <ok>
- Problems and fixes: <cards>
- Run by: <role> (+ owner for AWS)
```
Also state in the record that PII purged from the live DB still exists in backups until retention expires (up
to 35 days in production), matching what the DPA says (research 11 §7.2, research 12 §2.7).

## Rules
- MUST restore into a new database or instance, never over the live one.
- MUST NOT copy production or real-shop backups to a local machine or staging.
- MUST NOT run AWS restores, snapshots or deletions as an agent; the owner does (real account, cost).
- MUST time the drill from start to a healthy, signed-in API. A restore that "finished" but can't serve
  requests has no RTO yet.

## Done when
- Counts match, `audit.sql` is clean on the restored DB, the API health is ok and sign-in works.
- `invai-docs/ops/restore-drills.md` has the dated entry with RPO and RTO, compared with the targets.
- Temp databases, instances, dumps and processes are gone.
- Gaps (retention, cross-region copy, re-drive script) have cards.

## References
- `invai-docs/research/11-platform-scale-playbook.md` §3.3 (outbox re-drive), §7.2 (RPO/RTO, quarterly drill),
  G5
- `invai-docs/research/12-security-quality-playbook.md` §2.1, §2.6 (backups with restore evidence), §2.7
- `invai-infra/scripts/reset-db.sh`, `invai-infra/local/init.sql` (roles a restore must keep)
- Related: `tenant-isolation-audit`, `incident-response`, `deploy-to-environment`
