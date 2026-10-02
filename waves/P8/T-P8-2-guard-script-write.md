# T-P8-2: T-P7-4 round 3, a word after a redirect is a file, not a script to read

| Field | Value |
|---|---|
| Wave | P8 |
| Scope ref | `always-in-scope: security` (B-115 hook half, B-189); owner OI-23 answer A (2026-10-01) |
| Owner | platform-sre |
| Reviewer | security-reviewer (fable) as round 3 of T-P7-4 (the `reviewer` approved r1) |
| Risk flags | auth (team controls) |
| Model | opus |

## Read first
- `.claude/agents/platform-sre.md`; card `invai-docs/waves/P7/T-P7-4-hook-gaps.md` (its Safety section applies in full); report `waves/P7/reports/T-P7-4.md`; review `waves/P7/reviews/T-P7-4-security-reviewer-r2.md` (blocking finding 1 is this card).

## Owned paths (edit)
- `.claude/hooks/guard-bash.py`, `.claude/hooks/tests/**`, and the backup copies `invai-docs/team/hooks/**` (both copies identical when you finish).

## Read-only
- Everything else. `invai-infra/**` is being edited by T-P8-1 at the same time. T-P8-3 edits `guard-bash.py` after you hand back: finish, install and commit before handing back.

## Acceptance criteria (only this fix; OI-23 limits round 3 to it)
1. A word that directly follows a redirect operator (`>`, `>>`, `>|`, `&>`, `<`, and fd forms like `2>`) is treated as a file, not a command, so it never becomes a script reference.
2. These six forms are allowed (each an allow test): `echo 'ls' > /tmp/p8/w1.sh`; `cat > /tmp/p8/w2.sh <<'EOF'` … `EOF`; `echo ls > ./w8.sh`; `mkdir -p scripts && cat > scripts/w6.sh <<EOF` … `EOF`; `cat > invai-infra/scripts/new.sh <<EOF` … `EOF`; `echo … > /tmp/x.sh; echo written`. Also a heredoc that only quotes such a command (for example `cat >> notes.md <<'EOF'` containing the text `echo ls > x.sh`) is allowed.
3. Still denied (each a deny test): `echo … > n.sh; bash n.sh`, `curl -o n.sh …; bash n.sh`, `cp bad.sh n.sh; bash n.sh`, `sed … > n.sh; bash n.sh`, and every existing deny test still passes unchanged.
4. No other rule changes. The r2 optional notes (repositories/<id>, npx writers, `$(...)` producers) are not in this card; they go to the backlog.

## Verification
- Build and test in `/tmp/p8-2-hooks/` first: `python3 -B -m unittest discover -s /tmp/p8-2-hooks/tests 2>&1 | tail -n 5`. Install into `.claude/hooks/` only after it passes; then run the suite against the live copy and `invai-docs/team/hooks/`, and `diff -rq` the two (only `__pycache__` may differ).
- Right after installing, run `git -C /Users/bekbolsun/invai/invai-docs status --short` to prove normal work still passes.
- Count of tests before and after (no test removed or loosened).

## Commit
- `invai-docs`: commit only `team/hooks/**` and your report, message ends with the attribution line. Don't stage `learn/**` or anything else (a mentor agent works there). Don't push; only the tech lead pushes after the gate.

## Report
- `invai-docs/waves/P8/reports/T-P8-2.md`, `verify-and-report` format, at most 60 lines. Record every PID you start.
