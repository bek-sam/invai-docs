"""Tests for guard-memory-path.py (T-16-2 round 2).

Run: python3 -B -m unittest discover -s invai-docs/team/hooks/tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "guard-memory-path.py"


class MemoryPath(unittest.TestCase):
    def setUp(self):
        self.proj = os.path.realpath(tempfile.mkdtemp(prefix="memproj-"))
        self.home = os.path.join(self.proj, ".claude", "agent-memory")

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.proj])

    def run_hook(self, path=None, raw=None, env_project=True, tool="Write", cwd=None):
        env = {**os.environ}
        env.pop("CLAUDE_PROJECT_DIR", None)
        if env_project:
            env["CLAUDE_PROJECT_DIR"] = self.proj
        payload = raw if raw is not None else json.dumps(
            {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": cwd or self.proj,
             "tool_input": {"file_path": path, "content": "x"}, "agent_type": "platform-sre"})
        return subprocess.run([sys.executable, "-B", str(HOOK)], input=payload, capture_output=True, text=True,
                              env=env, timeout=10)

    def test_subfolder_memory_is_denied_with_the_right_path(self):
        bad = f"{self.proj}/invai-docs/waves/16/.claude/agent-memory/platform-sre/hook-facts.md"
        r = self.run_hook(bad)
        self.assertEqual(r.returncode, 2)
        self.assertIn(f"{self.home}/platform-sre/hook-facts.md", r.stderr)

    def test_other_denied_forms(self):
        for bad, tool in ((f"{self.proj}/invai-docs/.claude/agent-memory/reviewer/MEMORY.md", "Edit"),
                          ("invai-docs/.claude/agent-memory/qa-engineer/x.md", "MultiEdit"),  # relative
                          (f"{self.home}/../../invai-docs/.claude/agent-memory/x/y.md", "Write"),  # traversal
                          ("/tmp/elsewhere/.claude/agent-memory/tech-lead/MEMORY.md", "Write")):
            with self.subTest(bad=bad):
                r = self.run_hook(bad, tool=tool)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn(self.home + "/", r.stderr)

    def test_right_place_and_other_files_are_allowed(self):
        for ok in (f"{self.home}/platform-sre/MEMORY.md", ".claude/agent-memory/reviewer/notes.md",
                   f"{self.proj}/invai-docs/team/hooks/guard-bash.py", f"{self.proj}/invai-docs/agent-memory.md",
                   f"{self.proj}/.claude/settings.json"):
            with self.subTest(ok=ok):
                r = self.run_hook(ok)
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_relative_paths_are_resolved_against_cwd_first(self):
        sub = os.path.join(self.proj, "invai-docs", "waves", "16")
        os.makedirs(sub)
        cases = [
            (".claude/agent-memory/platform-sre/note.md", sub, 2),   # bare relative from a subfolder: the incident
            ("./.claude/agent-memory/platform-sre/note.md", sub, 2),
            (".claude/agent-memory/platform-sre/note.md", self.proj, 0),   # same path from the project root
            ("./.claude/agent-memory/platform-sre/note.md", self.proj, 0),
            ("../../../.claude/agent-memory/platform-sre/note.md", sub, 0),  # climbs back to the root
            ("../.claude/agent-memory/platform-sre/note.md", sub, 2),        # lands in invai-docs/waves/.claude
            ("../../.claude/agent-memory/reviewer/MEMORY.md", sub, 2),       # lands in invai-docs/.claude
        ]
        for path, cwd, rc in cases:
            with self.subTest(path=path, cwd=cwd):
                r = self.run_hook(path, cwd=cwd, tool="Edit")
                self.assertEqual(r.returncode, rc, r.stderr)
                if rc == 2:
                    self.assertIn(f"{self.home}/", r.stderr)
                    self.assertIn(os.path.basename(path), r.stderr)

    def test_fails_open(self):
        for raw in ("", "not json", "[1]", '{"tool_input": 7}', '{"tool_input": {"file_path": 7}}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.run_hook(raw=raw).returncode, 0)
        r = self.run_hook(f"{self.proj}/x/.claude/agent-memory/r/m.md", env_project=False)
        self.assertEqual(r.returncode, 0)

    def test_registered_in_settings(self):
        s = json.loads((HOOK.parent.parent / "settings.json").read_text())
        entries = [m for m in s["hooks"]["PreToolUse"] if "guard-memory-path" in json.dumps(m)]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["matcher"], "Write|Edit|MultiEdit")


if __name__ == "__main__":
    unittest.main()
