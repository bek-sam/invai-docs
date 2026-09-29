# invai-docs/ops

Operational documentation for running InvAI in production: policies, runbooks, SLOs, incidents,
postmortems and cost reports. Owned by `platform-sre` (`invai-docs/team/operating-system.md`,
ownership table); `security-reviewer` co-reviews anything security-flagged.

## What's here today

| File | What it is |
|---|---|
| `incident-response.md` | The written incident-response plan: severities, roles, detection sources, containment steps per incident class, the Amazon/GDPR/Shopify/Etsy notice clocks, evidence handling, postmortem timing. Written for B-10 (T-21-2). |
| `access-control.md` | The written access-control policy: AWS, GitHub, database roles, app roles and permissions, secret storage, access review and offboarding. Written for B-10 (T-21-2). |

## What's planned but not written yet

These folders and files are named by the skills in `.claude/skills/` that will create them. Don't
assume they exist until a task card adds them — check with `ls` first.

| Path | Created by | Purpose |
|---|---|---|
| `incidents/<YYYY-MM-DD>-<slug>.md` | `incident-response` playbook, during a real incident | The live timeline, evidence locations and clock end-times for one incident |
| `postmortems/<YYYY-MM-DD>-<slug>.md` | `postmortem` playbook, within 48 h of an incident resolving | Blameless timeline, impact, contributing causes, action items |
| `alerts.md` | `add-observability` playbook | Every alert: signal, threshold, severity, owner, first commands, runbook link |
| `slos.md` | `define-slo` playbook | The five starting SLOs (API availability, interactive latency, floor scan, label purchase, gang-sheet compose): SLI, target, window, error budget, alerts |
| `restore-drills.md` | `backup-restore-drill` playbook, quarterly | Dated record of each backup/restore drill, RPO/RTO achieved vs. targets |
| `cost-reviews/<YYYY-MM>.md` | `cost-review` playbook, monthly | Cloud, AI and label cost per tenant vs. plan revenue |
| `releases/<version>.md` | `release-checklist` playbook, before every deploy | Frozen SHAs, check results, migration plan, rollback plan, owner go-ahead |

## Reading order

1. `incident-response.md` and `access-control.md` for the written policies.
2. `invai-docs/research/12-security-quality-playbook.md` §5 (incident response) and §1 (security
   checklists) for the rules these policies are built from.
3. `invai-docs/research/11-platform-scale-playbook.md` §5 (observability, SLOs) and §7 (backups,
   cost) for the operational design not yet built.
4. `.claude/skills/incident-response/`, `.claude/skills/postmortem/`, `.claude/skills/define-slo/`,
   `.claude/skills/add-observability/`, `.claude/skills/backup-restore-drill/`,
   `.claude/skills/cost-review/`, `.claude/skills/release-checklist/` for the step-by-step playbooks
   agents actually run — these documents summarize what the playbooks do; the playbooks are the
   source of truth for how.

## Conventions for this folder

- Every claim about the system cites a file (code, config or another doc). A claim with no citation
  is a guess and doesn't belong here.
- Anything only the human owner can do (a real AWS action, sending something outside the team,
  spending, a repo setting) is marked `[[OWNER]]`.
- A step that needs a real AWS account says so plainly, since none is deployed yet
  (`invai-infra/sst.config.ts`: "this environment does not have [AWS credentials]").
- "Not yet" is a real answer for a security questionnaire, not a "yes" — same rule as
  `invai-docs/compliance/vendor-inventory.md`.
