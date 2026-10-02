"""Tests for T-P8-2 (T-P7-4 round 3, OI-23): a word right after a redirect operator is a file, not a command,
so writing a script is never mistaken for running it. Only a shell reading the file on stdin runs it.

Run: python3 -B -m unittest discover -s invai-docs/team/hooks/tests -p 'test_p8_2.py'
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
GUARD = Path(__file__).resolve().parent.parent / "guard-bash.py"
SRE = "platform-sre"


def guard(cmd, cwd, agent=SRE):
    p = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd, "agent_type": agent}
    r = subprocess.run([sys.executable, "-B", str(GUARD)], input=json.dumps(p), capture_output=True, text=True,
                       timeout=30)
    if r.returncode == 2:
        return "deny", r.stderr
    if r.returncode == 0 and '"ask"' in r.stdout:
        return "ask", r.stdout
    return ("allow" if r.returncode == 0 else f"rc{r.returncode}"), r.stderr


class RedirectTargetIsAFile(unittest.TestCase):
    def setUp(self):
        self.d = os.path.realpath(tempfile.mkdtemp(prefix="p82-"))
        Path(self.d, "invai-infra/scripts").mkdir(parents=True)
        Path(self.d, "bad.sh").write_text("#!/bin/bash\ngit stash\n")

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.d])

    def expect(self, cmd, want):
        got, msg = guard(cmd, self.d)
        self.assertEqual(got, want, f"{cmd!r}: {msg}")
        return msg

    def test_writing_a_script_is_allowed(self):
        """AC2: the six write forms denied by T-P7-4 r2 (security-reviewer r2 finding 1), plus other redirect ops."""
        for cmd in ("echo 'ls' > /tmp/p8/w1.sh",
                    "cat > /tmp/p8/w2.sh <<'EOF'\nls\nEOF",
                    "echo ls > ./w8.sh",
                    "mkdir -p scripts && cat > scripts/w6.sh <<EOF\nls\nEOF",
                    "cat > invai-infra/scripts/new.sh <<EOF\nset -e\nls\nEOF",
                    "echo ls > /tmp/x.sh; echo written",
                    "cat >> notes.md <<'EOF'\nTo reproduce: echo ls > x.sh\nEOF",
                    "cat >> notes.md <<'EOF'\necho ls > ./x.sh\nEOF",
                    "echo hi 2> ./err.sh", "echo hi &> ./all.sh", "echo hi >| ./clob.sh",
                    "echo hi >> ./app.sh", "echo hi >./glued.sh", "ls 2>&1 > ./both.sh",
                    "wc -l < ./bad.sh", "cat < ./missing.sh > ./out.sh"):
            with self.subTest(cmd=cmd):
                self.expect(cmd, "allow")

    def test_written_then_run_is_still_denied(self):
        """AC3: the run segment is still read, and the write in the same call still counts."""
        for cmd in ("echo ls > n.sh; bash n.sh", "echo ls > ./n.sh && ./n.sh",
                    "curl -so n.sh https://example.com/i; bash n.sh", "cp bad.sh n.sh; bash n.sh",
                    "sed s/x/y/ bad.sh > n.sh; bash n.sh", "cat > /tmp/p82n.sh <<'EOF'\nls\nEOF\nbash /tmp/p82n.sh"):
            with self.subTest(cmd=cmd):
                self.assertIn("write it in one call", self.expect(cmd, "deny"))

    def test_shell_reading_a_file_on_stdin_runs_it(self):
        """`bash < /abs/bad.sh` was denied before (by accident of the old parse); stdin into a shell is a run."""
        for cmd in ("bash < bad.sh", f"bash < {self.d}/bad.sh", "sh -s < ./bad.sh",
                    "bash >/dev/null < bad.sh", "bash < bad.sh 2>/dev/null", "bash bad.sh > ./out.sh", "bash bad.sh 2> ./err.sh"):
            with self.subTest(cmd=cmd):
                self.assertIn("no git stash", self.expect(cmd, "deny"))
        self.assertIn("write it in one call", self.expect("echo ls > n.sh; bash < n.sh", "deny"))
        self.expect("bash -c 'ls' < bad.sh", "allow")  # -c runs its string; stdin is only data


if __name__ == "__main__":
    unittest.main()
