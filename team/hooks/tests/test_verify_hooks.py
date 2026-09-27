"""Tests for track-verify.py and verify-gate.py (T-16-1).

Run: python3 -m unittest discover -s invai-docs/team/hooks/tests   (or python3 -m pytest ... if installed)
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS))
import invai_hooklib as h  # noqa: E402


def make_repo(base, name, worktree=False):
    d = Path(base) / name
    (d / "src").mkdir(parents=True, exist_ok=True)
    if worktree:
        (d / ".git").write_text("gitdir: /elsewhere/.git/worktrees/x\n")
    else:
        (d / ".git").mkdir(exist_ok=True)
    return str(d)


class HookEnv(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="hooktest-"))
        self.state = os.path.join(self.tmp, "state")
        self.ws = os.path.join(self.tmp, "ws")
        self.backend = make_repo(self.ws, "invai-backend")
        self.web = make_repo(self.ws, "invai-web")
        self.imaging = make_repo(self.ws, "invai-imaging")
        self.infra = make_repo(self.ws, "invai-infra")
        self.docs = make_repo(self.ws, "invai-docs")
        self.wt = make_repo(self.ws, "invai-backend-T-99-1", worktree=True)
        self.env = {**os.environ, "INVAI_HOOK_STATE_DIR": self.state}
        self.env.pop("CLAUDE_PROJECT_DIR", None)

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.tmp])

    def run_hook(self, script, payload, raw=None):
        stdin = raw if raw is not None else json.dumps(payload)
        r = subprocess.run([sys.executable, str(HOOKS / script)], input=stdin, capture_output=True,
                           text=True, env=self.env, timeout=30)
        return r

    def edit(self, path, agent=None, tool="Edit", session="s1"):
        p = {"hook_event_name": "PostToolUse", "session_id": session, "cwd": self.ws, "tool_name": tool,
             "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"}, "tool_response": {}}
        if agent:
            p["agent_id"], p["agent_type"] = agent, "backend-engineer"
        r = self.run_hook("track-verify.py", p)
        self.assertEqual(r.returncode, 0, r.stderr)
        time.sleep(0.01)

    def bash(self, cmd, cwd=None, agent=None, event="PostToolUse", stdout="", duration_ms=5, session="s1", **extra):
        p = {"hook_event_name": event, "session_id": session, "cwd": cwd or self.ws, "tool_name": "Bash",
             "tool_input": {"command": cmd, **extra}, "duration_ms": duration_ms}
        if event == "PostToolUse":
            p["tool_response"] = {"stdout": stdout, "stderr": "", "interrupted": False}
        else:
            p["error"] = "Exit code 1"
        if agent:
            p["agent_id"], p["agent_type"] = agent, "backend-engineer"
        r = self.run_hook("track-verify.py", p)
        self.assertEqual(r.returncode, 0, r.stderr)
        time.sleep(0.01)

    def stop(self, agent=None, active=False, session="s1"):
        p = {"session_id": session, "cwd": self.ws, "stop_hook_active": active,
             "hook_event_name": "SubagentStop" if agent else "Stop"}
        if agent:
            p["agent_id"], p["agent_type"] = agent, "backend-engineer"
        r = self.run_hook("verify-gate.py", p)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None


class TestGate(HookEnv):
    def test_code_edit_without_checks_blocks_once_with_commands(self):
        self.edit(f"{self.backend}/src/a.ts", agent="a1")
        out = self.stop(agent="a1")
        self.assertEqual(out["decision"], "block")
        self.assertIn(f"cd {self.backend} && pnpm typecheck && pnpm lint && pnpm test", out["reason"])
        self.assertIn("If you can't make them pass, stop and report the failure honestly.", out["reason"])
        self.assertIsNone(self.stop(agent="a1", active=True))  # stop_hook_active lets it through
        self.assertIsNone(self.stop(agent="a1"))  # same edit state: not blocked again
        self.edit(f"{self.backend}/src/b.ts", agent="a1")
        self.assertEqual(self.stop(agent="a1")["decision"], "block")  # new edit: blocks again

    def test_stop_hook_active_always_allows(self):
        self.edit(f"{self.backend}/src/a.ts")
        self.assertIsNone(self.stop(active=True))

    def test_chained_checks_after_edit_allow_stop(self):
        self.edit(f"{self.backend}/src/a.ts", agent="a1")
        self.bash("export PATH=x:$PATH && cd invai-backend && pnpm typecheck && pnpm lint && pnpm test", agent="a1")
        self.assertIsNone(self.stop(agent="a1"))

    def test_separate_commands_and_forms_count(self):
        self.edit(f"{self.backend}/src/a.ts")
        self.bash("pnpm -C invai-backend typecheck")
        self.bash("pnpm --dir invai-backend lint 2>&1 | tail -3", stdout="Checked 10 files. No fixes applied.")
        self.bash("node_modules/.bin/vitest run", cwd=self.backend)
        self.assertIsNone(self.stop())

    def test_failed_test_run_is_not_counted(self):
        self.edit(f"{self.backend}/src/a.ts")
        self.bash("pnpm typecheck && pnpm lint", cwd=self.backend)
        self.bash("pnpm test", cwd=self.backend, event="PostToolUseFailure")
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("pnpm test", out["reason"])
        self.assertNotIn("pnpm typecheck", out["reason"])

    def test_piped_failure_is_not_counted(self):
        self.edit(f"{self.backend}/src/a.ts")
        self.bash("pnpm typecheck && pnpm lint", cwd=self.backend)
        self.bash("pnpm test 2>&1 | tail -5", cwd=self.backend, stdout=" Tests  2 failed | 40 passed\n ELIFECYCLE")
        self.assertEqual(self.stop()["decision"], "block")
        self.bash("pnpm test 2>&1 | tail -5", cwd=self.backend, stdout=" Tests  42 passed (42)")
        self.assertIsNone(self.stop())

    def test_partial_or_masked_runs_do_not_count(self):
        self.edit(f"{self.backend}/src/a.ts")
        for cmd in ("pnpm test src/modules/orders", "pnpm test || true", "pnpm test; echo done",
                    "pnpm vitest run -t orders", "pnpm test &", "node_modules/.bin/biome check src/a.ts",
                    "pnpm typecheck; pnpm lint; pnpm test"):
            self.bash(cmd, cwd=self.backend)
        state = h.read_state(Path(self.state) / "verify__s1__main.json")
        self.assertEqual(set(state["repos"][self.backend]["ok"]), {"test"})  # only the trailing `pnpm test`
        self.assertEqual(self.stop()["decision"], "block")

    def test_check_that_started_before_the_edit_does_not_count(self):
        self.edit(f"{self.backend}/src/a.ts")
        self.bash("pnpm typecheck && pnpm lint && pnpm test", cwd=self.backend, duration_ms=60_000)
        self.assertEqual(self.stop()["decision"], "block")

    def test_checks_before_edit_do_not_count(self):
        self.edit(f"{self.backend}/src/a.ts")
        self.bash("pnpm typecheck && pnpm lint && pnpm test", cwd=self.backend)
        self.edit(f"{self.backend}/src/a.ts")
        self.assertEqual(self.stop()["decision"], "block")

    def test_background_command_is_not_counted(self):
        self.edit(f"{self.backend}/src/a.ts")
        self.bash("pnpm typecheck && pnpm lint && pnpm test", cwd=self.backend, run_in_background=True)
        self.assertEqual(self.stop()["decision"], "block")

    def test_web_needs_build(self):
        self.edit(f"{self.web}/src/App.tsx")
        self.bash("cd invai-web && pnpm typecheck && pnpm lint && pnpm test")
        out = self.stop()
        self.assertIn(f"cd {self.web} && pnpm build", out["reason"])
        self.bash("(cd invai-web && pnpm build)")
        self.assertIsNone(self.stop())

    def test_imaging_and_infra_commands(self):
        self.edit(f"{self.imaging}/app/nest.py")
        self.edit(f"{self.infra}/sst.config.ts")
        out = self.stop()
        self.assertIn(f"cd {self.imaging} && uv run ruff check . && uv run pytest", out["reason"])
        self.assertIn(f"cd {self.infra} && pnpm typecheck && pnpm lint", out["reason"])
        self.assertNotIn("pnpm test", out["reason"])
        self.bash(f"cd {self.imaging} && uv run ruff check . && uv run pytest -q")
        self.bash("cd invai-infra && pnpm typecheck && pnpm lint")
        self.assertIsNone(self.stop())

    def test_worktree_path(self):
        self.edit(f"{self.wt}/src/a.ts", agent="a1")
        out = self.stop(agent="a1")
        self.assertIn(f"cd {self.wt} && node_modules/.bin/tsc --noEmit && node_modules/.bin/biome check . "
                      "&& node_modules/.bin/vitest run", out["reason"])
        self.bash("node_modules/.bin/tsc --noEmit && node_modules/.bin/biome check . && node_modules/.bin/vitest run",
                  cwd=self.wt, agent="a1")
        self.assertIsNone(self.stop(agent="a1"))

    def test_docs_only_edits_never_block(self):
        self.edit(f"{self.docs}/waves/16/wave.md")
        self.edit(f"{self.docs}/team/hooks/x.py")  # invai-docs isn't a code repo
        self.edit(f"{self.backend}/README.md")
        self.edit(f"{self.backend}/docs/diagram.png", tool="Write")
        self.assertIsNone(self.stop())
        self.assertFalse((Path(self.state) / "verify__s1__main.json").exists())

    def test_read_only_agent_never_blocks(self):
        self.bash("git status && pnpm test", cwd=self.backend, agent="r1")
        self.assertIsNone(self.stop(agent="r1"))
        self.assertEqual(list(Path(self.state).glob("verify__*")), [])

    def test_agents_are_tracked_separately(self):
        self.edit(f"{self.backend}/src/a.ts", agent="a1")
        self.assertIsNone(self.stop())  # main session didn't edit code
        self.assertIsNone(self.stop(agent="a2"))
        self.assertIsNone(self.stop(agent="a1", session="other-session"))
        self.bash("pnpm typecheck && pnpm lint && pnpm test", cwd=self.backend)  # main's checks don't clear a1
        self.assertEqual(self.stop(agent="a1")["decision"], "block")

    def test_write_and_multiedit_and_relative_paths(self):
        self.edit("invai-backend/src/new.ts", tool="Write")
        self.edit(f"{self.web}/src/x.ts", tool="MultiEdit")
        out = self.stop()
        self.assertIn("invai-backend:", out["reason"])
        self.assertIn("invai-web:", out["reason"])

    def test_malformed_input_fails_open(self):
        for script in ("track-verify.py", "verify-gate.py"):
            for raw in ("", "not json", "[1,2]", '{"tool_name": 5}'):
                r = self.run_hook(script, None, raw=raw)
                self.assertEqual(r.returncode, 0, (script, raw, r.stderr))
                self.assertEqual(r.stdout.strip(), "", (script, raw))

    def test_state_is_atomic_json_and_old_files_are_pruned(self):
        Path(self.state).mkdir(parents=True, exist_ok=True)
        old = Path(self.state) / "verify__old__main.json"
        old.write_text("{}")
        three_days = time.time() - 3 * 24 * 3600
        os.utime(old, (three_days, three_days))
        self.edit(f"{self.backend}/src/a.ts")
        self.assertFalse(old.exists())
        f = Path(self.state) / "verify__s1__main.json"
        self.assertIn(self.backend, json.loads(f.read_text())["repos"])
        self.assertEqual((Path(self.state) / ".gitignore").read_text(), "*\n")
        self.assertEqual(list(Path(self.state).glob(".tmp-*")), [])

    def test_concurrent_updates_keep_every_repo(self):
        procs = []
        for repo in (self.backend, self.web, self.imaging, self.infra, self.wt):
            p = {"hook_event_name": "PostToolUse", "session_id": "s1", "cwd": self.ws, "tool_name": "Edit",
                 "tool_input": {"file_path": f"{repo}/src/a.ts"}}
            procs.append(subprocess.Popen([sys.executable, str(HOOKS / "track-verify.py")], stdin=subprocess.PIPE,
                                          env=self.env, text=True))
            procs[-1].stdin.write(json.dumps(p))
            procs[-1].stdin.close()
        for p in procs:
            p.wait(timeout=30)
        state = json.loads((Path(self.state) / "verify__s1__main.json").read_text())
        self.assertEqual(len(state["repos"]), 5)


class TestParser(unittest.TestCase):
    """parse_verifications on the real workspace layout (read-only: only checks that .git exists)."""

    W = "/Users/bekbolsun/invai"

    def found(self, cmd, cwd=None, out=""):
        return sorted((os.path.basename(r), c) for r, _k, c in h.parse_verifications(cmd, cwd or self.W, out))

    @unittest.skipUnless(os.path.isdir("/Users/bekbolsun/invai/invai-backend/.git"), "workspace not present")
    def test_forms(self):
        B = f"{self.W}/invai-backend"
        self.assertEqual(self.found("cd invai-backend && pnpm typecheck && pnpm lint && pnpm test"),
                         [("invai-backend", "lint"), ("invai-backend", "test"), ("invai-backend", "typecheck")])
        self.assertEqual(self.found("pnpm run test", B), [("invai-backend", "test")])
        self.assertEqual(self.found("perl -e 'alarm 120; exec @ARGV' pnpm test", B), [("invai-backend", "test")])
        self.assertEqual(self.found("TEST_DATABASE_URL=postgres://x pnpm test", B), [("invai-backend", "test")])
        self.assertEqual(self.found("cd invai-ui && \\\n node_modules/.bin/biome check . && node_modules/.bin/vitest run"),
                         [("invai-ui", "lint"), ("invai-ui", "test")])
        self.assertEqual(self.found("pnpm exec tsc --noEmit", B), [("invai-backend", "typecheck")])
        self.assertEqual(self.found("uv run pytest", B), [])  # a python tool doesn't verify a TS repo
        self.assertEqual(self.found("pnpm test", f"{self.W}/invai-imaging"), [])
        self.assertEqual(self.found("uv --directory invai-imaging run ruff check ."), [("invai-imaging", "lint")])
        self.assertEqual(self.found("cd - && pnpm test", B), [])
        self.assertEqual(self.found("pnpm test", self.W), [])  # not inside a repo


if __name__ == "__main__":
    unittest.main()
