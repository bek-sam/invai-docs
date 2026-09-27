"""Shared helpers for the InvAI fast-check, verification tracker and verification gate hooks.

Used by post-edit-check.py, track-verify.py and verify-gate.py. Not used by guard-bash.py, which stays
self-contained so it can fail closed without depending on anything else.
"""
import fcntl
import json
import os
import re
import shlex
import tempfile
import time
from pathlib import Path

REPO_RE = re.compile(r"^invai-(contracts|ui|backend|web|floor|infra|imaging)(?:$|[-_.])")
# Edits to these never need the repo checks (docs, images).
DOC_EXT = {".md", ".mdx", ".txt", ".rst", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".ico"}
STATE_MAX_AGE_S = 2 * 24 * 3600


# ---------- repos ----------

def find_repo(path):
    """(root, kind) of the InvAI code repo or worktree holding `path`, or None (docs, unknown)."""
    if not path:
        return None
    p = Path(os.path.realpath(os.path.expanduser(path)))
    for d in [p, *p.parents]:
        if (d / ".git").exists():
            m = REPO_RE.match(d.name)
            return (str(d), m.group(1)) if m else None
    return None


def is_worktree(root, kind):
    return Path(root).name != f"invai-{kind}"


def required_checks(kind):
    if kind == "imaging":
        return ["lint", "test"]
    if kind == "infra":
        return ["typecheck", "lint"]
    checks = ["typecheck", "lint", "test"]
    if kind in ("web", "floor"):
        checks.append("build")
    return checks


def check_command(root, kind, check):
    if kind == "imaging":
        return {"lint": "uv run ruff check .", "test": "uv run pytest"}[check]
    if is_worktree(root, kind):  # never run pnpm in a worktree (lessons, waves 6/7)
        return {
            "typecheck": "node_modules/.bin/tsc --noEmit",
            "lint": "node_modules/.bin/biome check .",
            "test": "node_modules/.bin/vitest run",
            "build": "node_modules/.bin/vite build",
        }[check]
    return f"pnpm {check}"


# ---------- state ----------

def state_dir():
    env = os.environ.get("INVAI_HOOK_STATE_DIR")
    if env:
        d = Path(env)
    elif os.environ.get("CLAUDE_PROJECT_DIR"):
        d = Path(os.environ["CLAUDE_PROJECT_DIR"]) / ".claude" / "state"
    else:
        d = Path(__file__).resolve().parent.parent / "state"
    d.mkdir(parents=True, exist_ok=True)
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n")
    return d


def _safe(s):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(s))[:80] or "x"


def state_file(session_id, agent_id):
    return state_dir() / f"verify__{_safe(session_id or 'nosession')}__{_safe(agent_id or 'main')}.json"


def prune(d):
    now = time.time()
    for f in d.iterdir():
        try:
            if f.name != ".gitignore" and now - f.stat().st_mtime > STATE_MAX_AGE_S:
                f.unlink()
        except OSError:
            pass


def read_state(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"repos": {}}


def update_state(path, fn):
    """Locked read-modify-write with an atomic replace. `fn(state)` mutates the dict."""
    path = Path(path)
    with open(str(path) + ".lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state(path)
        state.setdefault("repos", {})
        fn(state)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        with os.fdopen(fd, "w") as f:
            json.dump(state, f)
        os.replace(tmp, path)
    prune(path.parent)
    return state


def pending_checks(state):
    """[(root, kind, [missing checks])] for repos edited after their last successful checks."""
    out = []
    for root, r in sorted(state.get("repos", {}).items()):
        edited = r.get("edited_at", 0)
        ok = r.get("ok", {})
        missing = [c for c in required_checks(r["kind"]) if ok.get(c, 0) <= edited]
        if missing:
            out.append((root, r["kind"], missing))
    return out


# ---------- verification command parsing ----------

SEPARATORS = {"&&", "||", ";", "|", "&", "|&", ";;", "&;"}
def _tokens(cmd):
    cmd = re.sub(r"\\\n", " ", cmd).replace("\n", " ; ")
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    return list(lex)


def _segments(cmd):
    """Split into simple commands: [{words, op, here}] where op is the operator after the command.

    '(' and ')' are kept as marker segments; the operator after ')' is given to the command before it.
    `here` holds here-strings (`bash <<< 'pnpm test'`), so a shell fed one can be re-read.
    """
    segs, cur, here = [], [], []
    toks = _tokens(cmd)
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in SEPARATORS:
            if cur:
                segs.append({"words": cur, "op": t, "here": here})
                cur, here = [], []
            elif segs and segs[-1]["words"] == [")"]:
                for s in reversed(segs):
                    if s["words"] not in (["("], [")"]) and s["op"] is None:
                        s["op"] = t
                        break
        elif t in ("(", ")"):
            if cur:
                segs.append({"words": cur, "op": None, "here": here})
                cur, here = [], []
            segs.append({"words": [t], "op": None, "here": []})
        elif t == "<<<":
            if i + 1 < len(toks):
                here.append(toks[i + 1])
            i += 1
        elif t[:1] in ("<", ">") or t in ("&>", "&>>"):
            if cur and cur[-1].isdigit():
                cur.pop()
            i += 1  # skip the redirect target
        else:
            cur.append(t)
        i += 1
    if cur:
        segs.append({"words": cur, "op": None, "here": here})
    return segs


def _known_success(segs):
    """Given the whole command exited 0: "sure" segments succeeded; "piped" ones only did under pipefail."""
    real = [s for s in segs if s["words"] not in (["("], [")"])]
    # group into pipelines
    pipes, cur = [], []
    for s in real:
        cur.append(s)
        if s["op"] not in ("|", "|&"):
            pipes.append(cur)
            cur = []
    if cur:
        pipes.append(cur)
    ok = [False] * len(pipes)
    for i in range(len(pipes) - 1, -1, -1):
        if i == len(pipes) - 1:
            ok[i] = pipes[i][-1]["op"] in (None, ";")
        else:
            ok[i] = pipes[i][-1]["op"] == "&&" and ok[i + 1]
    result = {}
    for i, p in enumerate(pipes):
        for j, s in enumerate(p):
            if ok[i]:
                result[id(s)] = "sure" if j == len(p) - 1 else "piped"
    return result


def _strip_prefixes(w):
    w = list(w)
    changed = True
    while w and changed:
        changed = False
        if re.match(r"^[A-Za-z_]\w*=", w[0]):
            w.pop(0); changed = True
        elif w[0] in ("env", "time", "command", "exec", "nice", "npx", "caffeinate"):
            w.pop(0); changed = True
        elif w[0] in ("timeout", "gtimeout") and len(w) > 1:
            w.pop(0)
            while w and w[0].startswith("-"):
                w.pop(0)
            if w:
                w.pop(0)
            changed = True
        elif w[0] == "perl" and "-e" in w and any("exec" in x and "ARGV" in x for x in w):
            k = next(i for i, x in enumerate(w) if "exec" in x and "ARGV" in x)
            w = w[k + 1:]; changed = True
    return w


def _positional(args, value_opts=()):
    pos, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a == "--":
            continue
        if a.startswith("-"):
            if a in value_opts:
                skip = True
            continue
        pos.append(a)
    return pos


VITEST_FILTERS = ("-t", "--testNamePattern", "--changed", "--related", "--project", "--shard", "--dir", "--root")
PYTEST_FILTERS = ("-k", "-m", "--lf", "--last-failed", "--deselect", "--co", "--collect-only", "--sw", "--stepwise")


def _has_filter(args, filters):
    return any(a == f or a.startswith(f + "=") for a in args for f in filters)


def classify(words):
    """-> (check, dir or None, leaf tool) for a full-repo verification command, else None."""
    w = _strip_prefixes(words)
    if not w:
        return None
    tool = os.path.basename(w[0])
    args = w[1:]
    if tool == "pnpm":
        d = None
        while args and args[0].startswith("-"):
            a = args.pop(0)
            if a in ("-C", "--dir") and args:
                d = args.pop(0)
            elif a.startswith("--dir="):
                d = a.split("=", 1)[1]
            elif a in ("--filter", "-F"):
                return None
        if not args:
            return None
        sub = args.pop(0)
        if sub == "run" and args:
            sub = args.pop(0)
        if sub in ("exec", "dlx"):
            r = classify(args)
            return (r[0], r[1] or d, r[2]) if r else None
        if sub in ("typecheck", "lint", "test", "build"):
            if _positional(args) or _has_filter(args, VITEST_FILTERS):
                return None
            return (sub, d, "pnpm-script")
        r = classify([sub, *args])  # pnpm <bin> ...
        return (r[0], r[1] or d, r[2]) if r else None
    if tool in ("uv", "uvx"):
        d = None
        while args and args[0].startswith("-"):
            a = args.pop(0)
            if a in ("--directory", "--project") and args:
                d = args.pop(0)
        if tool == "uv":
            if not args or args.pop(0) != "run":
                return None
            while args and args[0].startswith("-"):
                a = args.pop(0)
                if a in ("--with", "--group", "--extra", "--python", "--directory", "--project") and args:
                    v = args.pop(0)
                    if a in ("--directory", "--project"):
                        d = v
        r = classify(args)
        return (r[0], r[1] or d, r[2]) if r else None
    if tool in ("python", "python3") and len(args) >= 2 and args[0] == "-m":
        return classify(args[1:])
    if tool in ("tsc", "tsgo"):
        if "--build" in args or "-b" in args or _positional(args, ("-p", "--project")):
            return None
        return ("typecheck", None, tool)
    if tool == "biome":
        if not args or args[0] not in ("check", "ci"):
            return None
        pos = _positional(args[1:], ("--reporter", "--max-diagnostics", "--config-path", "--diagnostic-level",
                                     "--log-level", "--log-kind", "--colors", "--stdin-file-path"))
        return ("lint", None, tool) if all(p in (".", "./") for p in pos) else None
    if tool == "vitest":
        if not args or (args[0] != "run" and "--run" not in args):
            return None
        rest = args[1:] if args[0] == "run" else args
        if _positional(rest, ("--reporter", "--pool", "--config", "-c")) or _has_filter(rest, VITEST_FILTERS):
            return None
        return ("test", None, tool)
    if tool == "vite":
        return ("build", None, tool) if args[:1] == ["build"] else None
    if tool == "ruff":
        if not args or args[0] != "check":
            return None
        pos = _positional(args[1:], ("--output-format", "--config", "--select", "--ignore"))
        return ("lint", None, tool) if all(p in (".", "./") for p in pos) else None
    if tool in ("pytest", "py.test"):
        if _positional(args, ("-p", "--rootdir", "-c", "--maxfail", "--tb", "-n")) or _has_filter(args, PYTEST_FILTERS):
            return None
        return ("test", None, tool)
    return None


IMAGING_TOOLS = {"ruff", "pytest", "py.test"}


def parse_verifications(cmd, cwd, output=""):
    """[(root, kind, check)] that a successful (exit 0) Bash command proves.

    `output` is unused since round 2: a piped check is credited only under `set -o pipefail`.
    """
    segs = _segments(cmd)
    known = _known_success(segs)
    pipefail = False  # a piped check counts only under `set -o pipefail`: `| tail` or `| head` hides the exit code
    stack = [cwd]
    found = []
    for s in segs:
        w = s["words"]
        if w == ["("]:
            stack.append(stack[-1]); continue
        if w == [")"]:
            if len(stack) > 1:
                stack.pop()
            continue
        if w and w[0] in ("cd", "pushd"):
            target = w[1] if len(w) > 1 else "~"
            target = os.path.expanduser(os.path.expandvars(target))
            if target == "-" or "$" in target:
                stack[-1] = None  # unknown directory from here on
            elif os.path.isabs(target):
                stack[-1] = os.path.normpath(target)
            elif stack[-1] is not None:
                stack[-1] = os.path.normpath(os.path.join(stack[-1], target))
            continue
        if w and w[0] == "set" and "pipefail" in w:
            k = w.index("pipefail")
            pipefail = k > 0 and (w[k - 1] == "-o" or re.fullmatch(r"-[a-z]*o", w[k - 1]) is not None)
            continue
        status = known.get(id(s))
        if status is None or (status == "piped" and not pipefail):
            continue
        if w and os.path.basename(w[0]) in ("sh", "bash", "zsh"):
            bodies = list(s.get("here", []))
            c_at = next((k for k, x in enumerate(w[1:], 1) if re.fullmatch(r"-[a-z]*c[a-z]*", x)), None)
            if c_at is not None and c_at + 1 < len(w):
                bodies.append(w[c_at + 1])
            for body in bodies:
                if stack[-1] is not None:
                    found.extend(parse_verifications(body, stack[-1]))
            continue
        c = classify(w)
        if not c:
            continue
        check, d, tool = c
        if d is not None:
            d = os.path.expanduser(os.path.expandvars(d))
        if stack[-1] is None and not (d and os.path.isabs(d)):
            continue
        repo = find_repo(os.path.join(stack[-1], d) if d and stack[-1] else (d or stack[-1]))
        if not repo:
            continue
        root, kind = repo
        if (kind == "imaging") != (tool in IMAGING_TOOLS):
            continue
        if check in required_checks(kind):
            found.append((root, kind, check))
    return found
