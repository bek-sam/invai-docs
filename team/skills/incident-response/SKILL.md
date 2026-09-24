---
name: incident-response
description: Run an InvAI incident — set severity (SEV1 = PII or cross-tenant exposure), name an incident commander, tell the owner at once with Amazon's 24-hour notice clock, contain, preserve evidence, find affected shops, draft owner-sent notices, track 7/30-day fix clocks, start the postmortem. Use for outages, shops blocked from shipping or pressing, data leaks, or leaked secrets.
---

# Incident response

Shops are protected first, the owner knows within minutes with every legal clock written down, evidence
survives, and nothing leaves the team without the owner.

## When to use
- An SLO fast-burn page or data-safety alarm (`define-slo`, `invai-docs/ops/alerts.md`).
- A shop can't import, press, pack or buy labels, or got wrong prints.
- Any sign of cross-tenant access, buyer PII in the wrong place (logs, prompts, another shop, a public link),
  a leaked key or token, or real PII found in a repo.
- A High security finding with evidence that it was reachable.

## Severity (pick the highest that fits; raise it freely, lower it only with evidence)
| SEV | Meaning | Examples |
|---|---|---|
| 1 | PII or cross-tenant exposure (suspected is enough), leaked secret with data access, data loss, or every shop blocked | shop B sees shop A's orders; `FIELD_ENCRYPTION_KEY` in a log; RDS data lost; API down for all |
| 2 | One or more shops blocked from shipping or pressing, wrong prints at scale, SLO fast burn | label buying fails for a shop; floor scans return errors; sheets built with the wrong art |
| 3 | Degraded with a workaround | one marketplace sync down (CSV import works); slow screens; a queue backed up but draining |
| 4 | Cosmetic or near miss | wrong label text; an alert that fired with no impact |
This follows the support order: blocks shipping > wrong print > staff time > annoyance.

## Roles
- **Incident commander (IC):** platform-sre by default (ask the tech lead to run it on Opus); the tech-lead
  for SEV1 security incidents. The IC decides, keeps the timeline and assigns work. The IC never fixes code.
- **Comms:** customer-success drafts shop messages; compliance-officer checks legal clocks and wording.
- **Scribe:** the IC, unless the tech lead names another role.
- **Fixers:** the owners of the affected paths (`respect-ownership`), with a normal card marked
  `always-in-scope: incident`. **Exception (declared High incident, i.e. a SEV1 security incident):** the
  security-reviewer may make a minimal fix directly; it is reviewed afterwards by `reviewer` plus architect or
  backend-foundation, before it is pushed.
- **The human owner** keeps every outbound message, the Amazon notice, spending, deploys, rollbacks and secret
  rotation in cloud accounts.

## Steps
1. **Declare (minute 0).** Write down T0 = detection time with timezone. Create
   `invai-docs/ops/incidents/<YYYY-MM-DD>-<slug>.md` (folder to be created) with: SEV, IC, T0, what we know,
   and a timeline section. Every action from now on gets a timestamped line.
2. **Tell the owner (within 15 minutes for SEV1–2).** `escalate-to-owner` entry with the owner brief from
   `drafts.md`. For SEV1, or any possible PII exposure, write the clocks into the entry:
   - **Amazon: security@amazon.com within 24 h of T0** (ends <T0+24h>), sent by the owner as the named
     incident contact.
   - **Shops (our controllers): within 24 h**, so each can meet GDPR's 72 h.
   - Shopify and other partners: per their terms (compliance-officer checks). US state breach laws: per state
     (lawyer).
3. **Contain,** smallest action that stops the harm, inside your authority:
   - a floor token: revoke the station in Settings → Stations (`stations.revokeToken`); re-pair tablets
     afterwards;
   - a staff account: `team.deactivate` (ends floor sessions at once);
   - a marketplace connection sending bad data: disconnect it in Settings → Channels (`channels.disconnect`);
   - a bad release: the owner rolls back (`deploy-to-environment` step 10);
   - a leaked secret: the owner rotates it (`sst secret set <Name> <new> --stage <stage>`).
     `FIELD_ENCRYPTION_KEY` rotates by prepending a key (`k2:<base64>,k1:<base64>`, runbook §2) so old data
     still decrypts; rotating `BETTER_AUTH_SECRET` signs everyone out;
   - locally, reproduce on your own API port first when you can.
   Never delete data, logs or audit rows to contain.
4. **Preserve evidence before changing data.**
   - Deployed SHAs: `git -C <repo> rev-parse origin/main` for each repo, plus the release record.
   - Logs for the window (API, worker, imaging). In AWS the owner exports them; there is no central log store
     yet (research 12 G30).
   - Database: locally
     `docker exec local-postgres-1 pg_dump -U invai -Fc -d invai -f /tmp/incident-<slug>.dump`; in AWS the
     owner takes an RDS snapshot.
   - `audit_log` is append-only by design; query it, don't copy PII out of it.
5. **Find who is affected.** Locally:
   `docker exec -i local-postgres-1 psql -U invai -d invai -v t1='<start ISO>' -v t2='<end ISO>'`, then paste
   the queries. In AWS only with the owner's go-ahead.
   ```sql
   -- actions per shop in the window
   select company_id, action, count(*) from audit_log
   where created_at between :'t1' and :'t2' group by 1, 2 order by 1, 3 desc;
   -- failed jobs per shop
   select company_id, kind, count(*) from jobs where status = 'failed'
     and created_at between :'t1' and :'t2' group by 1, 2;
   -- outbox events stuck or parked
   select company_id, name, count(*) filter (where dispatched_at is null) pending,
          count(*) filter (where last_error is not null and attempts >= 10) parked
   from outbox_events where created_at between :'t1' and :'t2' group by 1, 2;
   ```
   Map ids to shop names with `select id, name from companies where id in (…)`. Record counts, never buyer
   rows.
6. **Communicate.** Fill the drafts in `drafts.md` and queue them with `send-owner-draft`. Update the owner at
   least every 60 minutes for SEV1, every 2 hours for SEV2, and at every status change.
7. **Fix.** The IC asks the tech lead for a card (`always-in-scope: incident`); the IC doesn't write the fix.
   The fix still gets an independent review; for a security fix the reviewer plus architect or
   backend-foundation co-review (research 13 §6.3). In a SEV1 security incident the security-reviewer may fix
   directly (the exception under "Roles"), and that review happens afterwards, before push. Vulnerability fix clocks from the day it's known: **Critical ≤ 7 days, High ≤ 30
   days**; record the due date in `invai-docs/security/v1-review.md`.
8. **Resolve.** The impact has stopped, the fix is verified (`verify-and-report`, `run-golden-path` if a
   golden-path area), and every affected shop is listed. Set status `resolved` with the time.
9. **Hand off to `postmortem`** within 48 hours, for every incident.

## Rules
- MUST NOT send, post or reply to anyone outside the team. Drafts only; the owner sends.
- MUST NOT wait for certainty before telling the owner about possible PII exposure. The 24-hour clock runs
  from detection.
- MUST NOT delete, rewrite or "clean up" evidence (logs, audit rows, snapshots, git history) during an
  incident.
- MUST NOT copy buyer PII into the incident file, drafts, chat or prompts. Use counts and ids.
- MUST NOT weaken a control to restore service (for example turning off RLS or signature checks). Propose a
  safer option to the owner.

## Done when
- The incident file has SEV, IC, T0, a timestamped timeline, affected shops (counts), containment, evidence
  locations and the clock end times.
- The owner-inbox entry exists, with the Amazon and shop clocks stated for any PII case.
- Drafts are queued for the owner; fix cards exist with 7/30-day due dates where they apply.
- Status is `resolved` and the postmortem is scheduled within 48 hours.

## References
- `drafts.md` (this folder): owner brief, Amazon notice, shop notice en/es, status update
- `invai-docs/research/12-security-quality-playbook.md` §5 (roles, clocks, runbook steps), §2.1 (Amazon DPP
  table), §2.4 (GDPR breach notice)
- `invai-docs/research/11-platform-scale-playbook.md` §5.4
- `invai-docs/build/runbook.md` §2 (key rotation), §6 (troubleshooting)
- Related: `escalate-to-owner`, `send-owner-draft`, `postmortem`, `tenant-isolation-audit`
