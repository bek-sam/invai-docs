"""Adversarial tests for guard-paths.py (T-20-4, B-47): the tech lead and the reviewer write only their paths.

Each test builds a throwaway workspace (invai-docs/, invai-backend/, .claude/) and points CLAUDE_PROJECT_DIR at it.
Run: python3 -B -m pytest invai-docs/team/hooks/tests -q  (or unittest discover)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "guard-paths.py"
SETTINGS = Path(__file__).resolve().parent.parent.parent / "settings.json"
TL, RV = "tech-lead", "reviewer"

# (id, agent_type, path relative to the workspace or absolute marker, cwd relative to the workspace, expected)
CASES = [
    # tech lead: allowed
    ("T01", TL, "invai-docs/waves/20/T-20-9.md", "", "allow"),
    ("T02", TL, "invai-docs/waves/backlog.md", "", "allow"),
    ("T03", TL, "invai-docs/team/lessons.md", "", "allow"),
    ("T04", TL, "invai-docs/research/17-x.md", "", "allow"),
    ("T05", TL, "invai-docs/decisions/0099-x.md", "", "allow"),
    ("T06", TL, "invai-docs/owner-inbox.md", "", "allow"),
    ("T07", TL, "CLAUDE.md", "", "allow"),
    ("T08", TL, ".claude/agents/tech-lead.md", "", "allow"),
    ("T09", TL, ".claude/skills/task-intake/SKILL.md", "", "allow"),
    ("T10", TL, ".claude/agent-memory/tech-lead/MEMORY.md", "", "allow"),
    ("T11", TL, "invai-docs/.claude/agent-memory/tech-lead/MEMORY.md", "", "allow"),
    ("T12", TL, "@rel:waves/20/wave.md", "invai-docs", "allow"),
    ("T13", TL, "@rel:./20/reports/../wave.md", "invai-docs/waves", "allow"),
    ("T14", TL, "invai-docs/waves/20/reports/T-20-4.md", "", "allow"),
    ("T15", TL, "invai-docs/waves/20/reviews.md", "", "allow"),
    # tech lead: denied
    ("T20", TL, "invai-docs/waves/20/reviews/T-20-4-reviewer-r1.md", "", "deny"),
    ("T21", TL, "invai-docs/waves/20/reviews/sub/x.md", "", "deny"),
    ("T22", TL, "invai-backend/src/modules/orders/service.ts", "", "deny"),
    ("T23", TL, "@rel:../invai-backend/src/a.ts", "invai-docs", "deny"),
    ("T24", TL, "invai-docs/waves/../../invai-web/src/a.tsx", "", "deny"),
    ("T25", TL, "invai-docs/waves/20/../../../invai-backend/x.ts", "", "deny"),
    ("T26", TL, "invai-docs/waves/link-out/src/a.ts", "", "deny"),       # symlink waves/link-out -> invai-backend
    ("T27", TL, "invai-docs/waves/20/hard.ts", "", "deny"),               # hard link to a backend file
    ("T28", TL, ".claude/settings.json", "", "deny"),
    ("T29", TL, ".claude/hooks/guard-paths.py", "", "deny"),
    ("T30", TL, ".claude/agent-memory/reviewer/MEMORY.md", "", "deny"),
    ("T31", TL, "invai-docs/product/scope.md", "", "deny"),
    ("T32", TL, "invai-docs/owner-inbox.md.bak", "", "deny"),
    ("T33", TL, "invai-backend/CLAUDE.md", "", "deny"),
    ("T34", TL, "invai-docs/wavesX/a.md", "", "deny"),
    ("T35", TL, "invai-docs/waves", "", "deny"),
    ("T36", TL, "@abs:/etc/hosts", "", "deny"),
    ("T37", TL, "@abs:~/invai/invai-docs/waves/x.md", "", "deny"),
    ("T38", TL, "INVAI-DOCS/Waves/20/Reviews/x.md", "", "deny"),
    ("T39", TL, "invai-docs/.claude/agent-memory/reviewer/x.md", "", "deny"),
    ("T40", TL, "invai-docs/waves/20/reviews-link/x.md", "", "deny"),   # symlink waves/20/reviews-link -> reviews
    # reviewer: allowed
    ("R01", RV, "invai-docs/waves/20/reviews/T-20-4-reviewer-r1.md", "", "allow"),
    ("R02", RV, ".claude/agent-memory/reviewer/MEMORY.md", "", "allow"),
    ("R03", RV, "@rel:reviews/T-20-4-security-r1.md", "invai-docs/waves/20", "allow"),
    # reviewer: denied
    ("R10", RV, "invai-docs/waves/20/T-20-4.md", "", "deny"),
    ("R11", RV, "invai-docs/waves/reviews/x.md", "", "deny"),
    ("R12", RV, "invai-docs/waves/20/reviews/../T-20-4.md", "", "deny"),
    ("R13", RV, "invai-docs/team/hooks/guard-paths.py", "", "deny"),
    ("R14", RV, "invai-backend/src/a.ts", "", "deny"),
    ("R15", RV, "invai-docs/waves/20/reviews/out/a.ts", "", "deny"),    # symlink reviews/out -> invai-backend
    ("R16", RV, "invai-docs/.claude/agent-memory/reviewer/x.md", "", "deny"),
    ("R17", RV, ".claude/agent-memory/tech-lead/MEMORY.md", "", "deny"),
    ("R18", RV, "CLAUDE.md", "", "deny"),
    # other roles and name forms
    ("O01", "backend-engineer", "invai-backend/src/a.ts", "", "allow"),
    ("O02", "platform-sre", ".claude/settings.json", "", "allow"),
    ("O03", "invai:tech-lead", "invai-backend/src/a.ts", "", "deny"),
    ("O04", "Tech-Lead", "invai-backend/src/a.ts", "", "deny"),
    ("O05", "tech-lead-helper", "invai-backend/src/a.ts", "", "allow"),
]


class PathGuard(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="guardpaths-"))
        for d in ("invai-docs/waves/20/reviews", "invai-backend/src", "invai-web/src", ".claude/hooks"):
            os.makedirs(os.path.join(self.root, d))
        Path(self.root, "invai-backend/src/a.ts").write_text("x")
        os.symlink(os.path.join(self.root, "invai-backend"), os.path.join(self.root, "invai-docs/waves/link-out"))
        os.symlink(os.path.join(self.root, "invai-docs/waves/20/reviews"),
                   os.path.join(self.root, "invai-docs/waves/20/reviews-link"))
        os.symlink(os.path.join(self.root, "invai-backend"),
                   os.path.join(self.root, "invai-docs/waves/20/reviews/out"))
        os.link(os.path.join(self.root, "invai-backend/src/a.ts"), os.path.join(self.root, "invai-docs/waves/20/hard.ts"))
        self.log = os.path.join(self.root, "guard-paths.log")

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.root])

    def run_hook(self, payload, project=True, raw=None):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        env["INVAI_GUARD_PATHS_LOG"] = self.log
        if project:
            env["CLAUDE_PROJECT_DIR"] = project if isinstance(project, str) else self.root
        text = raw if raw is not None else json.dumps(payload)
        return subprocess.run([sys.executable, "-B", str(HOOK)], input=text, capture_output=True, text=True,
                              env=env, timeout=10)

    def payload(self, agent, path, cwd="", tool="Write"):
        if path.startswith("@rel:"):
            p = path[5:]
        elif path.startswith("@abs:"):
            p = path[5:]
        else:
            p = os.path.join(self.root, path)
        key = "notebook_path" if tool == "NotebookEdit" else "file_path"
        data = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": "s",
                "cwd": os.path.join(self.root, cwd) if cwd else self.root, "tool_input": {key: p, "content": "SECRET"}}
        if agent is not None:
            data["agent_type"], data["agent_id"] = agent, "a1"
        return data

    def test_table(self):
        self.assertEqual(len({c[0] for c in CASES}), len(CASES))
        for cid, agent, path, cwd, expected in CASES:
            with self.subTest(cid=cid, agent=agent, path=path):
                r = self.run_hook(self.payload(agent, path, cwd))
                self.assertEqual("deny" if r.returncode == 2 else "allow" if r.returncode == 0 else r.returncode,
                                 expected, r.stderr)

    def test_all_file_tools(self):
        for tool in ("Edit", "MultiEdit", "NotebookEdit"):
            with self.subTest(tool=tool):
                self.assertEqual(self.run_hook(self.payload(TL, "invai-backend/src/a.ts", tool=tool)).returncode, 2)
                self.assertEqual(self.run_hook(self.payload(TL, "invai-docs/waves/20/x.ipynb", tool=tool)).returncode, 0)

    def test_denial_names_paths_and_says_write_a_card(self):
        r = self.run_hook(self.payload(TL, "invai-backend/src/a.ts"))
        self.assertIn("write a card for the owner", r.stderr)
        self.assertIn("invai-docs/waves/**", r.stderr)
        self.assertIn(".claude/skills/**", r.stderr)
        r = self.run_hook(self.payload(RV, "invai-docs/waves/20/T-20-4.md"))
        self.assertIn("write a card for the owner", r.stderr)
        self.assertIn("invai-docs/waves/<n>/reviews/**", r.stderr)

    def test_main_session_allowed_and_logged_without_content(self):
        r = self.run_hook(self.payload(None, "invai-backend/src/a.ts"))
        self.assertEqual(r.returncode, 0, r.stderr)
        line = Path(self.log).read_text().strip().splitlines()[-1]
        self.assertIn("\tmain\tWrite\t", line)
        self.assertTrue(line.endswith("invai-backend/src/a.ts"))
        self.assertNotIn("SECRET", Path(self.log).read_text())

    def test_subagent_without_type_allowed_and_logged(self):
        data = self.payload(None, "invai-backend/src/a.ts")
        data["agent_id"] = "abc123"
        self.assertEqual(self.run_hook(data).returncode, 0)
        self.assertIn("no-agent-type agent_id=abc123", Path(self.log).read_text())

    def test_default_log_lives_in_team_state_and_is_ignored(self):
        env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "INVAI_GUARD_PATHS_LOG")}
        env["CLAUDE_PROJECT_DIR"] = self.root
        r = subprocess.run([sys.executable, "-B", str(HOOK)], input=json.dumps(self.payload(None, "CLAUDE.md")),
                           capture_output=True, text=True, env=env, timeout=10)
        self.assertEqual(r.returncode, 0)
        state = Path(self.root, "invai-docs/team/state")
        self.assertEqual(len((state / "guard-paths.log").read_text().splitlines()), 1)
        self.assertEqual((state / ".gitignore").read_text(), "*\n")

    def test_restricted_agents_fail_closed(self):
        self.assertEqual(self.run_hook(self.payload(TL, "CLAUDE.md"), project=False).returncode, 2)  # no workspace
        self.assertEqual(self.run_hook({"tool_name": "Write", "tool_input": {}, "agent_type": TL}).returncode, 2)
        self.assertEqual(self.run_hook({"tool_name": "Write", "tool_input": {"file_path": 5},
                                        "agent_type": RV}).returncode, 2)
        for raw in ("", "not json", "[1]", '{"tool_input": [1], "agent_type": "tech-lead"}',
                    '{"tool_input": {"file_path": "/x"}, "agent_type": 7}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.run_hook(None, raw=raw).returncode, 2)

    def test_other_roles_fail_open(self):
        self.assertEqual(self.run_hook(self.payload("backend-engineer", "CLAUDE.md"), project=False).returncode, 0)
        self.assertEqual(self.run_hook({"tool_name": "Write", "tool_input": {},
                                        "agent_type": "qa-engineer"}).returncode, 0)

    def test_project_dir_in_a_subfolder_or_via_symlink(self):
        sub = os.path.join(self.root, "invai-docs")
        self.assertEqual(self.run_hook(self.payload(TL, "invai-docs/waves/20/x.md"), project=sub).returncode, 0)
        self.assertEqual(self.run_hook(self.payload(TL, "invai-backend/src/a.ts"), project=sub).returncode, 2)
        link = self.root + "-link"
        os.symlink(self.root, link)
        try:
            data = self.payload(TL, "invai-docs/waves/20/x.md")
            data["tool_input"]["file_path"] = os.path.join(link, "invai-docs/waves/20/x.md")
            self.assertEqual(self.run_hook(data, project=link).returncode, 0)
            data["tool_input"]["file_path"] = os.path.join(link, "invai-backend/src/a.ts")
            self.assertEqual(self.run_hook(data, project=link).returncode, 2)
        finally:
            os.unlink(link)

    def test_settings_registers_the_hook(self):
        pre = json.loads(SETTINGS.read_text())["hooks"]["PreToolUse"]
        entry = next(e for e in pre if any("guard-paths.py" in h["command"] for h in e["hooks"]))
        self.assertEqual(set(entry["matcher"].split("|")), {"Write", "Edit", "MultiEdit", "NotebookEdit"})


if __name__ == "__main__":
    unittest.main()
