"""Adversarial tests for guard-bash.py (T-16-2). Each row: id, command, caller, expected, lesson.

Caller: MAIN = main session (no agent_type), otherwise the agent_type string.
Run: python3 -B -m unittest discover -s invai-docs/team/hooks/tests
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "guard-bash.py"
MAIN = None
BE = "backend-engineer"

CASES = [
    # --- R1 git push: main session or tech-lead only (lessons wave 2, wave 8) ---
    ("P01", "git push origin main", BE, "deny", "R1"),
    ("P02", "git -C /Users/bekbolsun/invai/invai-docs push", MAIN, "allow", "R1"),
    ("P03", "git -C /Users/bekbolsun/invai/invai-docs push origin main", "tech-lead", "allow", "R1"),
    ("P04", "cd invai-backend && git push origin main", "reviewer", "deny", "R1"),
    ("P05", "git -C ../invai-web push", BE, "deny", "R1"),
    ("P06", "GIT_SSH_COMMAND=ssh git --no-pager push origin main", BE, "deny", "R1"),
    ("P07", "git --git-dir .git push", BE, "deny", "R1"),
    ("P08", "git commit -m 'x' -- a.ts; git push", BE, "deny", "R1"),
    ("P09", "git status && \\\n  git push origin main", BE, "deny", "R1"),
    ("P10", "\"git\" 'push'", BE, "deny", "R1"),
    ("P11", "GIT PUSH origin main", BE, "deny", "R1"),
    ("P12", "bash -c \"git push origin main\"", BE, "deny", "R1"),
    ("P13", "echo 'git push origin main' | sh", BE, "deny", "R1"),
    ("P14", "G=git; $G push", BE, "deny", "R1"),
    ("P15", "git -c alias.p=push p", MAIN, "deny", "R1"),
    ("P16", "git commit -m \"docs: only the tech lead may git push\" -- waves/16/x.md", BE, "allow", "R1"),
    ("P17", "git push --force origin main", MAIN, "deny", "existing"),
    ("P18", "perl -e 'alarm 120; exec @ARGV' git push", "qa-engineer", "deny", "R1"),
    ("P19", "echo \"$(git push)\"", BE, "deny", "R1"),
    ("P20", "git send-pack origin main", BE, "deny", "R1"),
    # --- R2 destructive working-tree commands (lessons wave 4, wave 8) ---
    ("S01", "git stash", MAIN, "deny", "R2"),
    ("S02", "git stash pop", BE, "deny", "R2"),
    ("S03", "git -C invai-floor stash push -m tmp", BE, "deny", "R2"),
    ("S04", "git stash list", BE, "allow", "R2"),
    ("S05", "git stash show -p stash@{0}", BE, "allow", "R2"),
    ("S06", "cd invai-backend; git stash -u", BE, "deny", "R2"),
    ("S07", "git   Stash", BE, "deny", "R2"),
    ("S08", "git reset --hard HEAD", BE, "deny", "R2"),
    ("S09", "git reset HEAD src/a.ts", BE, "allow", "R2"),
    ("S10", "git checkout -- .", BE, "deny", "R2"),
    ("S11", "git checkout -- src/a.ts", BE, "deny", "R2"),
    ("S12", "git checkout .", BE, "deny", "R2"),
    ("S13", "git checkout src/modules/orders/service.ts", BE, "deny", "R2"),
    ("S14", "git checkout main", MAIN, "allow", "R2"),
    ("S15", "git restore src/a.ts", BE, "deny", "R2"),
    ("S16", "git restore .", BE, "deny", "R2"),
    ("S17", "git restore --staged src/a.ts", BE, "allow", "R2"),
    ("S18", "git restore -S src/a.ts", BE, "allow", "R2"),
    ("S19", "git restore --staged --worktree src/a.ts", BE, "deny", "R2"),
    ("S20", "git clean -fd", BE, "deny", "R2"),
    ("S21", "git clean -xdf", MAIN, "deny", "R2"),
    ("S22", "git clean --force", BE, "deny", "R2"),
    ("S23", "git clean -n", BE, "allow", "R2"),
    ("S24", "echo `git stash`", BE, "deny", "R2"),
    ("S25", "git commit -m 'lesson: never git stash or git reset --hard' -- team/lessons.md", BE, "allow", "R2"),
    ("S26", "git show HEAD:src/a.ts > /tmp/a.ts", BE, "allow", "R2"),
    # --- R3 pattern kills (lesson wave 2) ---
    ("K01", "pkill -f vite", BE, "deny", "R3"),
    ("K02", "killall node", MAIN, "deny", "R3"),
    ("K03", "/usr/bin/pkill node", BE, "deny", "R3"),
    ("K04", "PKILL node", BE, "deny", "R3"),
    ("K05", "kill $(pgrep -f 'tsx watch')", BE, "deny", "R3"),
    ("K06", "pgrep -f vite | xargs kill -9", BE, "deny", "R3"),
    ("K07", "kill `pidof node`", BE, "deny", "R3"),
    ("K08", "ps aux | grep '[t]sx' | awk '{print $2}' | xargs kill", BE, "deny", "R3"),
    ("K09", "kill 12345", BE, "allow", "R3"),
    ("K10", "kill -9 12345 23456", BE, "allow", "R3"),
    ("K11", "kill $(lsof -ti :3101)", BE, "allow", "R3"),
    ("K12", "lsof -ti :3101 | xargs kill", BE, "allow", "R3"),
    ("K13", "kill -9 -1", BE, "deny", "R3"),
    ("K14", "kill -- -4321", BE, "deny", "R3"),
    ("K15", "sudo pkill node", BE, "deny", "R3"),
    # --- R4 staging everything (handbook) ---
    ("A01", "git add -A", BE, "deny", "R4"),
    ("A02", "git add --all", BE, "deny", "R4"),
    ("A03", "git add .", MAIN, "deny", "R4"),
    ("A04", "git add -- .", BE, "deny", "R4"),
    ("A05", "git -C invai-web add -Av", BE, "deny", "R4"),
    ("A06", "git add -u", BE, "deny", "R4"),
    ("A07", "git add src/a.ts src/b.ts", BE, "allow", "R4"),
    ("A08", "git commit -a -m wip", BE, "deny", "R4"),
    ("A09", "git commit -am 'wip'", BE, "deny", "R4"),
    ("A10", "git commit --all -m wip", BE, "deny", "R4"),
    ("A11", "git commit -m 'fix -a flag' -- src/a.ts", BE, "allow", "R4"),
    ("A12", "git commit -ma", BE, "allow", "R4"),
    ("A13", "cd invai-backend && git add src/x.ts && git commit -m x -- src/x.ts", BE, "allow", "R4"),
    # --- R5 installs need the owner (lessons waves 6/7) ---
    ("I01", "pnpm install", BE, "ask", "R5"),
    ("I02", "pnpm i", MAIN, "ask", "R5"),
    ("I03", "pnpm add zod", BE, "ask", "R5"),
    ("I04", "npm install", BE, "ask", "R5"),
    ("I05", "cd ../invai-web-T-1 && pnpm --dir . install --frozen-lockfile", "reviewer", "ask", "R5"),
    ("I06", "CI=1 pnpm -C invai-ui i", BE, "ask", "R5"),
    ("I07", "pnpm typecheck && pnpm lint && pnpm test", BE, "allow", "R5"),
    ("I08", "pnpm exec vitest run", BE, "allow", "R5"),
    # --- R6 db:reset only for the gate (qa-engineer or main) ---
    ("D01", "pnpm db:reset", BE, "ask", "R6"),
    ("D02", "cd invai-backend && pnpm db:reset && pnpm db:migrate && pnpm db:seed", "web-engineer", "ask", "R6"),
    ("D03", "pnpm db:reset", "qa-engineer", "allow", "R6"),
    ("D04", "pnpm run db:reset", MAIN, "allow", "R6"),
    ("D05", "pnpm exec tsx src/db/reset.ts", BE, "ask", "R6"),
    ("D06", "pnpm db:migrate", BE, "allow", "R6"),
    # --- existing rules still hold ---
    ("E01", "git push origin v1.2.0", MAIN, "deny", "existing"),
    ("E02", "sst deploy --stage production", MAIN, "deny", "existing"),
    ("E03", "aws s3 ls", MAIN, "deny", "existing"),
    ("E04", "AWS s3 ls", MAIN, "deny", "existing"),
    ("E05", "gh secret set X", MAIN, "deny", "existing"),
    ("E06", "git remote set-url origin x", MAIN, "deny", "existing"),
    ("E07", "git status && git log --oneline -3", BE, "allow", "existing"),
    # --- hiding tricks ---
    ("H01", "$'\\x67it' push", BE, "deny", "evasion"),
    ("H02", "eval \"git stash\"", BE, "deny", "evasion"),
    ("H03", "cat <<'EOF'\ndon't worry\nEOF\ngit stash", BE, "deny", "evasion"),
    ("H04", "git config alias.sv stash", BE, "deny", "evasion"),
    ("H05", "timeout 60 git push", BE, "deny", "evasion"),
    ("H06", "(cd invai-web && git stash)", BE, "deny", "evasion"),
    ("H07", "env -i PATH=/usr/bin git add -A", BE, "deny", "evasion"),
    ("H08", "if true; then git reset --hard; fi", BE, "deny", "evasion"),
    ("H09", "git${IFS}stash", BE, "deny", "evasion"),
    ("H10", "sh -c 'bash -c \"git stash\"'", BE, "deny", "evasion"),
    ("H11", "find . -name x -exec git stash \\;", BE, "deny", "evasion"),
    ("H12", "python3 -c \"import os; os.system('git push origin main')\"", BE, "deny", "evasion"),
    ("H13", "python3 -c \"import subprocess; subprocess.run(['git', 'stash'])\"", BE, "deny", "evasion"),
    ("H14", "node -e \"require('child_process').execSync('pkill node')\"", BE, "deny", "evasion"),
    ("H15", "python3 -c \"print('hello')\"", BE, "allow", "evasion"),
    ("H16", "command -p git stash", BE, "deny", "evasion"),
    ("H17", "/usr/bin/env git stash", BE, "deny", "evasion"),
    # --- round 2: here-strings and heredocs fed to a shell (T-16-2 reviewer finding 1) ---
    ("W01", "bash <<< 'git push origin main'", BE, "deny", "R1"),
    ("W02", "sh <<< 'git stash'", BE, "deny", "R2"),
    ("W03", "bash <<< 'git reset --hard'", BE, "deny", "R2"),
    ("W04", "zsh <<< 'pkill node'", BE, "deny", "R3"),
    ("W05", "sh <<< 'git add -A'", BE, "deny", "R4"),
    ("W06", "bash<<<\"pnpm install\"", BE, "ask", "R5"),
    ("W07", "bash -s <<< 'git push'", BE, "deny", "R1"),
    ("W08", "cat <<< 'git push' | bash", BE, "deny", "R1"),
    ("W09", "bash <<'EOF'\ngit push origin main\nEOF", BE, "deny", "R1"),
    ("W10", "sh <<EOF\ngit stash\nEOF", BE, "deny", "R2"),
    ("W11", "bash <<< 'git status'", BE, "allow", "R1"),
    ("W12", "grep x <<< 'git push is only for the tech lead'", BE, "allow", "R1"),
    ("W13", "bash <<< 'aws s3 ls'", MAIN, "deny", "existing"),
    ("W14", "G='git push'; bash <<< \"$G\"", BE, "deny", "R1"),
    # --- round 2: npm-ecosystem wrappers (T-16-2 security finding 1) ---
    ("N01", "npx git push origin main", BE, "deny", "R1"),
    ("N02", "npx git add -A", BE, "deny", "R4"),
    ("N03", "npx git stash", BE, "deny", "R2"),
    ("N04", "npx git reset --hard", BE, "deny", "R2"),
    ("N05", "npx pkill -f node", BE, "deny", "R3"),
    ("N06", "npx pnpm install", BE, "ask", "R5"),
    ("N07", "npx npm install", BE, "ask", "R5"),
    ("N08", "npx -y pnpm add lodash", BE, "ask", "R5"),
    ("N09", "corepack pnpm install", BE, "ask", "R5"),
    ("N10", "npx aws s3 rm s3://bucket/key", MAIN, "deny", "existing"),
    ("N11", "pnpm dlx git push", BE, "deny", "R1"),
    ("N12", "pnpm exec git stash", BE, "deny", "R2"),
    ("N13", "pnpm -C invai-web exec pkill node", BE, "deny", "R3"),
    ("N14", "bunx git push", BE, "deny", "R1"),
    ("N15", "yarn dlx git add .", BE, "deny", "R4"),
    ("N16", "npm exec -- git push", BE, "deny", "R1"),
    ("N17", "npx --package=foo -c 'git stash'", BE, "deny", "R2"),
    ("N18", "npx pnpm db:reset", BE, "ask", "R6"),
    ("N19", "npx vitest run", BE, "allow", "R5"),
    ("N20", "pnpm exec biome check .", BE, "allow", "R5"),
    ("N21", "corepack enable", MAIN, "allow", "R5"),
]


def run(payload_text):
    return subprocess.run([sys.executable, "-B", str(GUARD)], input=payload_text, capture_output=True, text=True,
                          timeout=20)


def decision(r):
    if r.returncode == 2:
        return "deny"
    if r.returncode == 0 and r.stdout.strip():
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"]
    if r.returncode == 0:
        return "allow"
    return f"error rc={r.returncode}"


class TestGuard(unittest.TestCase):
    def test_table_has_at_least_40_cases(self):
        self.assertGreaterEqual(len(CASES), 40)
        self.assertEqual(len({c[0] for c in CASES}), len(CASES))

    def test_commands(self):
        for cid, cmd, caller, expected, _lesson in CASES:
            payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "session_id": "s", "cwd": "/tmp"}
            if caller is not None:
                payload["agent_type"], payload["agent_id"] = caller, "a1"
            with self.subTest(cid=cid, cmd=cmd, caller=caller):
                r = run(json.dumps(payload))
                self.assertEqual(decision(r), expected, r.stderr or r.stdout)

    def test_malformed_input_is_denied(self):
        for raw in ("", "not json", "[1]", '{"tool_name": 5}',
                    '{"tool_name": "Bash", "tool_input": {"command": 123}}',
                    '{"tool_name": "Bash", "tool_input": ["git", "push"]}',
                    '{"tool_name": "Bash", "tool_input": {"command": "ls"}, "agent_type": 7}'):
            with self.subTest(raw=raw):
                self.assertEqual(decision(run(raw)), "deny")

    def test_deny_messages_say_why(self):
        r = run(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push"}, "agent_type": BE}))
        self.assertIn("only the tech lead pushes", r.stderr)
        r = run(json.dumps({"tool_name": "Bash", "tool_input": {"command": "pnpm install"}}))
        self.assertIn("Only the owner approves", json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"])

    def test_mcp_rules_unchanged(self):
        r = run(json.dumps({"tool_name": "mcp__claude_ai_Gmail__send_message", "tool_input": {}}))
        self.assertEqual(decision(r), "ask")
        r = run(json.dumps({"tool_name": "mcp__claude_ai_Gmail__search_threads", "tool_input": {}}))
        self.assertEqual(decision(r), "allow")
        r = run(json.dumps({"tool_name": "Read", "tool_input": {"file_path": "/x"}}))
        self.assertEqual(decision(r), "allow")


if __name__ == "__main__":
    unittest.main()
