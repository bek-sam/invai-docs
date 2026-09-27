#!/bin/bash
# Copy the InvAI team between the live workspace (invai/) and this backup folder.
# Usage, from invai/:  bash invai-docs/team/sync.sh backup|restore
set -euo pipefail
cd "$(dirname "$0")/../.."   # the invai/ workspace
B=invai-docs/team
case "${1:-}" in
  backup)
    rm -rf "$B/agents" "$B/skills"   # hooks/ keeps its tests/ folder, so it is not wiped
    mkdir -p "$B/agents" "$B/skills" "$B/hooks"
    cp .claude/agents/*.md "$B/agents/"
    cp -R .claude/skills/. "$B/skills/"
    cp .claude/hooks/*.py "$B/hooks/"
    cp .claude/settings.json "$B/settings.json"
    cp CLAUDE.md "$B/CLAUDE.md"
    # Memory is merged, never wiped: live files overwrite their backup copies, and backup-only
    # files (seeds not yet restored, or a memory deleted live) stay. Remove stale entries by hand.
    if [ -d .claude/agent-memory ]; then
      mkdir -p "$B/agent-memory"
      cp -R .claude/agent-memory/. "$B/agent-memory/"
    fi
    echo "Backed up. Now commit invai-docs." ;;
  restore)
    mkdir -p .claude/agents .claude/skills .claude/hooks
    cp "$B"/agents/*.md .claude/agents/
    cp -R "$B/skills/." .claude/skills/
    cp "$B"/hooks/*.py .claude/hooks/ && chmod +x .claude/hooks/*.py   # hook scripts only, not tests/
    cp "$B/settings.json" .claude/settings.json
    cp "$B/CLAUDE.md" CLAUDE.md
    if [ -d "$B/agent-memory" ]; then
      mkdir -p .claude/agent-memory
      rsync -a --ignore-existing "$B/agent-memory/" .claude/agent-memory/   # never overwrite newer live memory (cp -n exits 1 on skips)
    fi
    echo "Restored the team into invai/." ;;
  *) echo "usage: bash invai-docs/team/sync.sh backup|restore" >&2; exit 1 ;;
esac
