---
name: triage-support-ticket
description: Triage an InvAI support ticket or pilot problem - severity (S1 blocks shipping > S2 wrong print > S3 staff time > S4 annoyance), reproduction on the seed stack, owner role, workaround, macro reply draft (en/es) and issue-log entry. Use when a shop reports a problem, a dry run or audit finds one, or someone says "ticket", "bug from a shop" or "support".
---

# Triage a support ticket

Every shop problem gets a severity, a reproduction, an owner, a workaround and a reply draft, fast enough that
no shop misses a ship-by because we were slow to look.

## When to use
- The owner forwards a shop's message, call note or screenshot.
- `import-dry-run`, `onboard-shop`, `ux-audit` or a usability session finds a product problem.
- A metric alarm points at one shop (late items piling up, scans blocked).

## Severity (pick the highest that applies)
| Sev | Means | Examples | Target: workaround to the owner | Target: fix |
|---|---|---|---|---|
| **S1 blocks shipping** | Orders can't move toward a label today, or tracking doesn't reach the marketplace | Import fails for a channel; labels can't be bought; floor can't log in or scan; tracking push failing; ship-by computed late | Within 1 hour of triage (and before the shop's carrier pickup) | Current wave, as a bug card; the tech lead is told now |
| **S2 wrong print** | A shirt could be pressed or shipped wrong | Wrong design or size passes the press check; personalization text read wrong or cut off; wrong transfer on a sheet; pack completes with a missing item | Same business day | Current or next wave, as a bug |
| **S3 staff time** | Work gets done but costs extra minutes or steps | Slow bulk mapping; confusing screen; Spanish missing on a floor step; manual workaround every day | 2 business days | Ranked by `prioritize-backlog` |
| **S4 annoyance** | Cosmetic or rare, no time lost | Label typo; odd sort order | Weekly batch | Backlog |

**Escalate beyond severity:**
- More than one shop hit, a platform outage, or data at risk: start `incident-response` (platform-sre leads).
- Any suspected buyer-data exposure: `escalate-to-owner` immediately, with Amazon's 24-hour notice clock
  stated.

Targets are ours, for pilots; set them to what the owner and team can actually meet, and revisit in the weekly
update.

## Steps
1. **Capture the ticket** without PII: the shop slug, the date and time (shop's time zone), role, screen or
   station, what they tried, what happened, what they expected, how many orders or items are affected, and the
   ship-by of the oldest affected order. Screenshots: blur or crop names and addresses before saving.
2. **Set severity** from the table. When unsure between two, pick the higher and say why.
3. **Check it's known.** Search `invai-docs/customers/issues.md` (created on first use by this playbook) and `invai-docs/waves/backlog.md` for the
   same symptom. If found, add this shop and date to that issue (the count matters for ranking) and reuse its
   workaround.
4. **Reproduce on the seed stack** (Desert Bloom Tees, the matching demo login or PIN), or on the isolated
   stack from `import-dry-run` if it needs the shop's data. Write exact steps. If it doesn't reproduce, list
   what differs (data, role, device, offline, browser) and ask for one missing fact through the owner.
5. **Classify:** product wrong (bug), needs training (it works; the shop didn't know how), or unusual data.
   Only "product wrong" goes to engineering.
6. **Find the owner role** from the layer (operating system table): a CSV or marketplace adapter →
   integrations-engineer; module logic → backend-engineer (name the area); a screen → web-engineer; a tablet
   flow → floor-engineer; a sheet or render → imaging-engineer; AI drafts or trademark → ai-engineer; a shared
   component → product-designer. When the layer isn't clear, ask the qa-engineer for `root-cause-bug`.
7. **Find a workaround** the shop can use today: a hold, a manual SKU map, a re-import, printing the label PDF
   again, reprinting from QC, or the old process for that channel. S1 and S2 must have one, or the owner is
   told there is none.
8. **Log it** in `invai-docs/customers/issues.md` with the entry format in `macros.md`. Id: `ISS-<n>`, the
   next number.
9. **Draft the reply** from a macro in `invai-docs/customers/macros/` (created on first use by this playbook;
   starter set in `macros.md`), in the shop's language, and put it in the owner inbox with `send-owner-draft`. Say what happened, what to do now,
   and when we'll update. No blame, no promised dates beyond the next update.
10. **Hand off.** S1 and S2: tell the tech lead now, with the issue id and repro, for a bug card. S3 and S4:
    they reach the PM's next ranking. Training fixes: ask the docs-writer for a `write-help-article`.
11. **Close the loop.** When the fix is pushed, re-test the repro, update the issue status, and draft the
    "fixed" message for the owner.

## Rules
- MUST triage S1 before any other work, and state the affected ship-by times.
- MUST keep buyer names, addresses, emails and order notes out of the log, the macros and screenshots
  (`scrub-pii-fixture`).
- MUST separate "product wrong" from "training" from "unusual data". Don't file a bug for a training gap.
- MUST NOT reply to the shop. Every reply is a draft for the owner.
- MUST NOT promise a fix date. Say when the next update comes.
- MUST NOT edit code or data to "fix" a shop. Workarounds are things the shop does in the app.

## Done when
- An `ISS-<n>` entry has severity, repro steps (or what's missing), class, owner role, workaround, affected
  count and status.
- A reply draft (en or es) is in the owner inbox.
- S1 and S2: the tech lead was told, with the time recorded. Incidents and PII suspicions went through
  `incident-response` or `escalate-to-owner`.

## References
- `macros.md` (this folder: issue entry format and starter macros)
- `.claude/agents/customer-success.md`
- `invai-docs/team/operating-system.md` (roles and owned paths)
- Severity and response practice: [Jitbit priority
  levels](https://www.jitbit.com/news/helpdesk-ticket-priority-levels/), [Rootly support
  levels](https://rootly.com/incident-response/support-levels) (checked 2026-09-24)
- Related playbooks: `root-cause-bug`, `incident-response`, `send-owner-draft`, `write-help-article`,
  `scrub-pii-fixture`
