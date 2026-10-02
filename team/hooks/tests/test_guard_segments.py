"""B-116 (T-20-4): guard-bash.py checks push flags and kill-by-pattern per command segment.

Lessons 2026-09-27: a plain push denied because `tr -d` ran later on the line; a kill of explicit PIDs denied
because the same line listed processes. Both must now pass, and every dangerous form must still be denied,
chained or not.
Run: python3 -B -m pytest invai-docs/team/hooks/tests -q  (or unittest discover)
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "guard-bash.py"
TL = "tech-lead"
MAIN = None
BE = "backend-engineer"

CASES = [
    # --- push: allowed now (the lesson shapes; T-P8-3: written in the one docs push form) ---
    ("B01", "git -C /Users/bekbolsun/invai/invai-docs push origin main; echo x | tr -d y", TL, "allow"),
    ("B02", "git -C /Users/bekbolsun/invai/invai-docs push origin main; echo x | tr -d y", MAIN, "allow"),
    ("B03", "git -C /Users/bekbolsun/invai/invai-docs push origin main && for r in a b; do echo $r | tr -d '\\n'; done", TL, "allow"),
    ("B04", "git -C /Users/bekbolsun/invai/invai-docs push origin main\nprintf '%s' x | tr -d y", TL, "allow"),
    ("B05", "git -C /Users/bekbolsun/invai/invai-docs push origin main | tr -d y", TL, "allow"),
    ("B06", "git -C /Users/bekbolsun/invai/invai-docs push origin main 2>&1 | tail -3", TL, "allow"),
    # T-23-6: a push whose repo is a loop variable (-C $r) can't be pinned, so the gate-stamp check refuses it.
    ("B07", "for r in invai-docs invai-backend; do git -C $r push origin main; done; git log -1 | tr -d x", TL, "deny"),
    ("B08", "git -C /Users/bekbolsun/invai/invai-docs push -u origin main", TL, "allow"),
    ("B09", "git -C /Users/bekbolsun/invai/invai-docs push --dry-run origin main", TL, "allow"),
    ("B10", "git -C /Users/bekbolsun/invai/invai-docs push origin HEAD:main", TL, "allow"),
    ("B11", "git -C /Users/bekbolsun/invai/invai-docs push origin main & wait; rm -d emptydir", TL, "allow"),
    ("B12", "git -C /Users/bekbolsun/invai/invai-docs push origin main; cut -d: -f1 /etc/hosts", TL, "allow"),
    ("B13", "git -C /Users/bekbolsun/invai/invai-docs push origin main && git log -1 --format=%h | tr -d '\\n'", TL, "allow"),
    # --- push: still denied (card AC4), alone and chained ---
    ("D01", "git push origin :main", TL, "deny"),
    ("D02", "git push -d origin main", TL, "deny"),
    ("D03", "git push --delete origin main", TL, "deny"),
    ("D04", "git push -f", TL, "deny"),
    ("D05", "git push --force-with-lease origin main", TL, "deny"),
    ("D06", "git push origin +main", TL, "deny"),
    ("D07", "echo hi && git push -f origin main", TL, "deny"),
    ("D08", "git status; git push origin :main", TL, "deny"),
    ("D09", "git status | git push --delete origin main", TL, "deny"),
    ("D10", "git status\ngit push --force origin main", TL, "deny"),
    ("D11", "(cd invai-docs && git push -d origin x)", TL, "deny"),
    ("D12", "echo $(git push -f origin main)", TL, "deny"),
    ("D13", "echo `git push origin +main`", TL, "deny"),
    ("D14", "bash -c 'git push --force-with-lease'", TL, "deny"),
    ("D15", "eval git push origin +main", TL, "deny"),
    ("D16", "git push -fu origin main", TL, "deny"),
    ("D17", "git push --forc origin main", TL, "deny"),
    ("D18", "git push --force-with-lease=main:abc123 origin main", TL, "deny"),
    ("D19", "git push origin main --tags", TL, "deny"),
    ("D20", "git push origin v1.0.0", TL, "deny"),
    ("D21", "git push origin refs/tags/v1", TL, "deny"),
    ("D22", "F=--force; git push origin main $F", TL, "deny"),
    ("D23", "git push origin main $EXTRA", TL, "deny"),
    ("D24", "git push origin $(echo --force)", TL, "deny"),
    ("D25", "git -c remote.origin.mirror=true push origin", TL, "deny"),
    ("D26", "git push --prune origin", TL, "deny"),
    ("D27", "git -C 'a;b' push -f origin main", TL, "deny"),
    ("D28", "git push origin 'main' '-f'", TL, "deny"),
    ("D29", "git push origin \"+main\"", MAIN, "deny"),
    ("D30", "git push --mirror", MAIN, "deny"),
    ("D31", "true || git push origin :refs/heads/main", MAIN, "deny"),
    ("D32", "git push origin main & git push -d origin old", TL, "deny"),
    ("D33", "git push origin main; git push --delete origin old; echo x | tr -d y", TL, "deny"),
    ("D34", "git push origin main\\\n  --force", TL, "deny"),
    ("D35", "git push origin main", BE, "deny"),  # role rule unchanged
    # T-P8-3 (OI-22): the old B-row shapes without the literal docs -C path are refused now (stricter)
    ("D36", "git push origin main; echo x | tr -d y", TL, "deny"),
    ("D37", "git push origin main 2>&1 | tail -3", TL, "deny"),
    ("D38", "git -C invai-docs push origin main", TL, "deny"),
    ("D39", "git push", MAIN, "deny"),
    # --- kill: literal PIDs are fine next to a listing (lesson 2026-09-27) ---
    ("K01", "kill 12345; ps -p 12345", TL, "allow"),
    ("K02", "kill 12345 23456 && ps aux | grep tsx", BE, "allow"),
    ("K03", "kill -9 12345\nlsof -iTCP:3101 -sTCP:LISTEN; pgrep -fl tsx", BE, "allow"),
    ("K04", "kill $(lsof -ti :3101); ps aux | grep '[t]sx'", BE, "allow"),
    ("K05", "kill -TERM 4321 && sleep 1; ps -p 4321 || echo gone", BE, "allow"),
    ("K06", "kill %1; pgrep -f vite", BE, "allow"),
    ("K07", "PID=$!; kill $PID", BE, "allow"),
    # --- kill: still denied when a lister feeds it ---
    ("X01", "kill $(pgrep -f tsx); echo done", BE, "deny"),
    ("X02", "pgrep tsx | xargs kill; echo done", BE, "deny"),
    ("X03", "P=$(pgrep tsx); kill $P", BE, "deny"),
    ("X04", "for p in $(pgrep node); do kill $p; done", BE, "deny"),
    ("X05", "echo ok && kill `pidof node`", BE, "deny"),
    ("X06", "ls; ps aux | grep x | awk '{print $2}' | xargs kill -9", BE, "deny"),
    ("X07", "bash -c 'kill $(pgrep x)'", BE, "deny"),
    ("X08", "kill 123 $(pgrep x)", BE, "deny"),
    ("X09", "kill 12345; pkill node", BE, "deny"),
    ("X10", "kill -9 -1; ps", BE, "deny"),
    ("X11", "P=$(pidof node)\nkill -9 $P", BE, "deny"),
    # T-20-4 r1 security finding 1: a lister's output relayed through a file or a `cat` substitution
    ("X12", "pgrep -f tsx > /tmp/p; kill $(cat /tmp/p)", BE, "deny"),
    ("X13", "pgrep -f tsx > /tmp/p\nkill $(cat /tmp/p)", BE, "deny"),
    ("X14", "pgrep -f tsx > /tmp/p; xargs kill < /tmp/p", BE, "deny"),
    ("X15", "ps aux | grep '[t]sx' | awk '{print $2}' > /tmp/p && kill $(cat /tmp/p)", BE, "deny"),
    ("X16", "pgrep node > /tmp/p; bash -c 'kill $(cat /tmp/p)'", BE, "deny"),
    ("X17", "pidof node > /tmp/p; kill `cat /tmp/p`", BE, "deny"),
]


def run(payload):
    return subprocess.run([sys.executable, "-B", str(GUARD)], input=json.dumps(payload), capture_output=True,
                          text=True, timeout=20)


def decision(r):
    if r.returncode == 2:
        return "deny"
    if r.returncode == 0 and r.stdout.strip():
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"]
    return "allow" if r.returncode == 0 else f"error rc={r.returncode}"


class TestSegments(unittest.TestCase):
    def test_ids_unique(self):
        self.assertEqual(len({c[0] for c in CASES}), len(CASES))

    def test_commands(self):
        for cid, cmd, caller, expected in CASES:
            payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "session_id": "s", "cwd": "/tmp"}
            if caller is not None:
                payload["agent_type"], payload["agent_id"] = caller, "a1"
            with self.subTest(cid=cid, cmd=cmd, caller=caller):
                r = run(payload)
                self.assertEqual(decision(r), expected, r.stderr or r.stdout)

    def test_push_denial_names_the_rule(self):
        r = run({"tool_name": "Bash", "tool_input": {"command": "git status; git push -d origin x"},
                 "agent_type": TL})
        self.assertIn("force-push, ref deletion", r.stderr)


if __name__ == "__main__":
    unittest.main()
