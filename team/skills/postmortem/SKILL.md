---
name: postmortem
description: Write a blameless InvAI postmortem within 48 hours of every incident or escaped High defect. Impact per shop, timeline, contributing causes found in systems and checks (never people), action items with owners and cards, and lessons fed into lessons.md, v1-review.md and decisions. Use after incident-response resolves, after a High bug reached a pilot, or when asked for "RCA" or "what went wrong".
---

# Postmortem

Every incident leaves the system harder to break in the same way: causes are found in conditions we control,
and each one has an owned, dated action and a lesson.

## When to use
- Every incident, within 48 hours of `resolved` (`operating-system.md`, "How the team learns").
- Every escaped High defect: a High-severity bug found by QA or a pilot after review approval.
- A canary bug that the review missed (lighter version: timeline, causes, actions).

## Steps
1. **Open the file.** Copy `template.md` (this folder) to `invai-docs/ops/postmortems/<YYYY-MM-DD>-<slug>.md`
   (folder to be created; platform-sre owns `invai-docs/ops/**`). Use the incident's date and slug. For an
   escaped defect, QA or the tech lead writes it and the platform-sre files it.
2. **Build the timeline from evidence,** not memory: the incident file's timestamped lines,
   `git -C <repo> log --since=<date> --format='%h %ad %s' --date=iso`, review files in
   `invai-docs/waves/<n>/reviews/`, log excerpts (ids only), alert history, owner-inbox entries. Every row has
   a source.
3. **Measure impact.** Shops affected (count; ids stay in the incident file), duration, orders delayed, labels
   failed, sheets wrong, scans blocked, error budget used (`define-slo`), buyer data involved (categories and
   count, never rows), and which notices the owner sent.
4. **Find contributing causes, blamelessly.** For each thing that went wrong, ask what condition allowed it,
   until you reach something the team can change:
   - a missing or weak check (test, lint, hook, review checklist item),
   - a default that bit (SST defaults, BullMQ `removeOnComplete`, in-memory rate limits),
   - an unclear or wrong doc, playbook or card,
   - a missing signal (no alert, no `company_id` in logs),
   - an environment trap (`tsx watch` restarts, shared dev DB, OrbStack hang).
   Write "the card template had no replay criterion", not "the engineer forgot replay". Name the reviewer's
   catch or miss as a property of the review process.
5. **Check the review trail** for escaped defects: did the card have the right acceptance criterion; did the
   review re-run the right command; did `scan-test-weakening.sh` or the checklist have a gap? This feeds the
   canary catch-rate metric in the wave file.
6. **Write action items.** Each has a type (prevent, detect, mitigate, process), one owner role, a card or
   backlog id (`invai-docs/waves/backlog.md`, from the tech lead), and a due date. Prefer mechanical fixes (a
   test, a hook, an alert) over "be careful". Security fixes follow the 7-day (Critical) / 30-day (High)
   clocks.
7. **Feed the learning system.**
   - One `log-lesson` row per new rule, with "Enforced in" pointing at the playbook, test or hook that now
     carries it.
   - Security causes become findings in `invai-docs/security/v1-review.md` (security-reviewer).
   - Lasting rules or accepted risks become decisions (`record-decision`).
8. **Review.** The tech lead and the owner role of the failing path review the draft; the security-reviewer
   too for security incidents. Fix factual errors and any blaming language, then set status `reviewed`.
9. **Report to the owner** in plain language: what happened, the impact, what we're changing, and anything the
   owner must decide (spend, a partner notice follow-up). Link the file in the owner's incident inbox entry.
10. **Close the loop.** When all action items are done, set status `actions done` and link the evidence. The
    tech lead tracks open actions in each retro.

## Rules
- MUST be blameless: no person, role, agent or model is a cause. Conditions are.
- MUST finish the draft within 48 hours of resolution, even if some analysis is still open (mark it).
- MUST give every action an owner role, a card id and a due date. Actions without owners are wishes.
- MUST NOT include buyer PII, secrets, or shop names beyond what the owner approves; counts and ids only.
- MUST NOT publish the postmortem outside the team. A public or shop-facing summary is a draft for the owner
  (`send-owner-draft`).

## Done when
- `invai-docs/ops/postmortems/<YYYY-MM-DD>-<slug>.md` has every template section filled with sourced facts.
- Each contributing cause maps to at least one action with owner, card and due date.
- Lessons, findings and decisions are recorded and linked.
- Reviews are done and the owner has the plain-language summary.

## References
- `template.md` (this folder)
- `invai-docs/team/operating-system.md` ("How the team learns")
- `invai-docs/research/11-platform-scale-playbook.md` §5.4; `research/13-team-gap-analysis.md` §6.6
- Google SRE Book, "Postmortem culture" (research 11 [S28])
- Related: `incident-response`, `log-lesson`, `record-decision`, `root-cause-bug`
