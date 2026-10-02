# Lesson 13.13 — Running your own AI team: roles, skills, cards, waves, reviews, hooks, budget

## 1. In one sentence
You'll write a small, real version of InvAI's own agent-team setup — one role file,
one skill, one task card, a tiny two-task "wave," and a review template — and run it
by hand (not literally spawning agents) to feel exactly what each piece prevents,
before reading the real `.claude/` setup this whole project runs on.

## 2. Why it exists
InvAI itself is built by a team of AI agents, not one. That only works because the
things a human team gets from structure — "who owns this," "what does done mean,"
"who checks the work," "don't do anything risky without asking" — are written down
as files an agent actually reads, not assumed. Without a role file, two agents can
both believe they own the same code. Without a task card's acceptance criteria,
"done" means whatever the agent that built it decided it meant. Without an
independent review, a change ships because the person (or agent) who wrote it also
decided it was good — the one checker least likely to catch their own mistake.
`CLAUDE.md`'s own rule states this plainly: "Nothing is pushed without passing tests
**and** an independent review by a different agent."

The token-budget rule exists for a more concrete reason: this project actually ran
out of usage mid-wave, more than once, in its real history (decision 0018,
2026-09-29) — "the session usage limit stopped the whole team about every 4–5 hours,"
with relaunched agents redoing finished work. Structure here isn't theoretical
process for its own sake; every rule in this lesson maps to a real incident that
already happened once.

## 3. How it works

### Step 1 — a role file
```markdown
---
name: widget-builder
description: Owns src/widgets/** -- build features for the widgets module only.
skills: [task-intake, verify-and-report]
---
# Widget builder

You build backend features inside `src/widgets/`. You never edit `src/auth.ts` or
another module's folder. Every change needs a passing test and an independent
review before it's considered done.
```
This is the whole trick of a role file: it's not a personality, it's a **scope
boundary** — explicit owned paths, explicit skills loaded, explicit limits on what
this role may touch.

### Step 2 — a tiny skill
```markdown
# verify-and-report

## When to use
Before reporting any task as done.

## Steps
1. Run `pnpm typecheck && pnpm test` and paste the exit code, not the full log.
2. Confirm you exercised the feature for real (a curl, a screenshot) — not just
   that it compiled.
3. Report: what you built, how you verified it, known gaps. Under 10 lines.
```
A skill is just a checklist a role is told to follow at a specific moment — the same
thing a human onboarding doc would say, written so an agent actually reads it before
the step it matters for, not buried in a wall of general instructions.

### Step 3 — a task card
```markdown
# T-1-1: Add widgets.list pagination

| Field | Value |
|---|---|
| Owner | widget-builder |
| Reviewer | reviewer |
| Risk flags | none |

## Owned paths
- src/widgets/**

## Acceptance criteria
1. Given 150 widgets exist, when listing with limit=50, then exactly 50 return
   with a non-null nextCursor.
2. Given the last page, when listing, then nextCursor is null.

## Verification
- pnpm typecheck && pnpm test
- curl the real endpoint with a seeded company of 150 widgets
```
The acceptance criteria are written as Given/When/Then **before** the feature is
built — the same "red first" idea from lesson 13.10, applied to planning instead of
tests.

### Step 4 — a tiny wave, run by hand
Pretend to be two roles yourself, in order: build `T-1-1` as `widget-builder`
(actually write the pagination code and make the criteria pass), then switch hats
entirely — re-read only the card and the diff, *not* your own reasoning while
building it — and review it as `reviewer` would: re-run the verification commands
yourself, check each acceptance criterion against real output, and write a verdict.
```markdown
# Review of T-1-1
Verdict: approve
## Acceptance criteria
1. Met — curl with 150 seeded widgets returned 50 + nextCursor. ✓
2. Met — last page returned nextCursor: null. ✓
```
Doing this switch deliberately — closing the mental model you had while building,
and checking only what the evidence in front of you actually shows — is the real
value of "a different agent reviews," even when you're simulating both sides
yourself.

### Step 5 — a hook, and why it's not optional
```python
#!/usr/bin/env python3
# guard.py -- a PreToolUse hook: read the Bash command about to run, block if risky
import sys, json
cmd = json.load(sys.stdin)["tool_input"]["command"]
if "push --force" in cmd or "rm -rf" in cmd:
    print("blocked: destructive command needs a human", file=sys.stderr)
    sys.exit(2)
```
A hook runs automatically, before the risky thing happens — unlike a rule in a
prompt, which an agent could simply forget, misread, or (if its context got long
enough) lose track of entirely.

## 4. In our code
- `.claude/agents/backend-engineer.md:1-13` — a real role file's frontmatter:
  `name`, `description` (what it owns and explicitly does *not* own — "Not for
  src/ai... or core infrastructure"), `model: opus`, and a `skills:` list it loads —
  the exact shape your Step 1 file echoed.
- `invai-docs/waves/templates/task-card.md` — the real task card template: Owner,
  Reviewer, Co-reviewers, Risk flags, Owned paths, Acceptance criteria as
  Given/When/Then, Verification, and a Budget line ("escalate... if blocked for more
  than about 30 minutes").
- `invai-docs/waves/templates/review.md` — the real review template: a verdict
  (approve/changes-required/escalate), a re-run evidence table, an acceptance
  criteria table, and a checklist including "none were weakened (no `.skip`,
  loosened assertions...)" — the real version of your Step 4 verdict.
- `.claude/hooks/guard-bash.py:1-20` — the real guard hook: blocks force-pushes,
  history rewrites, deploys, `aws` commands, and (per a named, dated lesson,
  T-16-2) restricts `git push` to only the main session or the tech-lead agent — a
  rule added *after* a real incident, not written speculatively.
- `invai-docs/decisions/0018-token-budget.md` — the real token-budget decision,
  written after the night of 2026-09-28–29 when "the session usage limit stopped
  the whole team about every 4–5 hours," agents were relaunched and redid finished
  work, and up to 6 agents ran at once against a cap of 3–4 — the real incident
  behind `CLAUDE.md`'s token-budget rules this course's own operator follows.
- `invai-docs/team/lessons.md:43-44, 56` and `invai-docs/decisions/0020-is-reprint
  -means-re-pressed.md` — two more real, dated incidents worth reading end to end:
  the **shared-Redis flakes** (parallel agents sharing one Redis DB produced
  confusing, hard-to-reproduce test failures across waves 20–P5, eventually fixed
  structurally rather than by one more written rule) and the **reprint profit bug**
  (`isReprint` was read as "not a real sale" by finance code, so every reprinted
  order showed $0 revenue and a false loss on 44 real seed orders — fixed by
  deciding, once, what the flag actually means, and removing every reader's wrong
  assumption).
- Module 10 (`10-ai-team/`) — the full lesson on roles, waves, reviews, hooks and
  the token budget, including these same incidents covered in more depth.

## 5. What it uses
- **Role files (`.claude/agents/*.md`)** — frontmatter plus instructions that scope
  one agent's ownership, model, and preloaded skills.
- **Skills** — reusable, named checklists an agent loads at a specific moment
  (before editing, before reporting done), instead of one long prompt trying to
  cover every situation at once.
- **Task cards** — the unit of planned work: one owner, explicit owned paths, a
  reviewer, and acceptance criteria written before the build starts.
- **Hooks** — scripts that run automatically around a tool call (before a Bash
  command, say) to block something structurally, rather than relying on a written
  rule being remembered.

## 6. Try it yourself
1. Deliberately build `T-1-1` from Step 3 with one acceptance criterion
   unmet (say, `nextCursor` is always `null`, even on a full page) and then review
   it as a genuinely different pass — re-run the curl yourself before trusting your
   own "it works" from five minutes earlier. Did switching hats actually catch it?
2. Read `invai-docs/team/lessons.md` lines 43–44 and 56 end to end (not just the grep
   snippet above) and write, in one sentence each, what *structural* fix followed
   each incident — not just "be more careful next time."
3. Open `.claude/hooks/guard-bash.py` and find one rule that exists because of a
   specific, dated lesson (the file's own comments cite several). Pick one and trace
   it back to the incident in `invai-docs/team/lessons.md` that caused it to be
   added.

## 7. Common mistakes
- Writing a role file as a personality ("be helpful and thorough") instead of a
  scope boundary (what paths it owns, what it explicitly doesn't touch). The real
  value is in what it *prevents* two agents from both believing they own.
- Reviewing your own work "as if" you were someone else without actually re-running
  anything — just re-reading your own reasoning and nodding along. The real
  `independent-review` playbook is explicit that a reviewer re-runs the verification
  commands and checks evidence, it doesn't just re-read the author's claims.
- Treating a written rule in a prompt as equivalent to a hook. A rule can be
  forgotten, misread, or lost in a long context; a hook runs mechanically every time,
  which is exactly why this project's worst-case actions (force-push, deploy, `aws`
  commands) are hook-blocked, not just written down as policy.

## 8. Check yourself
<details>
<summary>1. Why does a task card's acceptance criteria get written as Given/When/
Then *before* the build starts, rather than described after the fact?</summary>

Writing it first (the same "red first" idea from testing, lesson 13.10) means
"done" is defined independent of whatever the implementation ends up doing — it
can't quietly be redefined to match whatever got built. It also gives a reviewer a
fixed target to check evidence against, instead of trusting the builder's own
account of what they accomplished.
</details>

<details>
<summary>2. What's the real difference between a rule written in a role's prompt
and a rule enforced by a hook?</summary>

A prompt rule depends on the agent reading, remembering and correctly applying it —
which can fail if the context gets long, the instruction is ambiguous, or the agent
simply makes a mistake. A hook runs automatically around the specific tool call it
guards, every single time, regardless of what the agent currently believes the
rules are — which is why the genuinely risky, hard-to-undo actions in this project
are hook-blocked rather than left to a written instruction.
</details>

<details>
<summary>3. The reprint profit bug (decision 0020) wasn't fixed by telling finance
code authors "be careful with isReprint." What was actually different about the
real fix?</summary>

The team wrote down, once and explicitly, what `isReprint` actually means
("re-pressed at least once," informational, never a sale/non-sale filter) as a
recorded decision, then went through and removed every place that had assumed the
wrong meaning. The fix was a shared definition everyone could point back to, not a
reminder to be more careful — the same kind of structural fix the shared-Redis flakes
also eventually got (isolating test databases by default) instead of one more
written rule asking agents to remember to pin their own Redis DB.
</details>

## 9. Words to know
- **Role file** — a markdown file (with frontmatter) scoping one agent's ownership,
  model, and preloaded skills.
- **Skill** — a reusable, named checklist an agent loads at a specific point in its
  work, instead of one long always-on instruction set.
- **Task card** — the unit of planned work: owner, owned paths, reviewer,
  Given/When/Then acceptance criteria, written before the build starts.
- **Wave** — a small batch (at most 5 cards, 3–4 agents at once) of task cards run
  together, with a review gate before the next wave starts.
- **Hook** — a script that runs automatically around a tool call, enforcing a rule
  mechanically rather than relying on it being remembered.
- **Independent review** — a different agent re-running verification and checking
  evidence against acceptance criteria, rather than trusting the author's own
  account.
