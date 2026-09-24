---
name: record-decision
description: Record an InvAI architecture, product, ops, security or process decision as a numbered Nygard ADR in invai-docs/decisions/ (context, decision, status, consequences), add it to the index and link it from the wave. Use when a choice affects more than one module, repo or role, supersedes an earlier decision, or someone says "decide", "ADR" or "record this".
---

# Record a decision

Every decision that others must follow is written once, numbered, indexed and findable, and old ones are
superseded, never deleted.

## When to use
- A choice crosses modules, repos or roles (a contract shape, a state rule, a queue policy, a security limit).
- A choice reverses or narrows an accepted decision (with new evidence).
- The owner answered an `owner-inbox.md` entry that sets a rule.
- A review or retro settled a disagreement.

Not for routine choices inside one card: put those in the card's report under "Decisions".

## Steps
1. **Check it isn't decided already.** Read the index in `invai-docs/decisions/README.md` and grep:
   `grep -il "<topic>" invai-docs/decisions/*.md`. An accepted decision is reopened only with new evidence,
   and reopening goes to `owner-inbox.md` through `escalate-to-owner` first.
2. **Pick the type and owner** (`decisions/README.md`):
   | Type | Owner who must agree |
   |---|---|
   | architecture | architect |
   | product | product-manager |
   | ops | platform-sre |
   | security | security-reviewer |
   | process | tech-lead |
   | owner | the human owner (via `escalate-to-owner`) |
   If you aren't the type owner, draft it with status `proposed` and ask the owner role to accept it.
3. **Get the next number.**
   ```
   ls invai-docs/decisions | grep -E '^[0-9]{4}-' | sort | tail -1
   ```
   Add 1 and zero-pad to 4 digits. Slug: short kebab-case.
4. **Write `invai-docs/decisions/NNNN-<slug>.md`** in the house format (same as `0008-sign-in-rate-limit.md`):
   ```
   # NNNN: <decision in one line>

   - Status: proposed | accepted (YYYY-MM-DD) | superseded by NNNN
   - Type: architecture | product | ops | security | process | owner

   ## Context
   <the forces and facts, with evidence: file paths, numbers, research sections. 3–8 lines.
   End with the links: card T-n-k, spec, owner-inbox OI-n, and who decided and reviewed.>

   ## Decision
   <what we will do, stated as a rule someone can check. Include the exact values.>

   ## Consequences
   <what gets easier, what gets harder, what must change and who owns the follow-up.>
   ```
5. **Supersede, don't delete.** If this replaces decision `MMMM`, edit only its status line to
   `superseded by NNNN` and say so in your Context. Leave the rest of the old file as it was.
6. **Update the index table** in `invai-docs/decisions/README.md`: add the row
   `| [NNNN](NNNN-<slug>.md) | <one line> | <type> | <status> |` and update the status of any superseded row.
7. **Link it** from the wave file (`invai-docs/waves/<n>/wave.md`, under the card or retro) and from your
   report's "Decisions" section. The tech lead owns wave files; if you aren't the tech lead, ask them to add
   the link.
8. **Make it enforceable.** If the rule can be checked mechanically, name the test, lint rule or hook that
   will enforce it in Consequences, and give it an owner (`log-lesson` promotion ladder).

## Rules
- MUST keep one decision per file. Two decisions → two files.
- MUST state the decision as a checkable rule with exact values ("sign-in 20/min per IP", not "a reasonable
  limit").
- MUST cite evidence in Context. A preference is not evidence.
- MUST NOT change an accepted decision's body. Supersede it.
- MUST NOT record an owner-type decision (money, pricing, deploys, outside commitments, scope beyond MVP)
  without the owner's answer in `owner-inbox.md`.
- Edits to `invai-docs/decisions/**` are allowed for any role for its own type of decision; keep to your own
  file plus the index row.

## Done when
- `invai-docs/decisions/NNNN-<slug>.md` exists with Status, Type, Context, Decision and Consequences.
- The README index has its row, and any superseded decision shows `superseded by NNNN` in both places.
- The wave file or report links it.
- The type owner has accepted it, or it is clearly `proposed` with the owner named.

## References
- `invai-docs/decisions/README.md` (format, types, index)
- `invai-docs/decisions/0008-sign-in-rate-limit.md` (a good small example; it supersedes S-19)
- `invai-docs/team/operating-system.md` ("Where things live")
- Related: `escalate-to-owner`, `log-lesson`
