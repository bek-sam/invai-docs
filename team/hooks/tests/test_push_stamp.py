"""Tests for the T-23-6 pre-push gate stamp check in guard-bash.py (AC5, AC6).

`pnpm gate` (invai-infra/scripts/gate.sh) writes invai-infra/.gate/pass.json on a full pass:
{"repos": {"invai-<kind>": {"sha": "<HEAD sha>", "at": "<UTC ISO time>"}, ...}}. guard-bash.py
refuses `git push` of a code repo to main unless that repo has a fresh (<24h), matching entry.
invai-docs (docs-only) is exempt, and every existing guard rule (force-push, role, etc.) still
applies on top of this check.

Uses the real repos already checked out next to this workspace (invai-contracts, invai-docs) as
the "which repo is this" anchor, and INVAI_GATE_STAMP_PATH (read only from the guard's own process
environment, never from the checked command's text) to point at a scratch stamp file per case, so
no test touches the real invai-infra/.gate/pass.json.

Run: python3 -B -m unittest discover -s .claude/hooks/tests -p 'test_push_stamp.py'
"""
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "guard-bash.py"
# The live workspace (as test_fast_check.py): these tests run from .claude/hooks/tests,
# invai-docs/team/hooks/tests or a scratch copy, so the repos can't be found relative to this file.
WORKSPACE = Path(os.environ.get("INVAI_WORKSPACE", "/Users/bekbolsun/invai"))
CONTRACTS = str(WORKSPACE / "invai-contracts")
DOCS = str(WORKSPACE / "invai-docs")

CONTRACTS_SHA = subprocess.run(["git", "-C", CONTRACTS, "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()


def run(cmd, cwd, stamp_path, agent_type="tech-lead"):
    payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd}
    if agent_type is not None:
        payload["agent_type"] = agent_type
    env = dict(os.environ)
    if stamp_path is not None:
        env["INVAI_GATE_STAMP_PATH"] = stamp_path
    else:
        env.pop("INVAI_GATE_STAMP_PATH", None)
    return subprocess.run(["python3", "-B", str(GUARD)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=20, env=env)


def decision(r):
    if r.returncode == 2:
        return "deny"
    if r.returncode == 0 and r.stdout.strip():
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"]
    if r.returncode == 0:
        return "allow"
    return f"error rc={r.returncode}"


def write_stamp(path, sha, at):
    with open(path, "w") as f:
        json.dump({"repos": {"invai-contracts": {"sha": sha, "at": at}}}, f)


class TestPushStamp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def stamp_path(self, name="pass.json"):
        return os.path.join(self.tmp.name, name)

    def now_iso(self, delta=timedelta()):
        return (datetime.now(timezone.utc) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- AC6 case 1: a matching, fresh stamp allows the push ---
    def test_matching_fresh_stamp_allows(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())
        r = run("git push origin main", CONTRACTS, sp)
        self.assertEqual(decision(r), "allow", r.stderr)

    # --- AC6 case 2: a stamp with a stale SHA blocks ---
    def test_stale_sha_blocks(self):
        sp = self.stamp_path()
        write_stamp(sp, "0" * 40, self.now_iso())
        r = run("git push origin main", CONTRACTS, sp)
        self.assertEqual(decision(r), "deny")
        self.assertIn("stale", r.stderr)
        self.assertIn("pnpm gate", r.stderr)

    # --- AC6 case 3: an old stamp (>24h) blocks even with a matching SHA ---
    def test_old_stamp_blocks(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso(timedelta(hours=-25)))
        r = run("git push origin main", CONTRACTS, sp)
        self.assertEqual(decision(r), "deny")
        self.assertIn("24h", r.stderr)

    def test_stamp_just_under_24h_allows(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso(timedelta(hours=-23, minutes=-55)))
        r = run("git push origin main", CONTRACTS, sp)
        self.assertEqual(decision(r), "allow", r.stderr)

    # --- AC6 case 4: a forced push is still blocked, even with a fresh matching stamp ---
    def test_forced_push_still_blocked(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())
        r = run("git push --force origin main", CONTRACTS, sp)
        self.assertEqual(decision(r), "deny")
        self.assertIn("force-push", r.stderr)

    def test_force_with_lease_still_blocked(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())
        r = run("git push --force-with-lease origin main", CONTRACTS, sp)
        self.assertEqual(decision(r), "deny")

    # --- missing stamp / missing entry ---
    def test_missing_stamp_file_blocks(self):
        r = run("git push origin main", CONTRACTS, self.stamp_path("does-not-exist.json"))
        self.assertEqual(decision(r), "deny")
        self.assertIn("pnpm gate", r.stderr)

    def test_stamp_without_this_repos_entry_blocks(self):
        sp = self.stamp_path()
        with open(sp, "w") as f:
            json.dump({"repos": {"invai-web": {"sha": "a" * 40, "at": self.now_iso()}}}, f)
        r = run("git push origin main", CONTRACTS, sp)
        self.assertEqual(decision(r), "deny")

    # --- invai-docs (docs-only) is exempt, even with no stamp at all ---
    def test_docs_repo_exempt(self):
        r = run("git push origin main", DOCS, self.stamp_path("does-not-exist.json"))
        self.assertEqual(decision(r), "allow", r.stderr)

    # --- a push whose repo can't be identified at all (no known .git above cwd) falls back to
    # the existing rules only, so it doesn't regress the adversarial suite's plain "git push" cases ---
    def test_unidentifiable_repo_falls_back_to_existing_rules(self):
        r = run("git push origin main", "/tmp", self.stamp_path("does-not-exist.json"))
        self.assertEqual(decision(r), "allow", r.stderr)

    # --- role gating still applies on top of a good stamp ---
    def test_non_tech_lead_still_denied_regardless_of_stamp(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())
        r = run("git push origin main", CONTRACTS, sp, agent_type="backend-engineer")
        self.assertEqual(decision(r), "deny")
        self.assertIn("only the tech lead pushes", r.stderr)

    def test_main_session_with_good_stamp_allows(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())
        r = run("git push origin main", CONTRACTS, sp, agent_type=None)
        self.assertEqual(decision(r), "allow", r.stderr)


class TestPushStampRepoResolution(unittest.TestCase):
    """T-23-6 r2 finding 1: the repo a push targets must be resolved from cd/pushd/subshells/
    --git-dir/GIT_DIR, or the whole push is denied. Every case here starts from the WORKSPACE
    root (not the repo itself, unlike TestPushStamp above), the form the round-1 review proved
    bypassed the stamp check entirely (no repo resolved -> "nothing of ours to gate" -> allowed
    with no stamp at all)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def stamp_path(self, name="pass.json"):
        return os.path.join(self.tmp.name, name)

    def now_iso(self, delta=timedelta()):
        return (datetime.now(timezone.utc) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")

    def fresh_stamp(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())
        return sp

    # --- cd, from the workspace root, before a bare `git push` ---
    def test_cd_then_push_with_and_allows(self):
        r = run("cd invai-contracts && git push origin main", str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "allow", r.stderr)

    def test_cd_then_push_with_semicolon_allows(self):
        r = run("cd invai-contracts; git push origin main", str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "allow", r.stderr)

    def test_cd_in_subshell_then_push_allows(self):
        r = run("(cd invai-contracts && git push origin main)", str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "allow", r.stderr)

    def test_pushd_then_push_allows(self):
        r = run("pushd invai-contracts && git push origin main", str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "allow", r.stderr)

    def test_bash_c_cd_then_push_allows(self):
        r = run("bash -c 'cd invai-contracts && git push origin main'", str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "allow", r.stderr)

    def test_git_dir_env_prefix_allows(self):
        r = run("GIT_DIR=invai-contracts/.git git push origin main", str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "allow", r.stderr)

    def test_git_dir_flag_equals_form_allows(self):
        r = run(f"git --git-dir={CONTRACTS}/.git push origin main", "/tmp", self.fresh_stamp())
        self.assertEqual(decision(r), "allow", r.stderr)

    def test_cd_resolves_docs_and_stays_exempt(self):
        # Positively resolving to invai-docs (not just falling through unresolved) still exempts
        # it, even with no stamp at all.
        r = run("cd invai-docs && git push origin main", str(WORKSPACE), self.stamp_path("none.json"))
        self.assertEqual(decision(r), "allow", r.stderr)

    # --- the same forms with a stale or missing stamp: must now DENY, not silently allow ---
    def test_cd_then_push_with_no_stamp_denies(self):
        r = run("cd invai-contracts && git push origin main", str(WORKSPACE), self.stamp_path("none.json"))
        self.assertEqual(decision(r), "deny")
        self.assertIn("pnpm gate", r.stderr)

    def test_cd_then_push_with_stale_stamp_denies(self):
        sp = self.stamp_path()
        write_stamp(sp, "0" * 40, self.now_iso())
        r = run("cd invai-contracts && git push origin main", str(WORKSPACE), sp)
        self.assertEqual(decision(r), "deny")
        self.assertIn("stale", r.stderr)

    # --- loops/variables the guard truly cannot resolve: deny, regardless of any stamp ---
    def test_loop_variable_dash_c_denies_with_fresh_stamp(self):
        r = run("for r in invai-contracts; do git -C $r push origin main; done",
                str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "deny")
        self.assertIn("git -C /abs/path/<repo>", r.stderr)

    def test_loop_variable_dash_c_denies_with_no_stamp(self):
        r = run("for r in invai-contracts; do git -C $r push origin main; done",
                str(WORKSPACE), self.stamp_path("none.json"))
        self.assertEqual(decision(r), "deny")
        self.assertIn("git -C /abs/path/<repo>", r.stderr)

    def test_cd_dash_denies(self):
        r = run("cd invai-contracts && cd - && git push origin main", str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "deny")

    def test_popd_denies(self):
        r = run("pushd invai-contracts && popd && git push origin main", str(WORKSPACE), self.fresh_stamp())
        self.assertEqual(decision(r), "deny")

    # --- an unresolvable case still doesn't regress the plain "outside any repo" fallback ---
    def test_still_allows_when_genuinely_outside_any_repo(self):
        r = run("git push origin main", "/tmp", self.stamp_path("none.json"))
        self.assertEqual(decision(r), "allow", r.stderr)


class TestPushStampRefspec(unittest.TestCase):
    """T-23-6 r2 finding 5: the stamp must be compared with the commit actually being pushed
    (the refspec's source), not always the repo's local HEAD."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def stamp_path(self, name="pass.json"):
        return os.path.join(self.tmp.name, name)

    def now_iso(self, delta=timedelta()):
        return (datetime.now(timezone.utc) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")

    def test_explicit_main_to_main_refspec_allows(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())
        r = run("git push origin main:main", CONTRACTS, sp)
        self.assertEqual(decision(r), "allow", r.stderr)

    def test_other_commit_as_source_denies_even_with_fresh_head_stamp(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())  # a fresh, matching stamp for HEAD
        r = run("git push origin HEAD~1:main", CONTRACTS, sp)  # but pushing a DIFFERENT commit
        self.assertEqual(decision(r), "deny")
        self.assertIn("stale", r.stderr)

    def test_nonexistent_branch_source_denies(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso())
        r = run("git push origin no-such-branch-xyz:main", CONTRACTS, sp)
        self.assertEqual(decision(r), "deny")
        self.assertIn("can't resolve", r.stderr)


if __name__ == "__main__":
    unittest.main()
