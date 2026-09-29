# Incident response plan

Written policy for B-10 (`invai-docs/waves/backlog.md`), closing research gap G29
(`invai-docs/research/12-security-quality-playbook.md` §7, "Compliance and process"). This is the
written version of the `incident-response` playbook (`.claude/skills/incident-response/SKILL.md`),
which every agent runs during a real incident; this document is what we show Amazon, Shopify,
pilots and counsel as evidence the plan exists. Where the playbook and this document differ, the
playbook governs day-to-day (it is kept current by whoever last ran an incident); update this file
to match at the next `postmortem`.

Nothing here authorizes an agent to send anything outside the team. Every outward message is a
draft the owner sends (`send-owner-draft`, `.claude/skills/incident-response/drafts.md`).

## 1. Severity

| SEV | Meaning | Examples |
|---|---|---|
| 1 | PII or cross-tenant exposure (suspected is enough), a leaked secret with data access, data loss, or every shop blocked | shop B sees shop A's orders; `FIELD_ENCRYPTION_KEY` in a log; RDS data lost; API down for all |
| 2 | One or more shops blocked from shipping or pressing, wrong prints at scale, SLO fast burn | label buying fails for a shop; floor scans return errors; sheets built with the wrong art |
| 3 | Degraded with a workaround | one marketplace sync down (CSV import works); slow screens; a queue backed up but draining |
| 4 | Cosmetic or near miss | wrong label text; an alert that fired with no impact |

Source: `.claude/skills/incident-response/SKILL.md` ("Severity"). Raise severity freely; lower it
only with evidence.

## 2. Roles

| Role | Who | Notes |
|---|---|---|
| Incident commander (IC) | `platform-sre` by default; `tech-lead` for a SEV1 **security** incident | Decides, keeps the timeline, assigns work. The IC never fixes code. Ask the tech lead to run the IC on Opus for a live incident (`.claude/agents/platform-sre.md` role file). |
| Comms | `customer-success` drafts shop messages; `compliance-officer` checks legal wording and clocks | Drafts only — see §5. |
| Scribe | The IC, unless the tech lead names another role | Keeps the timestamped timeline in the incident file (§4). |
| Fixers | The owner of the affected path (`invai-docs/team/operating-system.md`, ownership table), on a card marked `always-in-scope: incident` | **Exception:** in a declared SEV1 security incident, `security-reviewer` may make a minimal fix directly; `reviewer` plus `architect` or `backend-foundation` review it afterwards, before push. |
| **The human owner** `[[OWNER]]` | — | Keeps every outbound message, the Amazon notice, spending, deploys, rollbacks and secret rotation in cloud accounts. Named as InvAI's incident contact (Amazon calls this the Incident Management Point of Contact) — `[[OWNER]]` names the person and the phone/email Amazon and Shopify should reach. |

## 3. Detection sources

No centralized alerting, log store or SLO burn-rate alarms are wired up yet (research gap G30;
`invai-docs/research/11-platform-scale-playbook.md` §5.3 lists the design, `.claude/skills/define-slo/SKILL.md`
and `.claude/skills/add-observability/SKILL.md` own building it). Until then, detection is:

- **A shop report** through `customer-success` (support ticket, `triage-support-ticket`).
- **An agent or reviewer** finding a cross-tenant result, a secret in a log, or a test failure that
  implies one of these (`tenant-isolation-audit`, `dependency-and-container-audit`).
- **In-app alert kinds** already modeled in `invai-contracts/src/schemas/alerts.ts` (`ALERT_KINDS`).
  The ones that indicate an incident, not routine ops noise:
  | Alert kind | Severity in schema | What it means |
  |---|---|---|
  | `queue_failed_spike` | critical | a background queue's failed jobs grew past threshold in 15 min |
  | `outbox_parked` | critical | an outbox event gave up after its retry budget — needs a redrive |
  | `ai_breaker_fail_open` | critical | the AI spend check couldn't reach Valkey and let a call through (a fail-open, research 12 §1.10 "A10: fail closed") |
  | `ai_spend_cap_tenant` / `ai_spend_cap_platform` | critical | a daily AI spend cap was hit — check for a runaway loop or a leaked key before assuming normal usage |
  | `sync_broken` | warning | a marketplace connection failed 30+ minutes — check for a token compromise (§6.5) before assuming an outage |
  | `qc_fail_spike` | warning | a spike in QC failures — can indicate wrong art routed to a shop (a possible tenant leak, §6.2) |
  These alerts are stored per-tenant (`alerts` table, `invai-backend/src/db/schema/tenancy.ts`) and
  read through `alerts.read`; there is no paging or on-call system reading them yet — a human must
  be looking at Today or the alerts list.
- **Planned, not yet built** (research 11 §5.2–5.3, the `define-slo` playbook's starting five SLOs):
  multiwindow burn-rate CloudWatch alarms on API availability, interactive latency, floor scan
  latency, label-purchase job duration and gang-sheet compose time, plus the data-safety alarms
  (parked outbox, backup failure, RDS storage > 85%, Valkey memory > 80%, AI spend breaker). **These
  need AWS** (CloudWatch, an SNS topic, PagerDuty/Opsgenie or equivalent) `[[OWNER]]` — none of it
  can be provisioned or tested without a real account and the owner's go-ahead per `CLAUDE.md`
  ("MUST NOT run `sst deploy`... without the owner's explicit go-ahead").
- **Planned:** centralized 12-month log retention (research 12 §1.10, gap G30) so logs can be
  searched by `company_id`/`request_id`/`trace_id` across API, worker and imaging. Today logs are
  per-process stdout only (`invai-backend/src/lib/log.ts`); in AWS this needs a CloudWatch Logs
  destination `[[OWNER]]`.

## 4. Declare and preserve evidence

1. **T0 = detection time**, with timezone. Create
   `invai-docs/ops/incidents/<YYYY-MM-DD>-<slug>.md` with SEV, IC, T0, what is known, and a
   timeline section. Every action after this gets a timestamped line (this is the file the
   postmortem is built from — `.claude/skills/postmortem/SKILL.md`).
2. **Preserve before changing data:**
   - Deployed SHAs: `git -C <repo> rev-parse origin/main` for each of the 8 repos, plus the release
     record (`invai-docs/ops/releases/<version>.md`, `release-checklist` playbook).
   - Logs for the window. Locally: the terminal output of `pnpm dev:all`. In AWS: exported by
     `[[OWNER]]` — no central log store exists yet (§3).
   - Database, locally:
     `docker exec local-postgres-1 pg_dump -U invai -Fc -d invai -f /tmp/incident-<slug>.dump`.
     In AWS: an RDS snapshot, taken by `[[OWNER]]`.
   - `audit_log` (`invai-backend/src/db/schema/tenancy.ts`) is append-only by design (writes are
     insert-only, per research 12 §1.10) — query it, never copy buyer-PII rows out of it into the
     incident file.
3. **Never** delete data, logs or audit rows to contain an incident, and never rewrite pushed git
   history (`CLAUDE.md`, `.claude/hooks/guard-bash.py` blocks force-push and history rewrites).

## 5. Tell the owner and start the legal clocks

Within 15 minutes for SEV1–2: an `escalate-to-owner` entry (`invai-docs/owner-inbox.md`) using the
"Owner brief" template in `.claude/skills/incident-response/drafts.md`. For SEV1, or any possible
PII exposure, the entry states these clocks (source: research 12 §5, §2.1):

| Clock | Deadline | Who acts | Template |
|---|---|---|---|
| **Amazon security notice** | Within **24 hours of T0** — sent by the owner as the named Incident Management Point of Contact `[[OWNER]]`, to `security@amazon.com` | `[[OWNER]]` sends; an agent drafts | `.claude/skills/incident-response/drafts.md` §2 |
| **Shop notice (we are the shops' processor/controller-adjacent party)** | Within 24 hours, so each shop can meet its own GDPR 72-hour deadline | `[[OWNER]]` sends; `customer-success` + `compliance-officer` draft | `.claude/skills/incident-response/drafts.md` (shop notice, en/es) |
| **GDPR breach notice (buyer-facing, via the shop)** | 72 hours from the shop's own awareness — our 24-hour notice to the shop exists to leave them room inside that window | `[[OWNER]]` via the shop | research 12 §2.4 |
| **Shopify** | Per the Shopify Partner terms; `compliance-officer` checks the current wording (`policy-change-watch`) before drafting | `[[OWNER]]` sends | — |
| **Etsy** | No Etsy-specific breach-notice clause is recorded yet in our compliance docs; treat it the same as the Shopify path (notify within 24 h) until `compliance-officer` finds Etsy's actual policy text, and record it as a decision when found | `[[OWNER]]` sends | — |
| **US state breach laws** | Per state — a lawyer's call | `[[OWNER]]` via counsel | `legal-doc-draft` playbook |

**MUST NOT** wait for certainty before telling the owner about *possible* PII exposure — the
24-hour clock runs from detection (T0), not from confirmation
(`.claude/skills/incident-response/SKILL.md` rule).

## 6. Containment steps by class

Containment is the smallest action that stops the harm, done inside the agent's own owned paths
or through the API as the right role. Nothing here is a real cloud action unless marked `[[OWNER]]`
or "needs AWS".

### 6.1 Key leak (a secret in a log, a commit, or a leaked env value)
1. Identify which secret and its blast radius using the table in §2 of `access-control.md`
   (`invai-docs/ops/access-control.md`).
2. `FIELD_ENCRYPTION_KEY`: rotate by **prepending** a new key
   (`k2:<base64 32 bytes>,k1:<base64 32 bytes>`) — old ciphertext still decrypts with the old key
   in the list (`invai-docs/build/runbook.md` §2, `invai-infra/sst.config.ts` `fieldEncryptionKey`
   secret). **Needs AWS** in production (`sst secret set FieldEncryptionKey <new> --stage <stage>`,
   then a redeploy) — `[[OWNER]]`.
3. `BETTER_AUTH_SECRET`: rotating it signs every web session out at once
   (`invai-backend/src/env.ts` `BETTER_AUTH_SECRET`). **Needs AWS**: `sst secret set
   BetterAuthSecret <new> --stage <stage>` — `[[OWNER]]`.
4. Provider keys (`ANTHROPIC_API_KEY`, `EASYPOST_API_KEY`, `SHOPIFY_API_KEY`/`SHOPIFY_API_SECRET`,
   `STRIPE_SECRET_KEY`): rotate at the provider's dashboard, then `sst secret set <Name> <new>
   --stage <stage>` — `[[OWNER]]` for both the provider console and the AWS secret. Until rotated,
   the platform runs on the mock provider for that integration by design
   (`invai-backend/src/env.ts` `mocks.*`), which is the safe fallback, not a bug.
5. `INTERNAL_ADMIN_TOKEN` (the DLQ/redrive operator token, `invai-backend/src/env.ts`): rotate the
   same way; while unset, the internal admin routes 404 by design.
6. **GitHub deploy keys / OIDC role** (see `access-control.md` §2 for the list): revoke and reissue
   the affected repo's deploy key in GitHub Settings, or (for the OIDC role) tighten or rotate the
   trust policy in IAM — `[[OWNER]]` (repo and AWS account settings).

### 6.2 Tenant leak (cross-tenant data returned, or a shop sees another shop's rows)
1. Reproduce locally first if possible: call the procedure as the affected role with the
   suspect id, on your own API port (`PORT=31xx pnpm dev:api`), and confirm the response shape.
2. Check whether the path used `withTenant` or `withSystem` (`invai-backend/src/db/client.ts`
   pattern named in `CLAUDE.md`); an unjustified `withSystem` call or a view/function that bypasses
   RLS is the likely cause (research 12 §1.1).
3. If a specific connection or job is the source, disable it: `channels.disconnect` (permission
   `channels.manage`, `invai-contracts/src/contract/channels.ts:50`) stops further sync from that
   connection without deleting data.
4. Query the audit log for the affected window (§4) to find which companies' data was returned to
   which session, using company-id counts only, never copying buyer rows into the incident file.
5. The fix is a card for the owning role, reviewed by `security-reviewer` (mandatory co-review for
   any `tenancy` risk flag, `invai-docs/team/operating-system.md`), never a workaround that turns
   off RLS or weakens a test.

### 6.3 PII exposure (buyer data in the wrong place: logs, prompts, a public link, another tenant)
1. **Logs:** no redaction layer exists yet in `invai-backend/src/lib/log.ts` (research 12 §1.10,
   gap G7) — search the captured log output for the specific fields at risk
   (`grep -Ei "<pattern>"`), scoped to your own terminal capture; never paste real buyer PII into
   the incident file, chat or a draft (`scrub-pii-fixture` rule).
2. **AI prompts:** buyer text is meant to be scrubbed before any provider call (`stripPiiDeep`,
   research 12 §1.9) — if scrubbing failed, that call's `promptRef` log line identifies the route
   and tenant without needing the payload itself.
3. **A public link (a presigned URL or an S3 object served without auth):** the object key follows
   `isCompanyKey()` (research 12 §1.1) — if a key was guessed or shared, the file bucket's signed
   URLs expire on their own; for anything already fetched, treat it as exposed and count it in the
   owner brief.
4. Same 24-hour/72-hour clocks as §5 apply the moment PII exposure is *suspected*.

### 6.4 Payment or label runaway (labels bought repeatedly, an AI spend spike, a billing loop)
1. Labels: check `shipping.buy`/`shipping.manage` calls in the audit log for the affected company
   and window; the carrier adapter is mocked today unless `EASYPOST_API_KEY` is set
   (`invai-backend/src/env.ts` `mocks.carrier`) — a runaway against the mock costs nothing but still
   indicates a bug to fix.
2. AI spend: the `ai_spend_cap_tenant` / `ai_spend_cap_platform` / `ai_breaker_fail_open` alerts
   (§3) are the detection signal. Per-tenant and platform daily caps already exist
   (`AI_DAILY_TENANT_CAP_CENTS`, `AI_DAILY_PLATFORM_CAP_CENTS`, `invai-backend/src/env.ts`) and
   pause the feature at zero; `ai_breaker_fail_open` means the check itself failed open — treat
   that as the incident, not just the spend.
3. Billing (Stripe) is stubbed, not live (`invai-backend/src/modules/billing/service.ts`, research
   12 gap G12) — a "runaway" here today can only be a code bug, not a real charge; once Stripe is
   live this section needs updating with webhook idempotency on `event.id` (research 12 §1.8).
4. Contain by disabling the specific integration for the affected tenant (`channels.disconnect` for
   a channel; the AI credit ledger already blocks at zero) rather than a platform-wide kill switch,
   unless the spike is platform-wide.

### 6.5 Marketplace token compromise (a connection's OAuth token or webhook secret leaked or misused)
1. Disconnect the connection: `channels.disconnect` (`channels.manage`,
   `invai-contracts/src/contract/channels.ts:50`) — this is reachable by any agent signed in as
   `office`/`admin`/`owner` for that tenant and needs no AWS access.
2. If the leak is platform-wide (InvAI's own Shopify Partner app credentials, not one shop's
   token): rotate `ShopifyApiKey`/`ShopifyApiSecret` at the Shopify Partner dashboard, then `sst
   secret set` for both — `[[OWNER]]` (see §6.1 step 4).
3. Webhook secrets: `EASYPOST_WEBHOOK_SECRET`, and per-channel webhook HMAC secrets, are verified
   on the raw body before any work happens (research 12 §1.8); a compromised secret means an
   attacker could forge deliveries — rotate at the provider, then the SST secret, `[[OWNER]]`.
4. Every floor station token is separate from marketplace tokens: see `access-control.md` §3 for
   station token revocation, which is a different containment path (a floor/production incident,
   not a marketplace one).

## 7. Communicate

Update the owner at least every 60 minutes for SEV1, every 2 hours for SEV2, and at every status
change, using the "Owner brief" template (`.claude/skills/incident-response/drafts.md`). All outward
text — to shops, Amazon, Shopify, Etsy or counsel — is a draft queued with `send-owner-draft`; no
agent sends, posts or replies outside the team (`CLAUDE.md`, `escalate-to-owner` rules).

## 8. Fix and resolve

- The IC asks the tech lead for a card marked `always-in-scope: incident`; the IC does not write the
  fix (§2).
- Every fix gets an independent review (`independent-review`); a security fix also gets
  `security-reviewer` plus `architect` or `backend-foundation` (research 13 §6.3, cited by the
  playbook).
- Vulnerability fix clocks, from the day the issue is known: **Critical ≤ 7 days, High ≤ 30 days**
  (research 12 §1.5, the Amazon DPP clock) — record the due date in
  `invai-docs/security/v1-review.md` (owned by `security-reviewer`, T-21-3).
- Resolve when impact has stopped, the fix is verified (`verify-and-report`, plus
  `run-golden-path` for a golden-path area), and every affected shop is listed by count in the
  incident file.

## 9. Postmortem

Every incident gets a blameless postmortem within **48 hours** of `resolved`
(`.claude/skills/postmortem/SKILL.md`), filed at
`invai-docs/ops/postmortems/<YYYY-MM-DD>-<slug>.md`. It feeds `log-lesson`
(`invai-docs/team/lessons.md`), new findings into `invai-docs/security/v1-review.md`, and any
lasting rule into `record-decision`.

## 10. Yearly tabletop exercise

Research 12 §5 calls for a yearly tabletop, for example "a floor station token leaked" or "a webhook
routed to the wrong tenant". None has been run yet — `[[OWNER]]` to schedule the first one before
the SP-API application (this is a process gap, not an AWS one; it needs no cloud access, just time
on the calendar).

## References

- `.claude/skills/incident-response/SKILL.md` and `.claude/skills/incident-response/drafts.md` (the
  live playbook and message templates this document summarizes)
- `invai-docs/research/12-security-quality-playbook.md` §5 (clocks and roles), §1.10 (audit
  logging and alerts), §2.1 (Amazon DPP), §2.4 (GDPR)
- `invai-docs/research/11-platform-scale-playbook.md` §5.2–5.3 (SLOs and burn-rate alerts, not yet
  built), §7.2 (data-safety alarms)
- `invai-contracts/src/schemas/alerts.ts` (`ALERT_KINDS`)
- `invai-backend/src/env.ts` (secrets and mock flags), `invai-infra/sst.config.ts` (SST secrets)
- `invai-docs/build/runbook.md` §2 (key rotation)
- `invai-docs/ops/access-control.md` (roles, secret storage, offboarding)
