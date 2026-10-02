"""Tests for the pre-push gate in guard-bash.py (T-23-6 round 3, card T-P8-3, owner OI-22 answer A).

A code repo (invai-backend, -web, -floor, -ui, -contracts, -imaging, -infra) is pushed only as the
whole Bash command `git -C /Users/bekbolsun/invai/<repo> push origin main|<sha>:main`, and then only
with a fresh (<24h) `pnpm gate` stamp in invai-infra/.gate/pass.json whose SHA is the commit being
pushed. Every other push form is refused with one message naming that form, unless the push is
positively invai-docs (`git -C /Users/bekbolsun/invai/invai-docs push ...`, a top-level command).
Force, tag, mirror, all, delete and role rules still apply on top.

The stamp is read from INVAI_GATE_STAMP_PATH (the guard's own process environment, never the
checked command) pointing at a scratch file per case, so no test touches the real stamp. The allowed
form names a real workspace repo, so the guard reads invai-contracts' commits (read-only rev-parse);
nothing is pushed: the guard only decides.

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


def _git(*args):
    return subprocess.run(["git", "-C", CONTRACTS, *args], capture_output=True, text=True, check=True).stdout.strip()


CONTRACTS_SHA = _git("rev-parse", "main")
PREV_SHA = _git("rev-parse", "main~1")
FORM = f"git -C {CONTRACTS} push origin main"  # the one allowed form
FORM_MSG = "git -C /Users/bekbolsun/invai/<repo> push origin main"


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


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def stamp_path(self, name="pass.json"):
        return os.path.join(self.tmp.name, name)

    def now_iso(self, delta=timedelta()):
        return (datetime.now(timezone.utc) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")

    def fresh_stamp(self, sha=CONTRACTS_SHA):
        sp = self.stamp_path()
        write_stamp(sp, sha, self.now_iso())
        return sp

    def no_stamp(self):
        return self.stamp_path("does-not-exist.json")

    def assertDecision(self, cmd, expected, stamp, cwd=None, agent_type="tech-lead", msg=None):
        r = run(cmd, cwd or str(WORKSPACE), stamp, agent_type)
        self.assertEqual(decision(r), expected, f"{cmd!r}: {r.stderr}")
        if msg:
            self.assertIn(msg, r.stderr)
        return r


class TestOneFormStamp(Base):
    """AC1 and AC4: the exact form, gated by the stamp."""

    def test_matching_fresh_stamp_allows(self):
        self.assertDecision(FORM, "allow", self.fresh_stamp())

    def test_form_allows_from_any_cwd(self):
        self.assertDecision(FORM, "allow", self.fresh_stamp(), cwd="/tmp")
        self.assertDecision(FORM, "allow", self.fresh_stamp(), cwd=DOCS)

    def test_sha_to_main_allows(self):
        self.assertDecision(f"git -C {CONTRACTS} push origin {CONTRACTS_SHA}:main", "allow", self.fresh_stamp())

    def test_short_sha_to_main_allows(self):
        self.assertDecision(f"git -C {CONTRACTS} push origin {CONTRACTS_SHA[:7]}:main", "allow", self.fresh_stamp())

    def test_stale_sha_blocks(self):
        self.assertDecision(FORM, "deny", self.fresh_stamp("0" * 40), msg="stale")

    def test_other_commit_as_source_denies_even_with_fresh_head_stamp(self):
        self.assertDecision(f"git -C {CONTRACTS} push origin {PREV_SHA}:main", "deny", self.fresh_stamp(),
                            msg="stale")

    def test_unknown_sha_denies(self):
        self.assertDecision(f"git -C {CONTRACTS} push origin 0000000deadbeef:main", "deny", self.fresh_stamp(),
                            msg="can't resolve")

    def test_old_stamp_blocks(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso(timedelta(hours=-25)))
        self.assertDecision(FORM, "deny", sp, msg="24h")
        self.assertDecision(f"git -C {CONTRACTS} push origin {CONTRACTS_SHA}:main", "deny", sp, msg="24h")

    def test_stamp_just_under_24h_allows(self):
        sp = self.stamp_path()
        write_stamp(sp, CONTRACTS_SHA, self.now_iso(timedelta(hours=-23, minutes=-55)))
        self.assertDecision(FORM, "allow", sp)

    def test_missing_stamp_file_blocks(self):
        self.assertDecision(FORM, "deny", self.no_stamp(), msg="pnpm gate")

    def test_stamp_without_this_repos_entry_blocks(self):
        sp = self.stamp_path()
        with open(sp, "w") as f:
            json.dump({"repos": {"invai-web": {"sha": "a" * 40, "at": self.now_iso()}}}, f)
        self.assertDecision(FORM, "deny", sp, msg="no gate stamp for invai-contracts")

    def test_unreadable_stamp_blocks(self):
        sp = self.stamp_path()
        with open(sp, "w") as f:
            f.write("[1, 2")
        self.assertDecision(FORM, "deny", sp, msg="pnpm gate")
        with open(sp, "w") as f:
            json.dump({"repos": {"invai-contracts": {"sha": CONTRACTS_SHA, "at": "yesterday"}}}, f)
        self.assertDecision(FORM, "deny", sp, msg="unreadable time")

    def test_non_tech_lead_still_denied_regardless_of_stamp(self):
        self.assertDecision(FORM, "deny", self.fresh_stamp(), agent_type="backend-engineer",
                            msg="only the tech lead pushes")

    def test_main_session_with_good_stamp_allows(self):
        self.assertDecision(FORM, "allow", self.fresh_stamp(), agent_type=None)


class TestExistingPushGuards(Base):
    """AC3: force, tag, mirror, all and delete pushes stay denied, in the exact form and with a fresh stamp."""

    def test_forced_push_still_blocked(self):
        for flag in ("--force", "-f", "--force-with-lease", "--force-if-includes"):
            self.assertDecision(f"git -C {CONTRACTS} push {flag} origin main", "deny", self.fresh_stamp(),
                                msg="force-push")

    def test_force_with_lease_still_blocked(self):
        self.assertDecision(f"git -C {CONTRACTS} push --force-with-lease origin main", "deny", self.fresh_stamp())

    def test_plus_refspec_still_blocked(self):
        self.assertDecision(f"git -C {CONTRACTS} push origin +main", "deny", self.fresh_stamp(), msg="force-push")
        self.assertDecision(f"git -C {CONTRACTS} push origin +{CONTRACTS_SHA}:main", "deny", self.fresh_stamp())

    def test_tags_mirror_all_delete_still_blocked(self):
        for args in ("--tags origin main", "--mirror origin", "--all origin", "--delete origin main",
                     "origin :main", "origin v1.0.0"):
            self.assertDecision(f"git -C {CONTRACTS} push {args}", "deny", self.fresh_stamp())
            self.assertDecision(f"git -C {DOCS} push {args}", "deny", self.no_stamp())


class TestEveryOtherFormDenied(Base):
    """AC2 and AC4: every other way to push a code repo is refused with the one message, even with a
    fresh matching stamp (S-42, T-23-6 r2 findings 1 and 2)."""

    DENIED = [
        "cd invai-contracts && git push origin main",
        f"cd {CONTRACTS} && git push origin main",
        "cd invai-contracts; git push origin main",
        "(cd invai-contracts && git push origin main)",
        "pushd invai-contracts && git push origin main",
        f"{FORM} 2>&1 | tail -3",
        f"{FORM} 2>&1",
        f"{FORM} 2>/dev/null",
        f"{FORM} > /tmp/push.log",
        f"{FORM}; echo done",
        f"{FORM} && echo done",
        f"echo start && {FORM}",
        f"{FORM} &",
        "git -C ~/invai/invai-contracts push origin main",
        "cd ~/invai/invai-contracts && git push origin main",
        "git -C $HOME/invai/invai-contracts push origin main",
        "git -C /Users/bekbolsun/invai/invai-{contracts,x} push origin main",
        "git -C /Users/bekbolsun/invai/invai-contract? push origin main",
        "git -C /Users/bekbolsun/invai/invai-docs/../invai-contracts push origin main",
        "echo invai-contracts | xargs -I{} git -C {} push origin main",
        f"echo x | xargs {FORM}",
        "find . -maxdepth 1 -name invai-contracts -exec git -C {} push origin main \\;",
        f"echo $({FORM})",
        f"$({FORM})",
        f"echo `{FORM}`",
        f"bash -c '{FORM}'",
        f"sh -c '{FORM}'",
        f"eval '{FORM}'",
        f"bash <<< '{FORM}'",
        f"echo '{FORM}' | bash",
        f"env {FORM}",
        f"GIT_TRACE=1 {FORM}",
        f"command {FORM}",
        f"timeout 60 {FORM}",
        "git -C invai-contracts push origin main",
        "git -C ./invai-contracts push origin main",
        f"git -C {CONTRACTS}/ push origin main",
        f"git -C '{CONTRACTS}' push origin main",
        f"git  -C {CONTRACTS} push origin main",
        f"git -C {CONTRACTS} push origin HEAD:main",
        f"git -C {CONTRACTS} push origin main:main",
        f"git -C {CONTRACTS} push origin",
        f"git -C {CONTRACTS} push",
        f"git -C {CONTRACTS} push -u origin main",
        f"git -C {CONTRACTS} push --dry-run origin main",
        f"git -C {CONTRACTS} push upstream main",
        f"git -C {CONTRACTS} push origin main other",
        f"git -C {CONTRACTS} push origin {CONTRACTS_SHA}:refs/heads/main",
        f"git -C {CONTRACTS} push origin {CONTRACTS_SHA.upper()}:main",
        f"git -C {CONTRACTS} -C . push origin main",
        f"git --git-dir={CONTRACTS}/.git push origin main",
        f"GIT_DIR={CONTRACTS}/.git git push origin main",
        f"git -C {CONTRACTS} send-pack origin main",
        f"git -C {WORKSPACE}/invai-backend-T-22-1-rev push origin main",
        "for r in invai-contracts; do git -C $r push origin main; done",
        f"git() {{ command git \"$@\"; }}; {FORM}",
    ]

    def test_every_other_form_denied_with_fresh_stamp(self):
        sp = self.fresh_stamp()
        for cmd in self.DENIED:
            with self.subTest(cmd=cmd):
                self.assertDecision(cmd, "deny", sp)

    def test_every_other_form_denied_with_no_stamp(self):
        sp = self.no_stamp()
        for cmd in self.DENIED:
            with self.subTest(cmd=cmd):
                self.assertDecision(cmd, "deny", sp)

    def test_deny_message_names_the_form(self):
        for cmd in ("cd invai-contracts && git push origin main", f"{FORM} 2>&1 | tail -3",
                    "git -C ~/invai/invai-contracts push origin main", f"bash -c '{FORM}'"):
            with self.subTest(cmd=cmd):
                self.assertDecision(cmd, "deny", self.fresh_stamp(), msg=FORM_MSG)

    def test_plain_push_in_a_code_repo_cwd_denied(self):
        self.assertDecision("git push origin main", "deny", self.fresh_stamp(), cwd=CONTRACTS, msg=FORM_MSG)
        self.assertDecision("git push", "deny", self.fresh_stamp(), cwd=CONTRACTS, msg=FORM_MSG)

    def test_push_outside_any_repo_denied(self):
        # Round 2 allowed this as "certainly outside our repos"; round 3 refuses anything not positively docs.
        self.assertDecision("git push origin main", "deny", self.no_stamp(), cwd="/tmp", msg=FORM_MSG)

    def test_push_inside_a_script_denied(self):
        script = os.path.join(self.tmp.name, "p.sh")
        with open(script, "w") as f:
            f.write(FORM + "\n")
        self.assertDecision(f"bash {script}", "deny", self.fresh_stamp(), msg=FORM_MSG)
        with open(script, "w") as f:
            f.write(f"git -C {DOCS} push origin main\n")
        self.assertDecision(f"bash {script}", "deny", self.no_stamp(), msg=FORM_MSG)


class TestDocsPush(Base):
    """AC2: invai-docs keeps working without a stamp, but only when positively identified."""

    def test_docs_push_allowed_without_stamp(self):
        for cmd in (f"git -C {DOCS} push origin main", f"git -C {DOCS}/ push origin main",
                    f"git -C {DOCS} push", f"git -C {DOCS} push -u origin main",
                    f"git -C {DOCS} push origin main 2>&1 | tail -3",
                    f"git -C {DOCS} push origin main; git -C {DOCS} log -1 --format=%h | tr -d x",
                    f"export PATH=\"$HOME/.local/share/pnpm/bin:$PATH\"; git -C {DOCS} push origin main"):
            with self.subTest(cmd=cmd):
                self.assertDecision(cmd, "allow", self.no_stamp())
        self.assertDecision(f"git -C {DOCS} push origin main", "allow", self.no_stamp(), cwd="/tmp")

    def test_docs_not_positively_identified_denied(self):
        for cmd, cwd in (("git push origin main", DOCS),
                         ("cd invai-docs && git push origin main", str(WORKSPACE)),
                         ("git -C invai-docs push origin main", str(WORKSPACE)),
                         ("git -C ~/invai/invai-docs push origin main", str(WORKSPACE)),
                         (f"GIT_DIR={CONTRACTS}/.git git -C {DOCS} push origin main", str(WORKSPACE)),
                         (f"export GIT_DIR={CONTRACTS}/.git; git -C {DOCS} push origin main", str(WORKSPACE)),
                         (f"read G''IT_DIR <<< {CONTRACTS}/.git; git -C {DOCS} push origin main", str(WORKSPACE)),
                         (f"git -C {DOCS} --git-dir={CONTRACTS}/.git push origin main", str(WORKSPACE)),
                         (f"git -C {DOCS} -C ../invai-contracts push origin main", str(WORKSPACE)),
                         (f"git() {{ command git -C {CONTRACTS} push origin main; }}; git -C {DOCS} push origin main",
                          str(WORKSPACE)),
                         (f"bash -c 'git -C {DOCS} push origin main'", str(WORKSPACE)),
                         (f"echo $(git -C {DOCS} push origin main)", str(WORKSPACE)),
                         (f"echo x | xargs git -C {DOCS} push origin", str(WORKSPACE))):
            with self.subTest(cmd=cmd):
                self.assertDecision(cmd, "deny", self.no_stamp(), cwd=cwd)

    def test_docs_force_still_denied(self):
        self.assertDecision(f"git -C {DOCS} push --force origin main", "deny", self.no_stamp(), msg="force-push")

    def test_docs_push_by_non_tech_lead_denied(self):
        self.assertDecision(f"git -C {DOCS} push origin main", "deny", self.no_stamp(),
                            agent_type="backend-engineer", msg="only the tech lead pushes")


if __name__ == "__main__":
    unittest.main()
