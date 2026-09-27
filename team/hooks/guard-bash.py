#!/usr/bin/env python3
"""PreToolUse guard for the InvAI team (see invai-docs/team/operating-system.md).

- Bash: denies force-pushes, history or remote rewrites, tag pushes, deploys, cloud CLIs,
  and secret or repo-setting changes.
- Bash, the recurring lessons (invai-docs/team/lessons.md, T-16-2):
  - `git push` only from the main session or the tech-lead agent (waves 2 and 8);
  - no `git stash` (except list/show), `git reset --hard`, `git checkout -- <path>|.`,
    `git restore` without --staged, `git clean -f` in the shared trees (waves 4 and 8);
  - no `pkill`, `killall`, or `kill` fed by a process pattern (wave 2); plain `kill <pid>` is fine;
  - no `git add -A/--all/-u/.` or `git commit -a` (handbook: commit only your own paths);
  - the owner approves `pnpm install/i/add` and `npm install/i/ci` (waves 6/7);
  - the owner approves `db:reset` unless the caller is the main session or qa-engineer (gates).
- MCP tools: anything that isn't clearly read-only (send, publish, create, update,
  delete...) needs the owner's explicit approval ("ask").

Fails closed: if the input can't be parsed, or the guard itself errors, the call is denied.
The new rules read shell words (shlex), following `bash -c`, `eval`, `$(...)`, backticks, pipes into
a shell and simple VAR=value assignments, so text inside a commit message doesn't trip them. A
determined bypass (base64 + eval, a script written to a file then run, shell aliases) is out of reach
of any denylist; the guard stops the mistakes the lessons record.
"""
import json
import os
import re
import shlex
import sys

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

BASH_RULES = [
    (GIT + r"push\b.*(--force|--force-with-lease|--mirror|--delete|--tags|--follow-tags|\s-[a-zA-Z]*[fd]\b|\s\+\S+|\s:\S+|refs/tags|\sv\d)",
     "no force-push, ref deletion, mirror or tag push (tags deploy production)"),
    (GIT + r"remote\s+(add|remove|rm|set-url|rename)\b", "never change remotes"),
    (GIT + r"(filter-branch|filter-repo)\b", "never rewrite history"),
    (r"(^|[\s/])(sst\s+(deploy|remove)|cdk\s+(deploy|destroy)|terraform\s+(apply|destroy)|pulumi\s+(up|destroy))\b",
     "deploys to real environments are triggered by the owner (deploy-to-environment)"),
    (r"\bpnpm\b.*\b(sst:deploy|deploy:\w+)\b", "deploys to real environments are triggered by the owner"),
    (r"\bgh\s+workflow\s+run\b", "running workflows (deploy.yml) is triggered by the owner"),
    (r"\bgh\s+run\s+(rerun|cancel)\b", "re-running or cancelling workflow runs (deploys) is done by the owner"),
    (r"\bgh\s+(secret|variable)\s+(set|delete|remove)\b", "secrets and variables are changed by the owner"),
    (r"\bgh\s+repo\s+(delete|edit|rename|archive)\b", "repo settings are changed by the owner"),
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


def _lex(cmd):
    """[(words, op_before)] simple commands, or None if shlex can't parse it."""
    cmd = cmd.replace("\n", " ; ")
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        return None
    out, cur, op = [], [], None
    for t in toks:
        if t and set(t) <= OPS:
            if cur:
                out.append((cur, op))
            cur, op = [], t
        else:
            cur.append(t)
    if cur:
        out.append((cur, op))
    return out


def _fallback(cmd):
    """Quote-stripped regex split, used when shlex can't parse (heredocs with apostrophes and such)."""
    flat = re.sub(r"""["'\\]""", "", re.sub(r"\\\n", " ", cmd))
    out = []
    for part in re.split(r"(&&|\|\||\||;|&|\n|\$\(|`|[(){}])", flat):
        if part and part.strip() and not re.fullmatch(r"&&|\|\||\||;|&|\n|\$\(|`|[(){}]", part):
            out.append((part.split(), None))
    return out


def _strip_prefix(w):
    w = list(w)
    while w:
        head = os.path.basename(w[0]).lower()
        if re.match(r"^[A-Za-z_]\w*=", w[0]) or head in PREFIX_CMDS:
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
        elif head == "perl" and any("ARGV" in x for x in w):
            k = next(i for i, x in enumerate(w) if "ARGV" in x)
            w = w[k + 1:]
        else:
            break
    return w


def simple_commands(cmd, depth=0):
    """Every simple command in `cmd` as a word list (prefixes stripped, $VARS from VAR=value expanded)."""
    if depth > 4:
        deny("the command nests shells too deeply for the guard to read")
    cmd = re.sub(r"\$\{?IFS\}?", " ", re.sub(r"\\\n", " ", cmd))
    text, bodies = _substitutions(cmd)
    parsed = _lex(text)
    items = parsed if parsed is not None else _fallback(cmd)
    env, result = {}, []
    for body in bodies:
        result.extend(simple_commands(body, depth + 1))
    for idx, (words, op) in enumerate(items):
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
        w = _strip_prefix(words)
        if not w:
            continue
        result.append(w)
        head = os.path.basename(w[0]).lower()
        if head in SHELLS:
            c_at = next((i for i, x in enumerate(w[1:], 1) if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", x)), None)
            if c_at is not None and c_at + 1 < len(w):
                result.extend(simple_commands(w[c_at + 1], depth + 1))
            elif op in ("|", "|&") and not [x for x in w[1:] if not x.startswith("-")]:
                j = idx - 1  # a pipe into a shell: read every earlier word in the pipeline as a command
                while j >= 0:
                    for x in items[j][0]:
                        result.extend(simple_commands(x, depth + 1))
                    if items[j][1] not in ("|", "|&"):
                        break
                    j -= 1
        elif head == "eval" and len(w) > 1:
            result.extend(simple_commands(" ".join(w[1:]), depth + 1))
        elif head == "find":
            for k, x in enumerate(w):
                if x in ("-exec", "-execdir", "-ok", "-okdir"):
                    rest = w[k + 1:]
                    end = next((j for j, y in enumerate(rest) if y in (";", "+", "\\;")), len(rest))
                    result.extend(simple_commands(" ".join(shlex.quote(y) for y in rest[:end]), depth + 1))
        elif re.match(r"^(python\d*(\.\d+)?|node|ruby|perl|deno|bun)$", head):
            code = next((w[k + 1] for k, x in enumerate(w[:-1]) if x in ("-c", "-e", "--eval", "-p")), None)
            if code:  # shell strings inside inline code: os.system("git stash"), ["git", "push"]
                lits = [m.group(2) for m in re.finditer(r"([\"'])(.*?)(?<!\\)\1", code)]
                for lit in lits + [" ".join(lits)]:
                    result.extend(simple_commands(lit, depth + 1))
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


def git_rules(w):
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


def lesson_rules(cmd):
    cmds = simple_commands(cmd)
    heads = [os.path.basename(w[0]).lower() for w in cmds]
    asks = []
    for w, head in zip(cmds, heads):
        found = None
        if head in ("pkill", "killall"):
            found = ("deny", "no pkill or killall: kill only PIDs you started (save $! or use lsof -ti :<port>) "
                             "(lesson: wave 2)")
        elif head == "kill":
            found = kill_rules(w)
            if not found and {"pgrep", "pidof", "ps"} & set(heads):
                found = ("deny", "no kill by process pattern (pgrep, pidof, ps | grep): kill only PIDs you started, "
                                 "or look them up by your own port with lsof -ti :<port> (lesson: wave 2)")
        elif head == "git":
            found = git_rules(w)
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
        if found and found[0] == "deny":
            deny(found[1])
        if any(re.search(r"db:reset|(^|/)db/reset\.ts$|reset-db", x) for x in w):
            if agent_type is not None and agent_type not in DB_RESET_ROLES:
                asks.append("db:reset wipes the shared dev database; only the gate (qa-engineer or the main "
                            "session) runs it")
    return asks


def main():
    if tool == "Bash":
        cmd = tool_input.get("command", "")
        if not isinstance(cmd, str):
            deny("the guard hook couldn't read the command")
        if re.search(r"\$'[^']*\\(x[0-9a-fA-F]|[0-7]{3}|u[0-9a-fA-F])", cmd):
            deny("no ANSI-C escaped words ($'\\x..'): they hide commands from the guard")
        joined = re.sub(r"\\\n", " ", cmd)
        flat = re.sub(r"""["'\\]""", "", joined)
        segments = re.split(r"&&|\|\||[;|\n]", joined) + re.split(r"&&|\|\||[;|\n]", flat)
        for seg in segments + [joined, flat]:
            for pattern, reason in BASH_RULES:
                if re.search(pattern, seg, re.I):
                    deny(reason)
        asks = lesson_rules(cmd)
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
