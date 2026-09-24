# How to write an InvAI playbook (skill)

A playbook is a Claude Code skill: `invai/.claude/skills/<name>/SKILL.md`, backed up in `invai-docs/team/skills/<name>/SKILL.md`. Roles preload playbooks through the `skills:` list in their role file. Any agent can also invoke one by name.

## Format
```
---
name: <kebab-case, same as the folder>
description: <what it does + when to use it, with trigger words an agent would recognize. One or two sentences, under 400 characters. This is what makes the playbook get picked.>
---

# <Title>

<One line: the outcome this playbook guarantees.>

## When to use
## Steps
## Rules (MUST / MUST NOT)
## Done when
## References
```
- Add `disable-model-invocation: true` only when the playbook has outside side effects that the owner must trigger (for example `deploy-to-environment`).
- Put long material (templates, tables, checklists) in extra files next to `SKILL.md`, such as `template.md` or `checklist.md`, and link to them. The agent reads them when needed.

## Content rules
1. **Specific to InvAI.** Name the real paths, commands, helpers, roles and files. Check that each one exists (`ls`, `grep`) before writing it down, and never invent a helper, script or path. Planned things that don't exist yet are marked "(to be created)".
2. **Steps an agent can follow and check.** Use numbered steps, concrete commands, and a "Done when" list that someone else could verify.
3. **Point, don't copy.** Link to `CLAUDE.md`, `team/operating-system.md`, repo READMEs and the research rulebooks (`research/10-marketplace-engineering-rules.md`, `11-platform-scale-playbook.md`, `12-security-quality-playbook.md`, `13-team-gap-analysis.md`) instead of repeating them. Quote a rule only when the playbook depends on it.
4. **Short.** 60–180 lines. No filler, no motivation paragraphs, no generic advice any engineer already knows.
5. **Plain language.** Short sentences, and InvAI's words (shop, order item, gang sheet, press, pack station).
6. **Respect the operating system.** Owners edit only their owned paths. Anything outbound or irreversible goes to `owner-inbox.md` through `escalate-to-owner` or `send-owner-draft`. Decisions go to `decisions/` through `record-decision`.
