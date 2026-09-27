#!/bin/bash
# Copy the InvAI team between the live workspace (invai/) and this backup folder.
# Usage, from invai/:  bash invai-docs/team/sync.sh backup|restore
set -euo pipefail
cd "$(dirname "$0")/../.."   # the invai/ workspace
B=invai-docs/team
case "${1:-}" in
  backup)
    rm -rf "$B/agents" "$B/skills" "$B/hooks"
    mkdir -p "$B/agents" "$B/skills" "$B/hooks"
    cp .claude/agents/*.md "$B/agents/"
    cp -R .claude/skills/. "$B/skills/"
    cp .claude/hooks/* "$B/hooks/"
    cp .claude/settings.json "$B/settings.json"
    cp CLAUDE.md "$B/CLAUDE.md"
    if [ -d .claude/agent-memory ]; then
      rm -rf "$B/agent-memory" && mkdir -p "$B/agent-memory"
      cp -R .claude/agent-memory/. "$B/agent-memory/"
    fi
    echo "Backed up. Now commit invai-docs." ;;
  restore)
    mkdir -p .claude/agents .claude/skills .claude/hooks
    cp "$B"/agents/*.md .claude/agents/
    cp -R "$B/skills/." .claude/skills/
    cp "$B"/hooks/* .claude/hooks/ && chmod +x .claude/hooks/*
    cp "$B/settings.json" .claude/settings.json
    cp "$B/CLAUDE.md" CLAUDE.md
    if [ -d "$B/agent-memory" ]; then
      mkdir -p .claude/agent-memory
      cp -Rn "$B/agent-memory/." .claude/agent-memory/   # never overwrite newer live memory
    fi
    echo "Restored the team into invai/." ;;
  *) echo "usage: bash invai-docs/team/sync.sh backup|restore" >&2; exit 1 ;;
esac
