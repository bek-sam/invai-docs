---
name: hooks-testing-layout
description: How to safely change and test .claude/hooks (guard fails closed for the whole team); test layout quirks, FORCE_COLOR, shlex comment trap
metadata:
  type: project
---

2026-10-01 T-P7-4: changing `.claude/hooks/*` safely.
- Test in a mirror: `/tmp/<x>/hooks/{*.py,tests/}` + `/tmp/<x>/settings.json` (tests read `HOOKS.parent/settings.json` and `tests/../..`), run `python3 -B -m unittest discover -s hooks/tests`. Install by `cp` to a dotfile + `mv` (atomic), then run one harmless Bash.
- Canonical tests live in `invai-docs/team/hooks/tests/` (sync.sh never copies tests); keep `.claude/hooks/tests/` identical. `test_push_stamp.py` uses `INVAI_WORKSPACE` (default /Users/bekbolsun/invai).
- Sessions set `FORCE_COLOR=3`: any tool output parsed by a hook needs `NO_COLOR=1` (ruff broke the fast-check test).
- shlex in posix mode treats `#` as a comment to end of input once newlines are turned into `;` — strip comments first and set `commenters = ""`.
- Deny-case samples go in a file piped to the guard (`/tmp/<x>/run.py`-style), never on your own command line.
- That includes patch scripts and report text: a Bash heredoc naming `gh api … secrets`/`-X DELETE` is blocked by the live line-level rule (BASH_RULES secrets/keys/dispatches). Write patch scripts with Write, then run them; append report text with Edit.
- 2026-10-01 T-P8-2: `_lex` makes each redirect target its own item (op=`>`/`<`/`<<`…, words[0]=file); `2>` lexes as word `2` + `>`. Before changing script/redirect rules, run a live-vs-patched compare over ~15 unrelated forms to catch side effects (the old parse denied `bash < /abs/x.sh` only by accident).

**Why:** the guard fails closed on every agent's Bash; a half-installed or syntax-broken guard stops the wave.
**How to apply:** any card touching `guard-bash.py`, `track-verify.py`, `invai_hooklib.py` or settings hooks. Related: [[worker-after-seed-ordering]].
- 2026-10-01 T-P8-3: push check is now one whole-command form for code repos (`CODE_PUSH_FORM`) + literal-abs `-C invai-docs` for docs; no cwd guessing. Prove new deny tests by running them against a scratch copy of the pre-change guard.

- 2026-10-02 T-P8-3 r4: the live guard scans heredoc/commit text too; any Bash call whose text holds `git ... push` words (even in a report heredoc or commit message) is judged as a push. Write such text with Edit/Write, and keep push words out of commit messages.
