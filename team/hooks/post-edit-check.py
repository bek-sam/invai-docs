#!/usr/bin/env python3
"""PostToolUse fast check for Edit/Write/MultiEdit: lint the edited file and typecheck its repo.

- .ts/.tsx/.js/.jsx/.mjs/.cjs/.mts/.cts/.json in a TS repo or a worktree of one: `biome check <file>`
  (read-only: never --write/--fix), then the repo's `tsc --noEmit` for code files and tsconfig*.json.
  Every repo typechecks in 0.3-1.4 s today (T-16-1 report); if tsc ever takes over 8 s it is skipped
  for an hour and the model is told to run it itself.
- .py in invai-imaging: `ruff check --no-fix --no-cache <file>`.
- Anything else exits at once.
Problems go back to the model as JSON (`decision: block` + reason for errors, `additionalContext` for
warnings only), at most 40 lines, file:line first, errors in the edited file first.

Fails OPEN, unlike guard-bash.py which fails closed: the guard is a control that must deny what it
can't read, while this hook only gives feedback, so a crash, a timeout or a missing tool exits 0 and
never blocks an edit. Its own subprocess timeouts (6 + 10 s) stay under the hook timeout (20 s).
"""
import json
import os
import sys

TS_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".json", ".jsonc"}
TYPECHECK_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}
MAX_LINES = 40
TSC_BUDGET_S = 8.0


def main():
    data = json.load(sys.stdin)
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ""
    ext = os.path.splitext(path)[1].lower()
    if ext not in TS_EXT and ext != ".py":
        return
    import re
    import subprocess
    import time

    sys.dont_write_bytecode = True  # no __pycache__ next to the hooks (sync.sh copies hooks/* flat)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import invai_hooklib as h

    cwd = data.get("cwd") or os.getcwd()
    path = os.path.realpath(path if os.path.isabs(path) else os.path.join(cwd, path))
    repo = h.find_repo(path)
    if not repo:
        return
    root, kind = repo
    rel = os.path.relpath(path, root)
    if "node_modules" in rel.split(os.sep):
        return

    def tool(name, venv=False):
        sub = (".venv", "bin", name) if venv else ("node_modules", ".bin", name)
        for base in (root, os.path.join(os.path.dirname(root), f"invai-{kind}")):
            p = os.path.join(base, *sub)
            if os.path.exists(p):
                return p
        return None

    errors, warnings, notes = [], [], []

    if kind == "imaging":
        if ext != ".py":
            return
        ruff = tool("ruff", venv=True)
        if not ruff:
            return
        r = subprocess.run([ruff, "check", "--no-fix", "--no-cache", "--output-format=concise", rel],
                           cwd=root, capture_output=True, text=True, timeout=6)
        for line in r.stdout.splitlines():
            if re.match(r"^.+:\d+:\d+: ", line):
                errors.append(line.strip())
    else:
        if ext not in TS_EXT:
            return
        biome = tool("biome")
        if biome:
            r = subprocess.run([biome, "check", "--reporter=json", "--colors=off", "--no-errors-on-unmatched",
                                "--files-ignore-unknown=true", rel],
                               cwd=root, capture_output=True, text=True, timeout=6)
            try:
                report = json.loads(r.stdout)
            except ValueError:
                report = {}
            for d in report.get("diagnostics", []):
                loc = d.get("location") or {}
                start = loc.get("start") or {}
                where = f"{loc.get('path') or rel}:{max(start.get('line') or 1, 1)}:{max(start.get('column') or 1, 1)}"
                cat = d.get("category", "")
                msg = d.get("message", "")
                if cat == "format":
                    msg = f"not formatted as Biome wants (fix: node_modules/.bin/biome check --write {rel})"
                line = f"{where} {d.get('severity', 'error')} {cat}: {msg}"
                (errors if d.get("severity") in ("error", "fatal") else warnings).append(line)
        base = os.path.basename(rel)
        tsc = tool("tsc") if os.path.isdir(os.path.join(root, "node_modules")) else None
        if tsc and (ext in TYPECHECK_EXT or (base.startswith("tsconfig") and ext == ".json")):
            slow_file = h.state_dir() / "fastcheck-slow.json"
            try:
                slow = json.loads(slow_file.read_text())
            except (OSError, ValueError):
                slow = {}
            if slow.get(root, 0) > time.time():
                notes.append(f"Typecheck skipped (over {TSC_BUDGET_S:.0f} s here): run it yourself before you finish.")
            else:
                t0 = time.time()
                try:
                    r = subprocess.run([tsc, "--noEmit", "--pretty", "false"], cwd=root,
                                       capture_output=True, text=True, timeout=10)
                    out = r.stdout
                except subprocess.TimeoutExpired:
                    out = ""
                if time.time() - t0 > TSC_BUDGET_S:
                    slow[root] = time.time() + 3600
                    tmp = str(slow_file) + f".{os.getpid()}"
                    with open(tmp, "w") as f:
                        json.dump(slow, f)
                    os.replace(tmp, slow_file)
                mine, other = [], []
                for line in out.splitlines():
                    m = re.match(r"^(.+?)\((\d+),(\d+)\): (error|warning) (TS\d+): (.*)$", line)
                    if not m:
                        continue
                    f_, ln, col, sev, code, msg = m.groups()
                    item = f"{f_}:{ln}:{col} {sev} {code}: {msg}"
                    same = os.path.normpath(f_) == os.path.normpath(rel)
                    (mine if same else other).append(item)
                errors.extend(mine)
                if other:
                    errors.extend(other[:10])
                    notes.append(f"{len(other)} type error(s) in other files: from your change, or another "
                                 "agent's work in progress in this tree.")

    if not errors and not warnings and not notes:
        return
    head = f"Fast check after editing {rel} ({os.path.basename(root)}):"
    body = errors + warnings
    room = MAX_LINES - 1 - len(notes)
    if len(body) > room:
        body = body[:room - 1] + [f"... {len(errors) + len(warnings) - (room - 1)} more"]
    text = "\n".join([head, *body, *notes])
    if errors:
        print(json.dumps({"decision": "block", "reason": text}))
    else:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
