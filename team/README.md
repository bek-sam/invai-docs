# InvAI agent team (backup)

The live team files sit in the `invai/` workspace folder, which is not a git repo. This folder is their versioned backup. **Start Claude from `invai/`**, because the team loads only there.

| Backup here | Live location | What it is |
| --- | --- | --- |
| `CLAUDE.md` | `invai/CLAUDE.md` | The handbook every agent reads |
| `agents/*.md` | `invai/.claude/agents/` | 20 role files |
| `skills/<name>/` | `invai/.claude/skills/` | 72 playbooks (Claude Code skills) that the roles preload |
| `hooks/guard-bash.py` | `invai/.claude/hooks/` | Guard hook: blocks force-pushes, deploys, `aws`, and secret changes; asks the owner before outbound MCP tools |
| `settings.json` | `invai/.claude/settings.json` | Registers the hook |

How the team works: [operating-system.md](operating-system.md). How to write a playbook: [skill-authoring.md](skill-authoring.md). What the team has learned: [lessons.md](lessons.md).

## Restore after a fresh clone
Run from the `invai/` folder:
```
bash invai-docs/team/sync.sh restore
```

## Back up after editing the live files
Run from the `invai/` folder, then commit `invai-docs`:
```
bash invai-docs/team/sync.sh backup
```
