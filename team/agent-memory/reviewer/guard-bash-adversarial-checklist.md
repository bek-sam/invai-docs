---
name: guard-bash-adversarial-checklist
description: When reviewing invai-docs/team/hooks/guard-bash.py (or its live copy), always probe here-string/heredoc redirects — the shlex-based parser has a real gap there
metadata:
  type: project
---

Wave 16 T-16-2 (round 1, 2026-09-26) added a shlex-based command parser to `guard-bash.py` to catch `bash -c`,
`eval`, `$(...)`, backticks, `echo … | sh`, `find -exec`, and `python -c "os.system(...)"` forms of a denied
command. It still misses **here-strings and heredocs used as a command source**: `bash <<< 'git push'`,
`sh <<< 'git stash'`, `zsh <<< 'git reset --hard'`, `sh <<< 'git add -A'` all return `allow`. Root cause:
`shlex` with `punctuation_chars=True` tokenizes `bash <<< 'git push'` as `['bash', '<<<', 'git push']` — the
quoted string becomes one token with an embedded space, so `os.path.basename(w[0])` is the literal string
`"git push"`, never matching `git`. This bypasses R1-R4 (push, stash/reset --hard/checkout/restore/clean,
pattern-kill, `add -A`) completely. Flagged blocking in `waves/16/reviews/T-16-2-reviewer-r1.md`; not yet fixed
as of round 1.

**Why:** the 112-row adversarial table in `test_guard.py` has no `<<<` or bare `<<` case, and the parser has
special-case handling for every *other* way of feeding a string to a shell (`-c`, `-e`, `-exec`, a pipe into
`sh`) but not this one. A denylist parser's blind spots cluster around "yet another way to hand a string to a
shell": if a new evasion form shows up later, check whether it's structurally the same gap (a single token that
is itself a full shell command, never re-lexed) before assuming it's fixed by the existing recursion.

**Exemptions keyed on a directory leak through the push's own arguments (T-23-6 r3 / T-P8-3, 2026-10-01, S-47):**
when a push rule exempts one repo by its `-C <dir>` (invai-docs, no gate stamp) but never checks the remote
and refspec words, two allowed commands move a code commit without the gate: `git -C <docs> fetch <code repo
path> main`, then `git -C <docs> push <code remote URL> FETCH_HEAD:main`. Always probe `push <url|path|other
remote> <ref>:main`, `--repo=`, and `fetch <sibling repo>` against any per-repo exemption, and compare what the
README/card promises ("only `push origin main`") with what the regex actually pins. Also confirmed: `python3
x.py` holding a push is never resolved (script resolution covers shells only), on old and new guard alike.

S-47 closed in T-P8-3 r4 (`b00480c`, 2026-10-02): `_is_docs_push` pins `w[sub_at+1:]` to `origin main|<7-40 hex>:main`, with `2>&1` accepted only in its lexed shape (`main 2` + `>&` item `1`). Redirect-shape probes worth repeating on any argv allow-list: `2 >&1` (space; allows, harmless), `2>/tmp/x`, `1>&2`, `2>&1 --repo=`, a second `-C`, `$REF`, uppercase sha, quoted extra word. Hand `main~1`-dependent tests a real workspace or they error.

**How to apply:** any future review of `guard-bash.py` (or `invai_hooklib.py`'s parser, which shares the same
shlex approach for the T-16-1 verification tracker) should always try `<sh|bash|zsh> <<< '<denied command>'`
and a real multi-line heredoc (`<<'EOF' ... EOF`) as part of the adversarial probe, in addition to whatever the
author's own table covers. Don't trust that "we handle `eval`/`-c`/pipes" implies here-strings are handled too
— check the token list with `shlex.shlex(cmd, posix=True, punctuation_chars=True)` directly if unsure.
