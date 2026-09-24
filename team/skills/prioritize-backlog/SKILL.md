---
name: prioritize-backlog
description: Rank InvAI's backlog by pain impact, shops affected, effort, risk and outside-approval dependency, and pick at most 5 items for the next wave. Use before each wave, after new pilot feedback or a metrics review, or when asked to "rank", "prioritize" or "what next".
---

# Prioritize the backlog

The tech lead gets a ranked list with a written reason for every position, and the next wave holds at most 5
items that are all in scope and all have specs.

## When to use
- Wave step 1 (Scope), before the tech lead writes `waves/<n>/wave.md`.
- After a weekly customer update, a weekly metrics review or an incident changes what matters.
- When the owner asks "what's next?".

## Steps
1. **Collect candidates** into one list, with their source:
   - the backlog: `invai-docs/waves/backlog.md` (P0 and P1 tables; ids `B-##` are stable, sources `v1-#`,
     `M-#`, `P-G#`, `S-G#`, `S-#`),
   - open pilot issues: `invai-docs/customers/issues.md` (created on first use by `triage-support-ticket`),
   - approved scope-change requests: `invai-docs/product/scope-changes/`,
   - security findings still open: `invai-docs/security/v1-review.md`,
   - metric alarms from the latest `invai-docs/metrics/weekly/` file (created on first use by `weekly-metrics-review`).
2. **Pull out the "always in scope" items first** (`product/scope.md`, "Always in scope"): bugs that block
   shipping or cause a wrong print, security findings, incidents, compliance deadlines, and reliability needed
   to run pilots. Backlog P0 items ("breaks in production, violates a policy, or blocks a pilot or approval")
   belong here. They skip the ranking but still take a slot and still get a card.
3. **Drop anything outside `invai-docs/product/scope.md`.** List it under "Not now: out of scope" with a
   pointer to `scope-change-request`.
4. **Score each remaining item** on the five factors in `scoring.md` (this folder). Write one sentence of
   evidence per score. No evidence means a score of 1.
5. **Compute** `priority = (pain × shops × confidence) / (effort × risk)`, then apply the approval rule: if
   the item needs an outside approval that hasn't landed (Etsy commercial access, Amazon SP-API, TikTok
   Partner, Walmart Solution Provider, EasyPost partner), it can't ship value yet. Rank it below every usable
   item unless the work is the application packet itself.
6. **Sanity-check the top 5** against the wedge: orders → gang sheets → floor → labels must be excellent
   before breadth. If the top 5 has no wedge item while a wedge issue is open, explain why in one line.
7. **Check specs.** Each of the top 5 needs a `ready` spec in `invai-docs/specs/`. Missing one? Run
   `write-spec`, or swap in the next item that has one.
8. **Write the ranking** to `invai-docs/product/backlog-ranking.md` (created on first use). Add a new dated
   section on top; never rewrite old sections. Use the table in `scoring.md`.
9. **Write "what changed and why"**: 3–5 lines on what moved since last time and which evidence moved it.
10. **Hand to the tech lead.** The tech lead owns `waves/backlog.md` and the wave plan; you rank, it reorders
    the table. You review the wave plan against scope when it comes back (operating system, "Who reviews
    whom").

## Rules
- MUST keep a wave at 5 items or fewer, always-in-scope items included.
- MUST score from evidence (issue ids, research section numbers, metric files), not opinion.
- MUST count shops honestly: pilots are 2–3 shops. "All pilots" means say how many.
- MUST NOT rank a one-shop quirk above a problem two shops confirmed, unless it blocks shipping.
- MUST NOT create or assign task cards. That is the tech lead's job.
- MUST NOT reorder around a logged decision (`invai-docs/decisions/`) without new evidence. Reopening one goes
  to the owner through `escalate-to-owner`.

## Done when
- A dated section in `product/backlog-ranking.md` lists every candidate with five scores, evidence and
  priority.
- The proposed wave has at most 5 items, each with a `ready` spec and a scope ref.
- Out-of-scope and blocked-on-approval items are listed separately with a reason.
- The "what changed and why" note is written and the tech lead has been told.

## References
- `scoring.md` (this folder)
- `invai-docs/team/operating-system.md` (owner rules 5 and 6, wave step 1)
- `invai-docs/research/13-team-gap-analysis.md` §5.5 (the factors) and §6.1
- `invai-docs/research/03-pain-points.md` (ranked pains)
- `.claude/agents/product-manager.md` ("Rules")
- Related playbooks: `write-spec`, `scope-change-request`, `weekly-metrics-review`, `triage-support-ticket`
