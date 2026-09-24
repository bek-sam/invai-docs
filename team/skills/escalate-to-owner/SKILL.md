---
name: escalate-to-owner
description: Ask InvAI's human owner for a decision by adding an OI-<n> entry to invai-docs/owner-inbox.md with options, a recommendation, cost of waiting, deadline and safe default. Use for deploys, real keys, anything sent outside, spending, pricing, submissions, real shop data, High security findings or PII incidents, beyond-MVP scope, reopened decisions, two failed reviews, or weakening a control.
---

# Escalate to the owner

The owner gets one short, decidable question with a recommendation and a safe default, and the team keeps
working on everything that doesn't depend on the answer.

## When to use (always escalate)
- A production or staging deploy, a real cloud account, real API keys or secrets.
- Anything sent outside the team: shops, vendors, marketplaces, partners, public posts (drafts go through
  `send-owner-draft`).
- Legal, marketplace or partner submissions and signatures.
- Spending, pricing, plan limits.
- Real shop data in any non-local environment.
- A High security finding or suspected PII incident: **immediately**, with Amazon's 24-hour clock stated (see
  step 4).
- Scope beyond the MVP (`product/scope.md`), or reopening an accepted decision.
- Two failed review rounds on a card.
- Any case where going ahead means weakening a control or a test.

**Never escalate** routine technical choices inside a card. Make the call and record it (`record-decision` if
cross-cutting).

## Steps
1. **Check it isn't answered.** Search the inbox: `grep -n "OI-" invai-docs/owner-inbox.md` and read open or
   answered entries on the same topic. Also check `invai-docs/decisions/`.
2. **Get the next id.**
   ```
   grep -oE '^## OI-[0-9]+' invai-docs/owner-inbox.md | sed 's/## OI-//' | sort -n | tail -1
   ```
   Add 1. If nothing prints, start at `OI-1`.
3. **Append the entry** at the end of `invai-docs/owner-inbox.md`, in exactly this format:
   ```
   ## OI-<n>: <question, answerable in one line>   status: open
   - From: <role>, <YYYY-MM-DD>. Deadline: <YYYY-MM-DD HH:MM TZ>. Default if no answer: <what happens>
   - Context: <2–4 lines: what happened, evidence path, what is blocked>
   - Options: A) … B) … C) …
   - Recommendation: <option and why, one or two sentences>
   - Cost of waiting: <what is blocked, what it costs per day>
   - Answer:
   ```
4. **For a High security finding or suspected PII incident,** start the Context with:
   `Detected <YYYY-MM-DD HH:MM TZ>. Amazon 24-hour notice clock (security@amazon.com, sent by the owner as incident contact) ends <detected + 24 h>. Shops to be told by the same time so they can meet GDPR's 72 h.`
   Then follow `incident-response`. Don't wait for the entry to be read before containing the problem inside
   your owned paths.
5. **Pick a safe default.** The default must be the choice that is reversible and doesn't send, spend, deploy
   or weaken anything ("hold the deploy", "keep the mock", "don't send"). Never make the default the risky
   option.
6. **Set a real deadline.** When the answer is needed to avoid the cost of waiting. For incidents, hours, not
   days.
7. **Keep working.** Continue on everything that doesn't depend on the answer. Note the OI id in your report
   and in the wave file (tech lead) so it's tracked.
8. **When answered,** the owner fills `Answer:` and sets the status. Act on it, then record anything lasting
   with `record-decision` (type `owner`) and link the OI id. If the deadline passes with no answer, apply the
   default and set `status: expired` in your report (the owner or tech lead updates the line).

## Rules
- MUST be one question per entry. Split bundles.
- MUST give 2–3 real options and one recommendation. No open-ended "what should we do?".
- MUST NOT send, deploy, spend, sign, submit or load real data while the entry is open.
  `.claude/hooks/guard-bash.py` blocks deploys and secret changes for the same reason.
- MUST NOT put secrets, keys or buyer PII in the inbox. Point to where the evidence is.
- MUST write in plain language the owner can decide on in two minutes (`write-plain-language-copy`).

## Done when
- The entry is at the end of `owner-inbox.md` with every field filled and `status: open`.
- The default is safe and the deadline is a real date and time.
- Your report and the wave file name the OI id.
- For incidents: the 24-hour clock end time is written in the entry.

## References
- `invai-docs/owner-inbox.md` (format and always-escalate list)
- `invai-docs/team/operating-system.md` ("Escalate to the owner", "The human owner keeps")
- `invai-docs/research/12-security-quality-playbook.md` §5 (incident clocks)
- Related: `send-owner-draft`, `incident-response`, `record-decision`
