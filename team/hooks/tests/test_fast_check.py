"""Tests for post-edit-check.py (T-16-1). Uses the real Biome, tsc and ruff through symlinks into scratch
copies of a repo's config; no repo file is touched.

Run: python3 -m unittest discover -s invai-docs/team/hooks/tests
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent
WS = Path("/Users/bekbolsun/invai")
HAVE_TS = (WS / "invai-backend/node_modules/.bin/biome").exists() and (WS / "invai-backend/node_modules/.bin/tsc").exists()
HAVE_RUFF = (WS / "invai-imaging/.venv/bin/ruff").exists()


class FastCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="fastcheck-"))
        self.env = {**os.environ, "INVAI_HOOK_STATE_DIR": os.path.join(self.tmp, "state")}
        self.env.pop("CLAUDE_PROJECT_DIR", None)
        self.be = Path(self.tmp) / "invai-backend"
        (self.be / "src").mkdir(parents=True)
        (self.be / ".git").mkdir()
        for f in ("biome.json", "tsconfig.json"):
            shutil.copy(WS / "invai-backend" / f, self.be / f)
        if HAVE_TS:
            os.symlink(WS / "invai-backend/node_modules", self.be / "node_modules")
        self.im = Path(self.tmp) / "invai-imaging"
        (self.im / "app").mkdir(parents=True)
        (self.im / ".git").mkdir()
        shutil.copy(WS / "invai-imaging/pyproject.toml", self.im / "pyproject.toml")
        if HAVE_RUFF:
            os.symlink(WS / "invai-imaging/.venv", self.im / ".venv")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def check(self, path, raw=None, tool="Edit"):
        payload = raw if raw is not None else json.dumps(
            {"hook_event_name": "PostToolUse", "tool_name": tool, "session_id": "s", "cwd": self.tmp,
             "tool_input": {"file_path": str(path)}})
        t0 = time.time()
        r = subprocess.run([sys.executable, str(HOOKS / "post-edit-check.py")], input=payload,
                           capture_output=True, text=True, env=self.env, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return (json.loads(r.stdout) if r.stdout.strip() else None), time.time() - t0

    @unittest.skipUnless(HAVE_TS, "invai-backend node_modules missing")
    def test_ts_lint_and_type_errors_reach_the_model_file_line_first(self):
        f = self.be / "src/bad.ts"
        f.write_text('export const x: number = "a";\nvar  y = 1\nexport const z = y\n')
        before = hashlib.sha256(f.read_bytes()).hexdigest()
        out, _ = self.check(f)
        self.assertEqual(out["decision"], "block")
        lines = out["reason"].splitlines()
        self.assertTrue(lines[0].startswith("Fast check after editing src/bad.ts"))
        self.assertTrue(all(ln.startswith("src/bad.ts:") for ln in lines[1:]), lines)
        self.assertTrue(any("TS2322" in ln for ln in lines))
        self.assertTrue(any("lint/" in ln or "format" in ln for ln in lines))
        self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(), before, "the fast check must not modify files")

    @unittest.skipUnless(HAVE_TS, "invai-backend node_modules missing")
    def test_clean_ts_file_is_silent(self):
        f = self.be / "src/ok.ts"
        f.write_text("export const ok = 1;\n")
        out, _ = self.check(f, tool="Write")
        self.assertIsNone(out)

    @unittest.skipUnless(HAVE_TS, "invai-backend node_modules missing")
    def test_output_is_capped_at_40_lines(self):
        f = self.be / "src/many.ts"
        f.write_text("".join(f'export const v{i}: number = "s";\n' for i in range(80)))
        out, _ = self.check(f)
        self.assertLessEqual(len(out["reason"].splitlines()), 40)
        self.assertIn("more", out["reason"])

    @unittest.skipUnless(HAVE_TS, "invai-backend node_modules missing")
    def test_json_file_is_linted_not_typechecked(self):
        f = self.be / "package.json"
        f.write_text('{"name":"x",  "version":"1.0.0"}')
        out, _ = self.check(f)
        self.assertIsNotNone(out)
        self.assertNotIn("TS", out["reason"].split(":", 1)[1])

    @unittest.skipUnless(HAVE_RUFF, "invai-imaging .venv missing")
    def test_python_in_imaging_uses_ruff(self):
        f = self.im / "app/bad.py"
        f.write_text("import os\nx = 1\n")
        before = f.read_text()
        out, _ = self.check(f)
        self.assertEqual(out["decision"], "block")
        self.assertIn("app/bad.py:1:8: F401", out["reason"])
        self.assertEqual(f.read_text(), before)

    def test_docs_and_other_files_exit_fast_and_silent(self):
        for p in (WS / "invai-docs/team/lessons.md", self.be / "README.md", self.be / "Dockerfile",
                  Path(self.tmp) / "notes.ts"):
            best = min(self.check(p)[1] for _ in range(3))
            out, _ = self.check(p)
            self.assertIsNone(out, p)
            if p.suffix != ".ts":
                self.assertLess(best, 0.1, f"{p} took {best:.3f}s")

    def test_crash_or_bad_input_fails_open(self):
        for raw in ("", "not json", "[]", '{"tool_input": 7}', '{"tool_input": {"file_path": 7}}'):
            out, _ = self.check(None, raw=raw)
            self.assertIsNone(out)

    def test_missing_tools_fail_open(self):
        wt = Path(self.tmp) / "invai-ui-T-1-1"   # a worktree with no node_modules and no sibling repo
        (wt / "src").mkdir(parents=True)
        (wt / ".git").write_text("gitdir: x\n")
        f = wt / "src/a.ts"
        f.write_text('const x: number = "a"\n')
        out, _ = self.check(f)
        self.assertIsNone(out)

    def test_settings_timeout_and_fail_open_comment(self):
        s = json.loads((HOOKS.parent / "settings.json").read_text())
        post = [hk for m in s["hooks"]["PostToolUse"] for hk in m["hooks"] if "post-edit-check" in hk["command"]]
        self.assertEqual(len(post), 1)
        self.assertLessEqual(post[0]["timeout"], 20)
        src = (HOOKS / "post-edit-check.py").read_text()
        self.assertIn("Fails OPEN, unlike guard-bash.py which fails closed", src)
        guard = s["hooks"]["PreToolUse"][0]
        self.assertEqual(guard, {"matcher": "Bash|mcp__.*", "hooks": [
            {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard-bash.py"}]})


if __name__ == "__main__":
    unittest.main()
