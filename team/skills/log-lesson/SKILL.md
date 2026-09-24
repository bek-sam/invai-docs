---
name: log-lesson
description: Add a blameless lesson to InvAI's append-only invai-docs/team/lessons.md (date, source, what happened, cause, rule, where it's enforced) and promote repeat lessons into a playbook, role file, test or hook. Use after a review catch, escaped defect, incident, postmortem, retro, canary result or any "we should never do that again" moment.
---

# Log a lesson

A mistake the team made once becomes a written rule, and a mistake made twice becomes a check that runs by
itself.

## When to use
- Wave retro (tech lead, operating system step 7).
- A postmortem produced an action item (`postmortem`).
- A reviewer caught something the author's checks missed, or a canary bug was (or wasn't) caught.
- An escaped defect: QA or a pilot found a bug after approval.
- You lost time to an environment or tooling trap other agents will hit too.

Not for one-off personal gotchas: those go in your role memory (`.claude/agent-memory/<role>/`, created when
`memory: project` is first used).

## Steps
1. **Check for a repeat.** `grep -in "<keyword>" invai-docs/team/lessons.md`. If the same cause is already
   there, this is a second occurrence: go to step 5 (promotion) as well as adding the row.
2. **Write the cause blamelessly.** Name the condition that let it happen (missing check, unclear doc, tool
   behavior, time pressure, a wrong default), never a role or agent as the cause. "Reviewer approved without
   re-running tests" becomes "the review template didn't require re-run evidence".
3. **Write the rule** as something checkable: "Run 3–4 agents at once, not more", not "be careful with
   agents".
4. **Append one row** to the table at the end of `invai-docs/team/lessons.md`, in exactly this shape:
   ```
   | YYYY-MM-DD | <source> | <what happened, one sentence> | <cause, blameless> | <rule> | <where it's enforced> |
   ```
   - Source: `wave <n>`, `T-<n>-<k> review`, `incident <YYYY-MM-DD>-<slug>`, `postmortem <slug>`,
     `canary wave <n>`, `v1 build`.
   - Enforced in: the real file path(s), for example `CLAUDE.md`, `run-golden-path`,
     `src/db/rls-coverage.test.ts`, `.claude/hooks/guard-bash.py`. If it isn't enforced anywhere yet, write
     `proposed: <where>` and tell the tech lead.
   - Keep each cell to one sentence. No pipes (`|`) inside cells.
   - Never edit or delete earlier rows. The file is append-only.
5. **Promote on the second occurrence** (promotion ladder, `operating-system.md` "How the team learns"):
   1. Second time → the rule goes into the relevant playbook (`.claude/skills/<name>/SKILL.md`) or role file
      (`.claude/agents/<role>.md`). The tech lead owns `invai-docs/team/**` and edits playbooks and role
      files; other roles propose the exact text.
   2. Mechanically checkable → it becomes a test (owner of the code path), a lint rule, or a hook in
      `.claude/settings.json` / `.claude/hooks/`.
   3. Update the "Enforced in" of the new row to the place it now lives.
6. **Tell the tech lead** in your report: the row you added and any promotion you propose.

## Rules
- MUST be blameless. No role, agent or model is ever the cause.
- MUST name where the rule is enforced, or mark it `proposed:`.
- MUST append only. Corrections go in a new row that says what it corrects.
- MUST NOT put PII, secrets, customer names or real shop data in a lesson.
- MUST NOT log a lesson that restates generic engineering advice. Only InvAI-specific facts that caused real
  time loss or risk.

## Done when
- One new row at the end of the lessons table, with all 6 cells filled.
- If this was a repeat, a promotion is proposed or done, and the row names where it lives.
- The tech lead has the row in your report.

## References
- `invai-docs/team/lessons.md` (the log and its existing rows)
- `invai-docs/team/operating-system.md` ("How the team learns", retro step)
- `invai-docs/research/13-team-gap-analysis.md` §6.6
- Related: `postmortem`, `independent-review` (canary catch rate)
