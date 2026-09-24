#!/usr/bin/env python3
"""PreToolUse guard for the InvAI team (see invai-docs/team/operating-system.md).

- Bash: denies force-pushes, history or remote rewrites, tag pushes, deploys, cloud CLIs,
  and secret or repo-setting changes.
- MCP tools: anything that isn't clearly read-only (send, publish, create, update,
  delete...) needs the owner's explicit approval ("ask").

Fails closed: if the input can't be parsed, the call is denied.
"""
import json
import re
import sys

INBOX = "If it's really needed, add an entry to invai-docs/owner-inbox.md (escalate-to-owner)."


def deny(reason):
    print(f"Blocked by InvAI team rules: {reason}. {INBOX}", file=sys.stderr)
    sys.exit(2)


def ask(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": f"InvAI team rule: {reason}. Only the owner approves this.",
    }}))
    sys.exit(0)


try:
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
except Exception:
    deny("the guard hook couldn't read its input")

GIT = r"\bgit(?:\s+-C\s+\S+|\s+-c\s+\S+|\s+--?[\w-]+(?:=\S+)?)*\s+"

BASH_RULES = [
    (GIT + r"push\b.*(--force|--force-with-lease|--mirror|--delete|--tags|--follow-tags|\s-[a-zA-Z]*[fd]\b|\s\+\S+|\s:\S+|refs/tags|\sv\d)",
     "no force-push, ref deletion, mirror or tag push (tags deploy production)"),
    (GIT + r"remote\s+(add|remove|rm|set-url|rename)\b", "never change remotes"),
    (GIT + r"(filter-branch|filter-repo)\b", "never rewrite history"),
    (r"(^|[\s/])(sst\s+(deploy|remove)|cdk\s+(deploy|destroy)|terraform\s+(apply|destroy)|pulumi\s+(up|destroy))\b",
     "deploys to real environments are triggered by the owner (deploy-to-environment)"),
    (r"\bpnpm\b.*\b(sst:deploy|deploy:\w+)\b", "deploys to real environments are triggered by the owner"),
    (r"\bgh\s+workflow\s+run\b", "running workflows (deploy.yml) is triggered by the owner"),
    (r"\bgh\s+run\s+(rerun|cancel)\b", "re-running or cancelling workflow runs (deploys) is done by the owner"),
    (r"\bgh\s+(secret|variable)\s+(set|delete|remove)\b", "secrets and variables are changed by the owner"),
    (r"\bgh\s+repo\s+(delete|edit|rename|archive)\b", "repo settings are changed by the owner"),
    (r"\bgh\s+api\b.*(secrets|variables|dispatches|/keys|-X\s*DELETE|--method\s+DELETE)",
     "secrets, deploy keys and workflow dispatch are changed by the owner"),
    (r"\bgh\s+release\s+(create|delete|edit)\b", "releases are created by the owner"),
    (r"^\s*(?:sudo\s+|env\s+|command\s+|exec\s+|\w+=\S+\s+)*(?:\S*/)?aws\s+", "real AWS accounts are touched only by the owner"),
]

READ_ONLY_MCP = re.compile(
    r"__(?:notion-)?(get|list|search|read|fetch|query|find|show|describe|explore|status|context|guide|"
    r"balance|wait|inspect|check|suggest|resolve|models|apps_search|apps_describe|"
    r"job_display|jobs_wait|tabs_context|read_page|get_page_text|read_console|read_network|"
    r"authenticate|complete_authentication)",
    re.I,
)

if tool == "Bash":
    cmd = tool_input.get("command", "")
    cmd = re.sub(r"\\\n", " ", cmd)  # join line continuations
    segments = re.split(r"&&|\|\||[;|\n]", cmd)
    for seg in segments + [cmd]:
        for pattern, reason in BASH_RULES:
            if re.search(pattern, seg):
                deny(reason)
elif tool.startswith("mcp__"):
    if not READ_ONLY_MCP.search(tool):
        ask(f"'{tool}' can send, publish or change something outside the team")

sys.exit(0)
