# InvAI agent team (backup)

A copy of the Claude Code agent team for this workspace. The live files sit outside every git repo, so this folder is the versioned backup.

| Backup here | Live location |
| --- | --- |
| `team/CLAUDE.md` | `invai/CLAUDE.md`: the team handbook every agent reads |
| `team/agents/*.md` | `invai/.claude/agents/*.md`: one file per role (16 roles) |

## Restore after a fresh clone

Run from the `invai/` workspace folder:

```
mkdir -p .claude/agents
cp invai-docs/team/agents/*.md .claude/agents/
cp invai-docs/team/CLAUDE.md CLAUDE.md
```

## Keep it in sync

After editing the live files, copy them back here and commit:

```
cp .claude/agents/*.md invai-docs/team/agents/
cp CLAUDE.md invai-docs/team/CLAUDE.md
```
