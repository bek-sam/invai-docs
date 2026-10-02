#!/usr/bin/env python3
"""PreToolUse guard for the InvAI team (see invai-docs/team/operating-system.md).

- Bash: denies force-pushes, history or remote rewrites, tag pushes, deploys, cloud CLIs,
  and secret or repo-setting changes.
- Bash, the recurring lessons (invai-docs/team/lessons.md, T-16-2):
  - `git push` only from the main session or the tech-lead agent (waves 2 and 8);
  - T-23-6 r3 (OI-22): a code repo is pushed only as the whole command
    `git -C /Users/bekbolsun/invai/<repo> push origin main|<sha>:main`, with a fresh `pnpm gate` stamp
    for that commit; invai-docs only as `git -C /Users/bekbolsun/invai/invai-docs push ...`; every
    other push form is denied;
  - no `git stash` (except list/show), `git reset --hard`, `git checkout -- <path>|.`,
    `git restore` without --staged, `git clean -f` in the shared trees (waves 4 and 8);
  - no `pkill`, `killall`, or `kill` fed by a process pattern (wave 2); plain `kill <pid>` is fine;
  - no `git add -A/--all/-u/.` or `git commit -a` (handbook: commit only your own paths);
  - the owner approves `pnpm install/i/add` and `npm install/i/ci` (waves 6/7);
  - the owner approves `db:reset` unless the caller is the main session or qa-engineer (gates).
- Bash, T-P7-4 (B-115, B-189):
  - scripts the command runs (`bash|sh|zsh <file>`, `source|. <file>`, `./<file>`, a path to a `*.sh`)
    are read (text up to 256 KB, any path; larger text is denied, binaries skipped) and checked with
    every rule above, nested scripts too. A missing file is allowed, unless the same command also
    may write it (a redirect into it, or a command other than a plain reader such as pnpm, grep,
    pgrep or echo naming it): written in this call, then run, so split it into two calls. The word
    after a redirect (`>`, `>>`, `>|`, `&>`, `2>`, `<`) is a file, not a script it runs, unless a shell
    reads it on stdin (`bash < x.sh`) (T-P8-2);
  - text piped into a shell must come from `echo`, `printf` or `cat` (read as commands); `curl | sh`,
    `wget -O- | bash`, `| rev | bash`, `| sed ... | sh` are denied;
  - decoded text run as code is denied: `base64 -d`, `openssl base64|enc -d`, `xxd -r`, `uudecode`,
    `basenc|base32 -d` in the same command (pipeline or $(...)) as `bash|sh` reading stdin or `-c`,
    `eval`, `source` or `.`; decoding to a file stays allowed;
  - `sst secret set|remove|load` (any stage); `gh api` writes (-X/--method POST|PUT|PATCH|DELETE, or
    -f/-F/--field/--raw-field/--input; path or full URL, GHES `/api/v3/` too) to a repo itself or its branch protection, rulesets,
    collaborators, hooks, environments, actions permissions or transfer; GraphQL repository-setting
    mutations; `gh repo edit|delete|rename|archive|unarchive` (word level only, so a commit message or
    heredoc that mentions them passes); `gh ruleset` other than list/view/check.
- MCP tools: anything that isn't clearly read-only (send, publish, create, update,
  delete...) needs the owner's explicit approval ("ask").

Fails closed: if the input can't be parsed, or the guard itself errors, the call is denied.
The new rules read shell words (shlex), following `bash -c`, `eval`, `$(...)`, backticks, pipes into
a shell, simple VAR=value assignments and the scripts above, so text inside a commit message doesn't
trip them; `#` comments are dropped before reading words. Known limits, out of reach of a denylist
(the guard stops the mistakes the lessons record, it is not a sandbox): commands built at run time
(`bash -c "$(printf ...)"`, `$var` filled by a command), shell aliases and functions, a script whose
path is a variable, and subprocesses started by node, python or other programs (package.json
scripts, `pnpm <script>` and Makefiles are not read).
"""
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone

INBOX = "If it's really needed, add an entry to invai-docs/owner-inbox.md (escalate-to-owner)."


def deny(reason):
    print(f"Blocked by InvAI team rules: {reason}. {INBOX}", file=sys.stderr)
    sys.exit(2)


def ask(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": f"InvAI team rule: {reason}. Only the owner approves this.",
    }}))
    sys.exit(0)


try:
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    agent_type = data.get("agent_type")
    if not isinstance(tool, str) or not isinstance(tool_input, dict) or not isinstance(agent_type, (str, type(None))):
        raise ValueError("bad shape")
except Exception:
    deny("the guard hook couldn't read its input")

GIT = r"\bgit(?:\s+-C\s+\S+|\s+-c\s+\S+|\s+--?[\w-]+(?:=\S+)?)*\s+"

PUSH_REASON = "no force-push, ref deletion, mirror or tag push (tags deploy production)"
# Checked per command segment only (B-116): a `-d` from `tr -d` later on the line is not a push flag.
PUSH_RULE = GIT + r"push\b.*(--force|--force-with-lease|--mirror|--delete|--tags|--follow-tags|\s-[a-zA-Z]*[fd]\b|\s\+\S+|\s:\S+|refs/tags|\sv\d)"
SEGMENT_SPLIT = r"&&|\|\||\|&|(?<![<>&])&(?![>&])|[;|\n()`]|\$\("
BASH_RULES = [
    (GIT + r"remote\s+(add|remove|rm|set-url|rename)\b", "never change remotes"),
    (GIT + r"(filter-branch|filter-repo)\b", "never rewrite history"),
    (r"(^|[\s/])(sst\s+(deploy|remove)|cdk\s+(deploy|destroy)|terraform\s+(apply|destroy)|pulumi\s+(up|destroy))\b",
     "deploys to real environments are triggered by the owner (deploy-to-environment)"),
    (r"\bpnpm\b.*\b(sst:deploy|deploy:\w+)\b", "deploys to real environments are triggered by the owner"),
    (r"\bgh\s+workflow\s+run\b", "running workflows (deploy.yml) is triggered by the owner"),
    (r"\bgh\s+run\s+(rerun|cancel)\b", "re-running or cancelling workflow runs (deploys) is done by the owner"),
    (r"\bgh\s+(secret|variable)\s+(set|delete|remove)\b", "secrets and variables are changed by the owner"),
    (r"\bgh\s+api\b.*(secrets|variables|dispatches|/keys|-X\s*DELETE|--method\s+DELETE)",
     "secrets, deploy keys and workflow dispatch are changed by the owner"),
    (r"\bgh\s+release\s+(create|delete|edit)\b", "releases are created by the owner"),
    (r"^\s*(?:sudo\s+|env\s+|command\s+|exec\s+|\w+=\S+\s+)*(?:\S*/)?aws\s+", "real AWS accounts are touched only by the owner"),
]

READ_ONLY_MCP = re.compile(
    r"__(?:notion-)?(get|list|search|read|fetch|query|find|show|describe|explore|status|context|guide|"
    r"balance|wait|inspect|check|suggest|resolve|models|apps_search|apps_describe|"
    r"job_display|jobs_wait|tabs_context|read_page|get_page_text|read_console|read_network|"
    r"authenticate|complete_authentication)",
    re.I,
)

# ---------- shell words for the lesson rules ----------

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
PREFIX_CMDS = {"sudo", "env", "command", "builtin", "exec", "nohup", "time", "nice", "caffeinate", "then",
               "do", "else", "if", "while", "until", "!", "{", "noglob"}
XARGS_VALUE_OPTS = {"-I", "-n", "-P", "-L", "-d", "-E", "-s", "-a", "-J", "-R"}
GIT_VALUE_OPTS = {"-c", "-C", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix",
                  "--config-env", "--list-cmds"}
OPS = set("();|&<>")
PUSH_ROLES = {"tech-lead"}
DB_RESET_ROLES = {"qa-engineer"}


def _substitutions(cmd):
    """Replace each $(...) and `...` outside single quotes with a placeholder; return (text, [bodies])."""
    out, bodies, i, n, sq, dq = [], [], 0, len(cmd), False, False
    while i < n:
        c = cmd[i]
        if c == "\\" and not sq and i + 1 < n:
            out.append(cmd[i:i + 2])
            i += 2
            continue
        if c == "'" and not dq:
            sq = not sq
        elif c == '"' and not sq:
            dq = not dq
        elif not sq and c == "`":
            j = cmd.find("`", i + 1)
            j = n if j < 0 else j
            bodies.append(cmd[i + 1:j])
            out.append(" SUBST ")
            i = j + 1
            continue
        elif not sq and cmd.startswith("$(", i):
            depth, j = 1, i + 2
            while j < n and depth:
                depth += {"(": 1, ")": -1}.get(cmd[j], 0)
                j += 1
            bodies.append(cmd[i + 2:j - 1])
            out.append(" SUBST ")
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out), bodies


def _strip_comments(cmd):
    """Drop `#` comments (a `#` starting a word, outside quotes) up to the end of their line.

    shlex's own comment handling ran past the newline once newlines became `;`, so everything after the
    first `#` (a comment, `a#b`, `${#x}`) went unread (T-P7-4)."""
    out, i, n, sq, dq = [], 0, len(cmd), False, False
    while i < n:
        c = cmd[i]
        if c == "\\" and not sq and i + 1 < n:
            out.append(cmd[i:i + 2])
            i += 2
            continue
        if c == "'" and not dq:
            sq = not sq
        elif c == '"' and not sq:
            dq = not dq
        elif c == "#" and not sq and not dq and (i == 0 or cmd[i - 1] in " \t\n;&|()<>"):
            j = cmd.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _lex(cmd):
    """[(words, op_before, here_strings)] simple commands, or None if shlex can't parse it.

    A here-string (`bash <<< 'git push'`) stays attached to its command, so a shell fed one can be re-read.
    """
    cmd = _strip_comments(cmd).replace("\n", " ; ")
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.commenters = ""
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        return None
    out, cur, op, here, want_here = [], [], None, [], False
    for t in toks:
        if want_here and not (t and set(t) <= OPS):
            here.append(t)
            want_here = False
        elif t == "<<<":
            want_here = True
        elif t and set(t) <= OPS:
            if cur or here:
                out.append((cur, op, here))
            cur, op, here = [], t, []
        else:
            cur.append(t)
    if cur or here:
        out.append((cur, op, here))
    return out


def _fallback(cmd):
    """Quote-stripped regex split, used when shlex can't parse (heredocs with apostrophes and such)."""
    flat = re.sub(r"""["'\\]""", "", re.sub(r"\\\n", " ", cmd))
    out = []
    for part in re.split(r"(&&|\|\||\||;|&|\n|\$\(|`|[(){}]|<<<)", flat):
        if part and part.strip() and not re.fullmatch(r"&&|\|\||\||;|&|\n|\$\(|`|[(){}]|<<<", part):
            out.append((part.split(), None, []))
    return out


WRAPPERS = {"npx", "bunx", "corepack", "pnpx"}
PM_VALUE_OPTS = {"-C", "--dir", "--filter", "-F", "--prefix", "-w", "--workspace", "--cwd"}


def _runner_at(w):
    """Index of `dlx`/`exec`/`x` in `pnpm dlx ...`, `pnpm exec ...`, `npm exec ...`, `yarn dlx ...`, else None."""
    i = 1
    while i < len(w) and w[i].startswith("-"):
        i += 2 if w[i] in PM_VALUE_OPTS else 1
    if i < len(w) and w[i].lower() in ("dlx", "exec", "x"):
        return i
    return None


def _strip_prefix(w, captured=None):
    """Strip prefix commands/wrappers (sudo, env, timeout, xargs, pnpm dlx, ...) down to the real
    command. `captured`, when given, collects any leading `VAR=value` words popped along the way
    (e.g. `GIT_DIR=repo/.git git push` -> {"GIT_DIR": "repo/.git"}); every existing caller omits
    it and sees no change in behavior."""
    w = list(w)
    while w:
        head = os.path.basename(w[0]).lower()
        if re.match(r"^[A-Za-z_]\w*=", w[0]) or head in PREFIX_CMDS:
            if captured is not None and re.match(r"^[A-Za-z_]\w*=", w[0]):
                k_, v_ = w[0].split("=", 1)
                captured[k_] = v_
            w.pop(0)
            while w and w[0].startswith("-") and head in ("sudo", "env", "nice", "command", "exec"):
                opt = w.pop(0)
                if head in ("nice", "sudo") and opt in ("-n", "-u", "-g") and w:
                    w.pop(0)
        elif head in ("timeout", "gtimeout"):
            w.pop(0)
            while w and w[0].startswith("-"):
                w.pop(0)
            if w:
                w.pop(0)
        elif head == "xargs":
            w.pop(0)
            while w and w[0].startswith("-"):
                opt = w.pop(0)
                if opt in XARGS_VALUE_OPTS and w:
                    w.pop(0)
        elif head in WRAPPERS:
            w.pop(0)
            while w and w[0].startswith("-"):
                opt = w.pop(0)
                if opt in ("-c", "--call") and w:
                    return _strip_prefix(shlex.split(w[0]), captured)
                if opt in ("-p", "--package") and w:
                    w.pop(0)
        elif head in ("pnpm", "npm", "yarn") and _runner_at(w) is not None:
            w = w[_runner_at(w) + 1:]
            while w and w[0].startswith("-"):
                opt = w.pop(0)
                if opt in ("-c", "--call", "--shell-mode") and w:
                    return _strip_prefix(shlex.split(w[0]), captured)
                if opt in ("-p", "--package") and w:
                    w.pop(0)
        elif head == "perl" and any("ARGV" in x for x in w):
            k = next(i for i, x in enumerate(w) if "ARGV" in x)
            w = w[k + 1:]
        else:
            break
    return w


# T-23-6 r2 finding 1: a sentinel meaning "we lost track of the working directory with
# certainty" (an unresolved `cd $var`, `cd -`, `popd`, or a relative `cd`/`-C` from an already-
# ambiguous base). Distinct from any real path string, so `x is CWD_AMBIGUOUS` is unambiguous.
CWD_AMBIGUOUS = object()


def _advance_cwd(w, cwd):
    """The tracked cwd after a `cd`/`pushd` word list `w` (head already known to be one of
    these), or CWD_AMBIGUOUS once it can't be pinned to a literal path. `pushd` is tracked like
    `cd` (we don't model the real directory *stack*, only "where are we now"); `popd` always
    returns CWD_AMBIGUOUS from its own caller, since without that stack we can't say where it
    goes back to."""
    args = [a for a in w[1:] if a != "--"]
    target = next((a for a in args if not a.startswith("-") or a == "-"), None)
    if not target or target == "-" or "$" in target or "`" in target:
        return CWD_AMBIGUOUS
    if os.path.isabs(target):
        return os.path.normpath(target)
    if cwd is CWD_AMBIGUOUS:
        return CWD_AMBIGUOUS
    return os.path.normpath(os.path.join(cwd, target))


# ---------- T-P7-4: scripts the command runs (B-115) ----------
SCRIPT_MAX_BYTES = 256 * 1024
SCRIPT_MAX_COUNT = 32
SCRIPT_REFS = []  # (path word as written, cwd at that command), appended by simple_commands
SHELL_VALUE_OPTS = {"-o", "+o", "-O", "+O", "--rcfile", "--init-file"}


def _script_target(w):
    """The script file a simple command runs (`bash x.sh`, `source x`, `. x`, `./x`, `dir/x.sh`), or None."""
    head_raw, head = w[0], os.path.basename(w[0]).lower()
    if head in SHELLS:
        i = 1
        while i < len(w):
            a = w[i]
            if a in SHELL_VALUE_OPTS:
                i += 2
                continue
            if a == "--":
                i += 1
                break
            if a.startswith(("-", "+")) and len(a) > 1:
                if a.startswith("-") and not a.startswith("--") and ("c" in a or "s" in a):
                    return None  # -c runs a string (read above); -s reads stdin
                i += 1
                continue
            break
        return w[i] if i < len(w) else None
    if head in ("source", ".") and len(w) > 1:
        return w[1]
    if head_raw.startswith(("./", "../")) or ("/" in head_raw and head_raw.endswith(".sh")):
        return head_raw
    return None


def _resolve_script(word, cwd):
    """Absolute path of a script word, or None when it can't be pinned (a variable, an unknown cwd)."""
    if not word or "$" in word or "SUBST" in word or "`" in word:
        return None
    p = os.path.expanduser(word)
    if not os.path.isabs(p):
        if cwd is CWD_AMBIGUOUS or cwd is None:
            return None
        p = os.path.join(cwd, p)
    return os.path.normpath(p)


def _read_script(path):
    """The script's text; None when missing, unreadable or binary. Text over 256 KB is denied."""
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "rb") as f:
            raw = f.read(SCRIPT_MAX_BYTES + 1)
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    if len(raw) > SCRIPT_MAX_BYTES:
        deny(f"the script {os.path.basename(path)} is over 256 KB, too large for the guard to read")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


# ---------- T-P7-4: decoded text run as code (B-115) ----------

def _is_decoder(w):
    head, args = os.path.basename(w[0]).lower(), w[1:]
    short = _short_flags(args)
    if head in ("base64", "gbase64", "base32", "gbase32", "basenc"):
        return "--decode" in args or bool({"d", "D"} & short)
    if head == "openssl":
        return bool(args) and args[0].lower() in ("base64", "enc") and ("-d" in args or "-decode" in args)
    if head == "xxd":
        return "r" in short or "-revert" in args
    return head == "uudecode"


def _is_executor(w):
    head = os.path.basename(w[0]).lower()
    if head in ("eval", "source", "."):
        return True
    if head in SHELLS:
        if any(re.fullmatch(r"-[a-zA-Z]*[cs][a-zA-Z]*", x) for x in w[1:]):
            return True
        t = _script_target(w)
        return t is None or t.startswith("/dev/")
    return False


def _quiet_commands(seg, cwd):
    """simple_commands for a re-read of one segment: its script refs were already noted (with the right cwd)."""
    n = len(SCRIPT_REFS)
    try:
        return simple_commands(seg, cwd=cwd)
    finally:
        del SCRIPT_REFS[n:]


def encoded_rules(cmd, cwd):
    """Deny decoded text that reaches a shell, eval or source in the same top-level segment."""
    for seg in _top_segments(cmd):
        ws = [w for w, _, _ in _quiet_commands(seg, cwd)]
        if any(_is_decoder(w) for w in ws) and any(_is_executor(w) for w in ws):
            return ("deny", "no decoded text run as code (base64/xxd/openssl -d into a shell, eval or source): "
                            "it hides commands from the guard. Decode to a file and read it first")
    return None


# ---------- T-P7-4: secrets and repo settings (B-189) ----------
GH_API_VALUE_OPTS = {"-H", "--header", "-q", "--jq", "-t", "--template", "--cache", "-p", "--preview",
                     "--hostname"}
GH_API_FIELD_OPTS = {"-f", "-F", "--field", "--raw-field", "--input"}
GH_SETTINGS_PATH = re.compile(
    r"^repos/[^/]+/[^/]+/?$|(^|/)(rulesets|collaborators|hooks|environments|protection|transfer|"
    r"actions/permissions|vulnerability-alerts|automated-security-fixes)(/|$)")
GH_SETTINGS_GRAPHQL = re.compile(
    r"(updateRepository|deleteRepository|archiveRepository|unarchiveRepository|transferRepository|"
    r"BranchProtectionRule|Ruleset|Collaborator|Environment)", re.I)


def _gh_api_write(args):
    """(is_write, endpoint, all_text) for `gh api <args>`."""
    method, fields, endpoint, i = None, False, None, 0
    while i < len(args):
        a = args[i]
        if a in ("-X", "--method") and i + 1 < len(args):
            method, i = args[i + 1], i + 2
            continue
        if a.startswith("--method="):
            method = a.split("=", 1)[1]
        elif a.startswith("-X") and len(a) > 2:
            method = a[2:]
        elif a in GH_API_FIELD_OPTS:
            fields, i = True, i + 2
            continue
        elif any(a.startswith(f + "=") for f in GH_API_FIELD_OPTS if f.startswith("--")) or (
                a[:2] in ("-f", "-F") and len(a) > 2):
            fields = True
        elif a in GH_API_VALUE_OPTS:
            i += 2
            continue
        elif not a.startswith("-") and endpoint is None:
            endpoint = a
        i += 1
    m = (method or ("POST" if fields else "GET")).upper()
    return m in ("POST", "PUT", "PATCH", "DELETE"), (endpoint or ""), " ".join(args)


def _gh_api_path(endpoint):
    """`gh api` endpoint as a path: full URLs (`https://api.github.com/repos/o/r/`, GHES `/api/v3/`) lose their
    scheme and host, so the URL form matches the same rules as `repos/o/r`."""
    ep = re.split(r"[?#]", endpoint, maxsplit=1)[0].strip().lower()
    ep = re.sub(r"^(?:[a-z][a-z0-9+.-]*:)?//[^/]*", "", ep)
    ep = re.sub(r"^/*(?:api/v3/+)?", "", ep)
    return re.sub(r"/{2,}", "/", ep)


def setting_rules(w):
    head = os.path.basename(w[0]).lower()
    rest = [x for x in w[1:]]
    if head in ("pnpm", "npm", "yarn", "bunx") and rest and rest[0] == "sst":
        head, rest = "sst", rest[1:]
    if head == "sst":
        pos = [x.lower() for x in rest if not x.startswith("-")]
        if "secret" in pos:
            k = pos.index("secret")
            if k + 1 < len(pos) and pos[k + 1] in ("set", "remove", "load", "rm", "unset"):
                return ("deny", "secrets are changed by the owner (sst secret set/remove/load)")
    elif head == "gh":
        while rest and rest[0].startswith("-"):
            rest = rest[2:] if rest[0] in ("-R", "--repo", "--hostname") else rest[1:]
        sub = rest[0].lower() if rest else ""
        verb = rest[1].lower() if len(rest) > 1 else ""
        if sub == "repo" and verb in ("edit", "delete", "rename", "archive", "unarchive"):
            return ("deny", "repo settings are changed by the owner")
        if sub == "ruleset" and verb not in ("list", "ls", "view", "check", ""):
            return ("deny", "repo rulesets are changed by the owner")
        if sub == "api":
            write, endpoint, text = _gh_api_write(rest[1:])
            ep = _gh_api_path(endpoint)
            if ep == "graphql" and "mutation" in text.lower() and GH_SETTINGS_GRAPHQL.search(text):
                return ("deny", "repo settings are changed by the owner (GraphQL mutation)")
            if write and GH_SETTINGS_PATH.search(ep):
                return ("deny", "repo settings, branch protection, rulesets, collaborators, hooks and "
                                "environments are changed by the owner (gh api write)")
    return None


# Only literal text may be piped into a shell (its words are read as commands below); decoders get
# encoded_rules' message.
PIPE_TO_SHELL_SOURCES = {"echo", "printf", "cat"}
# Redirect operators as _lex returns them (`>`, `>>`, `>|`, `&>`, `2>` as `2` then `>`, `<`, `<<`, `>&`, `<>`),
# also glued to a separator (`;>`); `>(`/`<(` are process substitutions, not redirects (T-P8-2).
REDIRECT_OP = re.compile(r"(?:&>>?|>>?|>\||>&|<&|<>|<<?)$")


def simple_commands(cmd, depth=0, cwd=None):
    """Every simple command in `cmd` as (word list, tracked cwd, GIT_DIR value or None).

    Prefixes are stripped and $VARS from VAR=value expanded, as before. The added `cwd` element
    is the shell's working directory at that command, tracked from `cwd`/the session cwd forward
    through `cd`/`pushd`/`popd` and real command sequencing (`;`, `&&`, `||`, and - like the rest
    of this flattening - a literal `(...)` grouping, which this parser cannot distinguish from a
    plain separator, so a `cd` inside one is not un-done after its `)`; every case this guard
    needs to catch has at most one push per command, so that never matters in practice). A
    `bash -c`/`eval`/`$(...)`/backtick body gets its own copy of the *caller's* cwd-at-that-point
    and never leaks its own `cd`s back out, which correctly models a real subshell. It is
    CWD_AMBIGUOUS once a `cd`/`pushd`/`popd` target can't be pinned to a literal path (an
    unresolved loop variable, `cd -`, `popd`); a resolved absolute `cd` can recover from that.
    """
    if depth > 4:
        deny("the command nests shells too deeply for the guard to read")
    if cwd is None:
        cwd = data.get("cwd") or os.getcwd()
    cmd = _strip_comments(re.sub(r"\$\{?IFS\}?", " ", re.sub(r"\\\n", " ", cmd)))
    text, bodies = _substitutions(cmd)
    parsed = _lex(text)
    items = parsed if parsed is not None else _fallback(cmd)
    env, result = {}, []
    for body in bodies:
        result.extend(simple_commands(body, depth + 1, cwd))
    for idx, (words, op, here) in enumerate(items):
        if words and all(re.match(r"^[A-Za-z_]\w*=", x) for x in words[1:] if x) and words[0] in ("export", "declare", "local", "readonly"):
            words = words[1:]
        if words and all(re.match(r"^[A-Za-z_]\w*=", x) for x in words):
            for x in words:
                k, v = x.split("=", 1)
                env[k] = v
            continue

        def expand(x):
            return re.sub(r"\$\{?([A-Za-z_]\w*)\}?", lambda m: env.get(m.group(1), m.group(0)), x)

        words = [expand(x) for x in words]
        here = [expand(x) for x in here]
        captured = {}
        w = _strip_prefix(words, captured)
        if not w:
            continue
        git_dir_here = captured.get("GIT_DIR") or env.get("GIT_DIR")
        result.append((w, cwd, git_dir_here))
        head = os.path.basename(w[0]).lower()
        if op and REDIRECT_OP.search(op):
            # T-P8-2: the word after a redirect is a file, not a command (`echo ls > /tmp/x.sh` runs nothing).
            # Only a shell reading it on stdin (`bash < x.sh`, `sh -s < x.sh`) runs it as a script.
            j = idx - 1
            while j > 0 and items[j][1] and REDIRECT_OP.search(items[j][1]):
                j -= 1
            runner = _strip_prefix(list(items[j][0])) if j >= 0 and op.endswith("<") and not op.endswith("<<") else []
            if (runner and os.path.basename(runner[0]).lower() in SHELLS and _script_target(runner) is None
                    and not any(re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", x) for x in runner[1:])):
                SCRIPT_REFS.append((w[0], cwd))
            target = None
        else:
            target = _script_target(w)
        if target is not None:
            SCRIPT_REFS.append((target, cwd))
        if head in ("cd", "pushd"):
            cwd = _advance_cwd(w, cwd)
        elif head == "popd":
            cwd = CWD_AMBIGUOUS
        if head in SHELLS and here:
            for body in here:  # bash <<< 'git push': the shell runs the here-string
                result.extend(simple_commands(body, depth + 1, cwd))
        if head in SHELLS:
            c_at = next((i for i, x in enumerate(w[1:], 1) if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", x)), None)
            if c_at is not None and c_at + 1 < len(w):
                result.extend(simple_commands(w[c_at + 1], depth + 1, cwd))
            elif op in ("|", "|&") and not [x for x in w[1:] if not x.startswith("-")]:
                j = idx - 1  # a pipe into a shell: read every earlier word in the pipeline as a command
                while j >= 0:
                    up = _strip_prefix(list(items[j][0]))
                    if up and os.path.basename(up[0]).lower() not in PIPE_TO_SHELL_SOURCES and not _is_decoder(up):
                        deny("no downloaded or transformed text piped into a shell (curl | sh, | rev | bash): the "
                             "guard can't read what runs. Save it to a file, read it, then run the file")
                    for x in items[j][0] + items[j][2]:
                        result.extend(simple_commands(x, depth + 1, cwd))
                    if items[j][1] not in ("|", "|&"):
                        break
                    j -= 1
        elif head == "eval" and len(w) > 1:
            result.extend(simple_commands(" ".join(w[1:]), depth + 1, cwd))
        elif head == "find":
            for k, x in enumerate(w):
                if x in ("-exec", "-execdir", "-ok", "-okdir"):
                    rest = w[k + 1:]
                    end = next((j for j, y in enumerate(rest) if y in (";", "+", "\\;")), len(rest))
                    result.extend(simple_commands(" ".join(shlex.quote(y) for y in rest[:end]), depth + 1, cwd))
        elif re.match(r"^(python\d*(\.\d+)?|node|ruby|perl|deno|bun)$", head):
            code = next((w[k + 1] for k, x in enumerate(w[:-1]) if x in ("-c", "-e", "--eval", "-p")), None)
            if code:  # shell strings inside inline code: os.system("git stash"), ["git", "push"]
                lits = [m.group(2) for m in re.finditer(r"([\"'])(.*?)(?<!\\)\1", code)]
                for lit in lits + [" ".join(lits)]:
                    result.extend(simple_commands(lit, depth + 1, cwd))
    return result


def _short_flags(args, value_letters=""):
    """Letters of single-dash flag clusters, stopping at a letter that takes a value."""
    letters, skip = set(), False
    for a in args:
        if skip:
            skip = False
            continue
        if a == "--":
            break
        if a.startswith("-") and not a.startswith("--") and len(a) > 1:
            for i, ch in enumerate(a[1:]):
                letters.add(ch)
                if ch in value_letters:
                    skip = i == len(a) - 2
                    break
    return letters


PUSH_LONG_DENY = ("--force", "--force-with-lease", "--force-if-includes", "--mirror", "--delete", "--tags",
                  "--follow-tags", "--prune", "--all", "--branches")

# ---------- T-23-6: pre-push gate stamp (round 3, OI-22: exactly one push form) ----------
# `pnpm gate` (invai-infra/scripts/gate.sh) writes invai-infra/.gate/pass.json on a full pass:
# {"repos": {"invai-backend": {"sha": "<HEAD sha>", "at": "<UTC ISO time>"}, ...}}. A code repo is
# pushed only by the one form below, as the whole Bash command, and only with a fresh (<24h) stamp
# for the commit being pushed. No folder guessing: anything else is refused unless the push is
# positively invai-docs (docs-only, no gate suites), written as `git -C <WORKSPACE_DIR>/invai-docs push ...`.
WORKSPACE_DIR = "/Users/bekbolsun/invai"
GATE_STAMP_MAX_AGE_S = 24 * 3600
CODE_PUSH_FORM = re.compile(
    r"git -C " + re.escape(WORKSPACE_DIR)
    + r"/invai-(backend|web|floor|ui|contracts|imaging|infra) push origin (main|([0-9a-f]{7,40}):main)")
DOCS_DIR = WORKSPACE_DIR + "/invai-docs"
DOCS_PUSH_REFSPEC = re.compile(r"main|[0-9a-f]{7,40}:main")  # S-47: docs pushes `origin <this>` and nothing else
PUSH_CTX = {"cmd": "", "in_script": False}  # the whole Bash command; set by main() and script_rules()
PUSH_FORM_MSG = ("a code repo is pushed only as the whole command, exactly: "
                 "git -C " + WORKSPACE_DIR + "/<repo> push origin main (or <sha>:main), with nothing before "
                 "or after it (no cd, &&, ;, |, 2>&1, $(...), bash -c, env prefix, ~ or relative path), "
                 "after 'pnpm gate' passed for that commit. invai-docs: git -C " + DOCS_DIR + " push origin main "
                 "(or <sha>:main), nothing else in the push")


def _gate_stamp_path(workspace_dir):
    override = os.environ.get("INVAI_GATE_STAMP_PATH")  # test-only: read from the guard's own env, never the checked command
    if override:
        return override
    return os.path.join(workspace_dir, "invai-infra", ".gate", "pass.json")


def _is_docs_push(w, sub_at, git_dir_val):
    """True only when this push is positively invai-docs: a top-level command of the Bash call itself
    (not a script, $(...), bash -c, eval, xargs or other prefix), written `git -C <DOCS_DIR>[/] push ...`,
    with no GIT_* variable, --git-dir, git function or alias anywhere in the command, and pushing
    exactly `origin main` or `origin <7-40 hex sha>:main` (S-47)."""
    cmd = PUSH_CTX["cmd"]
    if PUSH_CTX["in_script"] or git_dir_val is not None or w[sub_at].lower() != "push":
        return False
    if w[1:sub_at] not in (["-C", DOCS_DIR], ["-C", DOCS_DIR + "/"]):
        return False
    args = w[sub_at + 1:]  # S-47: no other remote, URL, path, option or refspec
    redir = args[-1:] == ["2"]  # `... main 2>&1` lexes as words `... main 2`, then a `>&` item `1`
    if redir:
        args = args[:-1]
    if len(args) != 2 or args[0] != "origin" or not DOCS_PUSH_REFSPEC.fullmatch(args[1]):
        return False
    if "GIT_" in cmd or re.search(r"\bfunction\s+git\b|\bgit\s*\(\s*\)|\balias\b", cmd):
        return False
    text, _ = _substitutions(_strip_comments(re.sub(r"\\\n", " ", cmd)))
    items = _lex(text)
    if items is None:
        return False
    if any("GIT_" in x for words, _, here in items for x in words + here):
        return False
    return any(words == w and (not redir or items[i + 1:i + 2] and items[i + 1][:2] == (["1"], ">&"))
               for i, (words, _, _) in enumerate(items))


def _gate_check_push(w, sub_at, git_dir_val):
    """None if this push may proceed, else (reason,) to deny (OI-22 answer A).

    invai-docs, positively identified (_is_docs_push), is not gated. Every other push must be the
    whole Bash command in CODE_PUSH_FORM, and then needs a fresh stamp whose SHA is the commit being
    pushed; every read fails closed."""
    if _is_docs_push(w, sub_at, git_dir_val):
        return None
    m = None if PUSH_CTX["in_script"] else CODE_PUSH_FORM.fullmatch(PUSH_CTX["cmd"].strip())
    if m is None or w != ["git", "-C", f"{WORKSPACE_DIR}/invai-{m.group(1)}", "push", "origin", m.group(2)]:
        return (PUSH_FORM_MSG,)
    kind, src = m.group(1), m.group(3) or "main"
    root = f"{WORKSPACE_DIR}/invai-{kind}"
    stamp_path = _gate_stamp_path(WORKSPACE_DIR)
    try:
        with open(stamp_path) as f:
            stamp = json.load(f)
    except (OSError, ValueError):
        return (f"no fresh gate pass recorded ({stamp_path}). Run 'pnpm gate' from invai-infra first",)
    entry = (stamp.get("repos") or {}).get(f"invai-{kind}") if isinstance(stamp, dict) else None
    if not isinstance(entry, dict) or not entry.get("sha") or not entry.get("at"):
        return (f"no gate stamp for invai-{kind}. Run 'pnpm gate' from invai-infra first",)
    try:
        at = datetime.fromisoformat(str(entry["at"]).replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - at).total_seconds()
    except (ValueError, TypeError):
        return (f"the gate stamp for invai-{kind} has an unreadable time. Run 'pnpm gate' again",)
    if age > GATE_STAMP_MAX_AGE_S or age < -60:
        return (f"the gate stamp for invai-{kind} is older than 24h. Run 'pnpm gate' again before pushing",)
    try:
        r = subprocess.run(["git", "-C", root, "rev-parse", "--verify", "--quiet", f"{src}^{{commit}}"],
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return (f"can't read invai-{kind}'s commit for '{src}' to check the gate stamp",)
    pushed_sha = r.stdout.strip()
    if r.returncode != 0 or not pushed_sha:
        return (f"can't resolve '{src}' to a commit in invai-{kind} to check the gate stamp. "
                f"Run 'pnpm gate' again before pushing",)
    if entry["sha"] != pushed_sha:
        return (f"the gate stamp for invai-{kind} is for a different commit than '{src}' (stale). "
                f"Run 'pnpm gate' again before pushing",)
    return None


def _push_is_dangerous(git_opts, args):
    """Word-level check on this push's own words only (B-116): flags, refspecs, and config that forces."""
    for k, opt in enumerate(git_opts):  # git -c remote.origin.push=+... / -c push.followTags=true
        val = git_opts[k + 1] if opt == "-c" and k + 1 < len(git_opts) else opt[2:] if opt.startswith("-c") else ""
        if re.match(r"(remote\.|push\.|branch\.)", val.lower()):
            return True
    for a in args:
        if "SUBST" in a or "$" in a:
            return True  # a flag or refspec the guard can't read: write push arguments literally
        if a.startswith("--"):
            name = a.split("=", 1)[0].lower()
            if len(name) > 2 and any(d.startswith(name) for d in PUSH_LONG_DENY):  # git accepts abbreviations
                return True
        elif a.startswith("-") and a != "-":
            if {"f", "d"} & _short_flags([a], "o"):
                return True
        elif a.startswith(("+", ":")) or ":+" in a or "refs/tags" in a.lower() or re.search(r"(^|:)v\d", a):
            return True
    return False


def git_rules(w, cwd=None, git_dir_val=None):
    i = 1
    while i < len(w) and w[i].startswith("-"):
        opt = w[i]
        if opt in GIT_VALUE_OPTS and i + 1 < len(w):
            if opt == "-c" and w[i + 1].lower().startswith("alias."):
                return ("deny", "no git aliases: they hide blocked commands")
            i += 2
        else:
            if opt.startswith("-c") and opt[2:].lower().startswith("alias."):
                return ("deny", "no git aliases: they hide blocked commands")
            i += 1
    if i >= len(w):
        return None
    sub, args = w[i].lower(), w[i + 1:]
    if sub in ("push", "send-pack"):
        if agent_type is not None and agent_type not in PUSH_ROLES:
            return ("deny", "only the tech lead pushes, after the wave gate (lessons: waves 2 and 8). "
                            "Commit your own paths and report the SHA")
        if _push_is_dangerous(w[1:i], args):
            return ("deny", PUSH_REASON)
        gate = _gate_check_push(w, i, git_dir_val)
        if gate is not None:
            return ("deny", gate[0])
    elif sub == "stash":
        if not args or args[0].lower() not in ("list", "show"):
            return ("deny", "no git stash in a shared tree: it takes every agent's uncommitted work "
                            "(lessons: waves 4 and 8). Compare in your own worktree")
    elif sub == "reset":
        if "--hard" in args or "--merge" in args:
            return ("deny", "no git reset --hard in a shared tree: it discards other agents' work")
    elif sub == "checkout":
        if ("--" in args or "-f" in args or "--force" in args or "-p" in args or "--patch" in args
                or any(a in (".", "./", ":/") or re.search(r"(^\.{0,2}/|/$|\.\w{1,6}$)", a) for a in args if not a.startswith("-"))):
            return ("deny", "no git checkout of paths in a shared tree: it discards other agents' edits. "
                            "Use git show HEAD:<path> or your own worktree")
    elif sub == "switch":
        if "--discard-changes" in args or "-f" in args or "--force" in args:
            return ("deny", "no git switch that discards changes in a shared tree")
    elif sub == "restore":
        letters = _short_flags(args, "s")
        staged = "--staged" in args or "S" in letters
        worktree = "--worktree" in args or "W" in letters
        if not staged or worktree:
            return ("deny", "git restore only with --staged (unstaging); restoring files discards other "
                            "agents' edits in the shared tree")
    elif sub == "clean":
        if "--force" in args or "f" in _short_flags(args, "e"):
            return ("deny", "no git clean -f in a shared tree: it deletes other agents' new files")
    elif sub == "add":
        pathspecs = [a for a in args if not a.startswith("-") or a in ("-",)]
        if (set(args) & {"--all", "--update", "--no-ignore-removal"} or {"A", "u"} & _short_flags(args, "")
                or any(p in (".", "./", ":/", "*", ":(top)", ":/*") for p in pathspecs)):
            return ("deny", "stage only your own paths: git add <path> ... (never -A, --all, -u or .); "
                            "several agents share this index")
    elif sub == "commit":
        if "--all" in args or "a" in _short_flags(args, "mFcCt"):
            return ("deny", "no git commit -a: commit only your own paths with "
                            "git commit -m \"...\" -- <paths>")
    elif sub == "config":
        if any(a.lower().startswith("alias.") for a in args) and not set(args) & {"--get", "--get-regexp", "--list", "-l", "--unset"}:
            return ("deny", "no git aliases: they hide blocked commands")
    return None


def kill_rules(w):
    args = w[1:]
    pids, i, signal_seen = [], 0, False
    while i < len(args):
        a = args[i]
        if a in ("-s", "-n") and not signal_seen:
            signal_seen = True
            i += 2
            continue
        if a == "--":
            pids.extend(args[i + 1:])
            break
        if a.startswith("-") and not signal_seen and not a.startswith("--"):
            signal_seen = True
        elif a in ("-l", "-L"):
            return None
        else:
            pids.append(a)
        i += 1
    if any(re.fullmatch(r"-\d+|0", p) for p in pids):
        return ("deny", "kill only PIDs you started: no process groups, 0 or -1 (lesson: wave 2)")
    return None


LISTERS = {"pgrep", "pidof", "ps"}


def _top_segments(cmd):
    """Split on ; && || & and newlines outside quotes, $(...), backticks and heredoc-free text (pipes stay joined)."""
    segs, cur, i, n, sq, dq, depth, bt = [], [], 0, len(cmd), False, False, 0, False
    while i < n:
        c = cmd[i]
        if c == "\\" and not sq and i + 1 < n:
            cur.append(cmd[i:i + 2])
            i += 2
            continue
        if c == "'" and not dq and not bt:
            sq = not sq
        elif c == '"' and not sq:
            dq = not dq
        elif not sq and c == "`":
            bt = not bt
        elif not sq and cmd.startswith("$(", i):
            depth += 1
            cur.append("$(")
            i += 2
            continue
        elif not sq and depth and c == "(":
            depth += 1
        elif not sq and depth and c == ")":
            depth -= 1
        elif not (sq or dq or bt or depth):
            two = cmd[i:i + 2]
            if two in ("&&", "||"):
                segs.append("".join(cur))
                cur, i = [], i + 2
                continue
            prev = cmd[i - 1] if i else ""
            if c in ";\n" or (c == "&" and prev not in "<>" and cmd[i + 1:i + 2] != ">"):
                segs.append("".join(cur))
                cur, i = [], i + 1
                continue
        cur.append(c)
        i += 1
    segs.append("".join(cur))
    return [x for x in segs if x.strip()]


def _kill_pids(w):
    args, pids, i, signal_seen = w[1:], [], 0, False
    while i < len(args):
        a = args[i]
        if a in ("-s", "-n") and not signal_seen:
            signal_seen = True
            i += 2
            continue
        if a == "--":
            pids.extend(args[i + 1:])
            break
        if a.startswith("-") and not signal_seen and not a.startswith("--"):
            signal_seen = True
        else:
            pids.append(a)
        i += 1
    return pids


def kill_by_pattern(cmd, line_heads, cwd=None):
    """B-116: a kill of literal PIDs is fine even if the same line lists processes to check them. A kill whose PIDs
    aren't literal is denied when a process lister feeds it: in its own segment (pipe, $(...), xargs), or anywhere
    on the line unless the kill's own segment is a pure lsof port lookup (a lister's output can cross segments in
    a $variable, a file, `cat` or xargs < file)."""
    for seg in _top_segments(cmd):
        cmds = _quiet_commands(seg, cwd)
        seg_heads = {os.path.basename(w[0]).lower() for w, _, _ in cmds}
        for w, _, _ in cmds:
            if os.path.basename(w[0]).lower() != "kill" or {"-l", "-L"} & set(w[1:]):
                continue
            pids = _kill_pids(w)
            if pids and all(re.fullmatch(r"\d+|%[\w+-]*", p) for p in pids):
                continue
            if LISTERS & seg_heads:
                return True
            # A lister elsewhere on the line can reach this kill through a variable, a file or a substitution
            # (T-20-4 r1 finding 1), so only a pure port lookup (lsof) may feed a non-literal kill then.
            if LISTERS & line_heads:
                if not pids or any("$" in p for p in pids) or not (seg_heads - {"kill"} - SHELLS) <= {"lsof"}:
                    return True
    return False


def lesson_rules(cmd, cwd=None):
    cmds = simple_commands(cmd, cwd=cwd)
    heads = [os.path.basename(w[0]).lower() for w, _, _ in cmds]
    enc = encoded_rules(cmd, cwd)
    if enc:
        deny(enc[1])
    if "kill" in heads and kill_by_pattern(cmd, set(heads), cwd):
        deny("no kill by process pattern (pgrep, pidof, ps | grep): kill only PIDs you started, "
             "or look them up by your own port with lsof -ti :<port> (lesson: wave 2)")
    asks = []
    for (w, cwd, git_dir), head in zip(cmds, heads):
        found = None
        if head in ("pkill", "killall"):
            found = ("deny", "no pkill or killall: kill only PIDs you started (save $! or use lsof -ti :<port>) "
                             "(lesson: wave 2)")
        elif head == "kill":
            found = kill_rules(w)
        elif head == "aws":
            found = ("deny", "real AWS accounts are touched only by the owner")
        elif head == "git":
            found = git_rules(w, cwd, git_dir)
        elif head in ("pnpm", "npm"):
            rest = list(w[1:])
            while rest and rest[0].startswith("-"):
                opt = rest.pop(0)
                if opt in ("-C", "--dir", "--filter", "-F", "--prefix", "-w", "--workspace") and rest:
                    rest.pop(0)
            sub = rest[0].lower() if rest else ""
            installs = {"install", "i", "add"} if head == "pnpm" else {"install", "i", "ci", "add", "isntall", "in"}
            if sub in installs:
                asks.append(f"'{head} {sub}' changes node_modules links shared by every agent (lessons: waves 6/7)")
        if not found and head in ("sst", "gh", "pnpm", "npm", "yarn", "bunx"):
            found = setting_rules(w)
        if found and found[0] == "deny":
            deny(found[1])
        if any(re.search(r"db:reset|(^|/)db/reset\.ts$|reset-db", x) for x in w):
            if agent_type is not None and agent_type not in DB_RESET_ROLES:
                asks.append("db:reset wipes the shared dev database; only the gate (qa-engineer or the main "
                            "session) runs it")
    return asks


def text_rules(cmd):
    """The line-level regex rules (deploys, cloud CLIs, secrets, force-push) on raw command text."""
    if re.search(r"\$'[^']*\\(x[0-9a-fA-F]|[0-7]{3}|u[0-9a-fA-F])", cmd):
        deny("no ANSI-C escaped words ($'\\x..'): they hide commands from the guard")
    joined = re.sub(r"\\\n", " ", cmd)
    flat = re.sub(r"""["'\\]""", "", joined)
    segments = re.split(r"&&|\|\||[;|\n]", joined) + re.split(r"&&|\|\||[;|\n]", flat)
    for seg in segments + [joined, flat]:
        for pattern, reason in BASH_RULES:
            if re.search(pattern, seg, re.I):
                deny(reason)
    for seg in re.split(SEGMENT_SPLIT, joined) + re.split(SEGMENT_SPLIT, flat):
        if re.search(PUSH_RULE, seg, re.I):
            deny(PUSH_REASON)


# Commands whose mention of a script name is not a write (round 2: `pnpm vitest run` next to
# `./node_modules/.bin/vitest` is not "written then run").
NAME_READERS = {"pnpm", "npm", "npx", "yarn", "pnpx", "bunx", "pgrep", "pkill", "pidof", "ps", "grep", "egrep",
                "rg", "ls", "which", "type", "stat", "file", "head", "tail", "wc", "less", "lsof", "test", "[",
                "echo", "printf", "cat", "cd", "pushd", "rm", "diff", "kill", "true", "sleep", "exit"}


def _written_here(cmd, word, name):
    """True when the command may create the missing script `word` (basename `name`) before running it: a
    redirect into it, or any other command naming it that isn't a plain reader or another run of it."""
    pat = r"(?<![\w.-])" + re.escape(name) + r"(?![\w.-])"
    run_words = {word, word.removeprefix("./")}
    for seg in re.split(SEGMENT_SPLIT, cmd):
        if not re.search(pat, seg):
            continue
        if re.search(r"(?:>>?|>\||&>>?)\s*[\"']?[^\s;&|]*" + pat, seg):
            return True
        words = [x.strip("\"'") for x in seg.split()]
        while words and (re.match(r"^[A-Za-z_]\w*=", words[0]) or words[0] in PREFIX_CMDS):
            words.pop(0)
        if not words:
            continue
        head = os.path.basename(words[0]).lower()
        if words[0] in run_words or words[0].removeprefix("./") in run_words:
            continue  # this segment runs it
        if head in SHELLS or head in ("source", "."):
            target = _script_target(words)
            if target is not None and target.removeprefix("./") in run_words:
                continue
            return True
        if head in NAME_READERS:
            continue
        return True
    return False


def script_rules(cmd, n_top):
    """Read every script the command runs (and the scripts those run) and apply all the rules to it.
    The first `n_top` refs come from the command itself; only those can be "written in this call"."""
    asks, seen, k = [], set(), 0
    while k < len(SCRIPT_REFS):
        word, cwd = SCRIPT_REFS[k]
        k += 1
        path = _resolve_script(word, cwd)
        if path is None:
            continue
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen.add(real)
        if len(seen) > SCRIPT_MAX_COUNT:
            deny("the command runs too many scripts for the guard to read")
        text = _read_script(real)
        if text is None:
            name = os.path.basename(path)
            if k <= n_top and not os.path.exists(real) and _written_here(cmd, word, name):
                deny(f"the script {name} doesn't exist yet, so the guard can't read it: write it in one "
                     f"call and run it in the next")
            continue
        text_rules(_strip_comments(text))
        PUSH_CTX["in_script"] = True  # a push inside a script is never the one allowed form
        asks += lesson_rules(text, cwd)
    return asks


def main():
    if tool == "Bash":
        cmd = tool_input.get("command", "")
        if not isinstance(cmd, str):
            deny("the guard hook couldn't read the command")
        PUSH_CTX["cmd"] = cmd
        text_rules(cmd)
        asks = lesson_rules(cmd)
        asks += script_rules(cmd, len(SCRIPT_REFS))
        if asks:
            ask(asks[0])
    elif tool.startswith("mcp__"):
        if not READ_ONLY_MCP.search(tool):
            ask(f"'{tool}' can send, publish or change something outside the team")


try:
    main()
except SystemExit:
    raise
except Exception:
    deny("the guard hook hit an error reading this command")
sys.exit(0)
