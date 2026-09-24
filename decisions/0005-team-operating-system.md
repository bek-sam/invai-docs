# 0005: Team operating system

- Status: accepted (2026-09-24)
- Type: process

## Context
The v1 team had 16 roles and no enforcement. Verifiers fixed their own findings, the tech lead coded, and nobody owned production, compliance, analytics, growth or support (`research/13-team-gap-analysis.md` §3).

## Decision
Adopt `team/operating-system.md`:
- **20 roles.** Five are new: `reviewer`, `ai-engineer`, `compliance-officer`, `data-analyst` and `growth-marketer`.
- **Merged and renamed.** `design-system-engineer` is merged into `product-designer`. `devops-engineer` becomes `platform-sre`, `pilot-success` becomes `customer-success`, and `tech-writer` becomes `docs-writer`.
- **Playbooks.** Every role preloads playbooks (Claude Code skills).
- **Records.** Waves of at most 5 task cards, and an independent read-only review of every task. Decisions go in this folder, scope in `product/scope.md`, and questions for the owner in `owner-inbox.md`.
- **Tool limits.** `tech-lead` has no `NotebookEdit`, and `reviewer` has no `Edit`. Both still have Write and Bash, so "no code edits" is enforced by their role files and by independent review, not by tools. A path-guard hook is backlog B-47.
- **Guard hook** (`.claude/hooks/guard-bash.py`, fails closed):
  - denies force-pushes, ref deletions and tag pushes, remote or history rewrites, deploys, `aws` commands, and secret or repo-setting changes
  - asks the owner before any MCP tool that sends, publishes or changes something outside the team

## Consequences
- The team is bigger on paper, but `data-analyst` and `growth-marketer` stay dormant until their triggers, and no more than 3–4 agents run at once.
- Waves take longer per task because of the review step. Fewer defects should escape.
- The team metrics in each wave file show whether this is working.
