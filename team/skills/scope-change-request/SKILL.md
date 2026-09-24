---
name: scope-change-request
description: File or decide a request to add, cut or change something in InvAI's MVP scope (invai-docs/product/scope.md). Anyone files; the PM decides; cost, risk or beyond-MVP changes go to the owner. Use when work is asked for that isn't in scope.md, or when scope must be cut.
---

# Scope change request

No one builds outside `product/scope.md`, and every change to it is written down with evidence, a decision and
a changelog line.

## When to use
- A task, pilot issue or idea needs something `scope.md` doesn't include.
- A pilot or metric shows something in scope isn't worth building (a cut).
- A wave is running late and something must move out.
- A reviewer blocks a card for scope creep.

Not needed for "always in scope" work: bugs, security findings, incidents and compliance deadlines.

## Steps (filer: any role)
1. **Check it's really out of scope.** Read `invai-docs/product/scope.md`, `invai-docs/decisions/`
   (`0006-v1-cuts.md` lists the v1 cuts). If a logged decision already cut it, you need new evidence, not just
   a new request.
2. **Get the next number:** `ls invai-docs/product/scope-changes/ 2>/dev/null | sort | tail -1`. Start at
   `SCR-001`.
3. **Write the request** in `invai-docs/product/scope-changes/SCR-NNN-<slug>.md` using the template below.
   Non-PM roles don't own that folder: put the text in your task report or wave file and ask the PM to file
   it.
4. **Tell the PM** in your report. Keep working on in-scope work meanwhile. Never build the change "just in
   case".

## Steps (decider: product-manager)
5. **Check the evidence.** Is there a pilot issue, a ranked pain, or a metric? How many shops (small, mid,
   large)? One shop's quirk gets "not now" unless it blocks shipping.
6. **Size it with the tech lead:** effort in wave cards, and any contract change, migration, new outside
   service or cost.
7. **Decide one of:**
   - **Accept:** edit `scope.md` (in-list plus changelog line), then run `write-spec`.
   - **Accept with a smaller cut:** say exactly which part.
   - **Defer:** add it to the "later" list in `scope.md` with a trigger ("when 2 pilots ask", "after Etsy
     approval").
   - **Reject:** one-line reason.
8. **Send it to the owner instead of deciding** (`escalate-to-owner`) when any of these is true:
   - it goes beyond the MVP,
   - it adds spending: a new paid service, more AI or label cost, hardware,
   - it changes pricing, plan limits or what a plan includes,
   - it reopens a logged decision, such as AI design generation (cut for IP risk) or direct Amazon SP-API
     (deferred),
   - it adds risk: IP, buyer PII, a marketplace policy, or security.
   Use the `OI-<n>` entry format in `owner-inbox.md`: 2–3 options, your recommendation, the cost of waiting, a
   deadline and the default if there's no answer.
9. **Record it.** A product decision that changes direction gets a decision record through `record-decision`
   (type: product). Fill in the request's "Decision" block and date.
10. **Tell the filer and the tech lead** so the backlog and cards match.

## Template
```
# SCR-NNN: <title>
Filed by: <role>  Date: YYYY-MM-DD  Type: add | cut | change
Scope section affected: scope.md#<anchor>
## Request
What, in one paragraph.
## Why (evidence)
Issue ids, research section, metric, who asked (shop segment, never a real name).
## Who it helps
Small / mid / large; roles.
## Cost and risk
Effort (cards), new services or spend, security, marketplace policy, IP.
## If we don't
What happens to shops.
## Decision
Accepted | accepted smaller | deferred (trigger) | rejected | sent to owner (inbox id)
Reason:  Decided by:  Date:
```

## Rules
- MUST get an SCR before any out-of-scope work begins, even small work.
- MUST go to the owner for anything beyond the MVP or touching cost, pricing or risk. The PM decides the rest.
- MUST add a changelog line to `scope.md` for every accepted change or cut.
- MUST NOT let a role other than the PM edit `scope.md`.
- MUST NOT name real shops or buyers. Use the segment and a customer-folder slug.

## Done when
- `product/scope-changes/SCR-NNN-<slug>.md` exists with the decision block filled in.
- Accepted: `scope.md` and its changelog updated, and a spec started or queued.
- Sent to owner: the inbox entry id is in the SCR.
- The filer and tech lead were told.

## References
- `invai-docs/team/operating-system.md` (owner rule 6, "Escalate to the owner")
- `invai-docs/research/13-team-gap-analysis.md` §6.5 (how scope is recorded)
- `invai-docs/product/scope.md`, `invai-docs/decisions/0006-v1-cuts.md`
- Related playbooks: `write-spec`, `prioritize-backlog`, `record-decision`, `escalate-to-owner`
