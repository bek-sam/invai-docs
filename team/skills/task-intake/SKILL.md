---
name: task-intake
description: Start any InvAI task card the same way. Read the card, confirm owned and read-only paths, restate the acceptance criteria, check dependencies and list unknowns before touching code. Use at the start of every card (T-<wave>-<k>), bug fix or assigned task, or when someone says "pick up", "start" or "take this card".
---

# Task intake

Before any edit, you know exactly what you own, what "done" means and what could stop you, and you have
written it down.

## When to use
- You were given a task card `invai-docs/waves/<n>/T-<n>-<k>-<slug>.md`.
- You were given a task in chat with no card (bug, incident follow-up, security fix).
- You are resuming a card after a review round sent it back.

## Steps
1. **Find the card.** `ls invai-docs/waves/*/T-*` and open yours. No card? Ask the tech lead for one. For an
   urgent bug or incident, write the intake note (step 8) as your first report and continue.
2. **Check it is complete.** Compare it with `invai-docs/waves/templates/task-card.md`. It must have:
   - a scope ref (`product/scope.md#<anchor>` or `always-in-scope: bug / security / incident / compliance`),
   - one owner and a reviewer,
   - owned paths and read-only paths,
   - acceptance criteria and verification commands.
   If a field is missing, stop and tell the tech lead. Don't guess owned paths.
3. **Confirm the scope ref.** Open `invai-docs/product/scope.md` and find the anchor. If the work isn't there
   and isn't an always-in-scope class, stop: that is a `scope-change-request`, not your call.
4. **Confirm ownership.** Your role's paths are in `invai-docs/team/operating-system.md` ("The team"). The
   card's owned paths must sit inside them. If the card asks you to edit something another role owns, follow
   `respect-ownership`.
5. **Read the spec and decisions.**
   - The spec named on the card (`invai-docs/specs/<slug>.md`).
   - Decisions that touch the area: `grep -il "<area>" invai-docs/decisions/*.md`. Don't reopen an accepted
     decision (`decisions/README.md`).
   - The backlog row the card came from (`invai-docs/waves/backlog.md`, ids `B-NN`) and its source (research
     10–12 gap ids, `security/v1-review.md` S-ids).
6. **Check dependencies.** For each "Depends on" and "Interfaces promised" line:
   - the provider's stub exists (`grep -rn "<functionName>" <repo>/src`),
   - contract changes are in `invai-contracts/src/contract/` before backend or UI work (change order:
     contracts → backend → web/floor, `CLAUDE.md`).
   If a stub is missing, tell the tech lead. Work on the parts that don't need it.
7. **Check the risk flags.** Each flag pulls in a co-reviewer and a playbook:
   - `tenancy`, `pii`, `auth`, `webhooks`, `files`, `payments` → `threat-model-change` before coding,
     `security-reviewer` co-reviews.
   - `migration` → `backend-foundation` co-reviews.
   - `ui` → `write-plain-language-copy`, `product-designer` co-reviews.
   - `ai` → `ai-engineer` co-reviews.
   - a golden-path area → `run-golden-path` before you report.
8. **Write the intake note** (keep it in your working notes and put it at the top of your final report):
   ```
   Card: T-<n>-<k>  Owner: <role>  Scope ref: <ref>
   Owned (edit): <paths>
   Read-only: <paths>
   Acceptance criteria, in my words:
     1. <Given/When/Then, with the role, starting state and observable result>
   Verification I will run: <commands from the card + DoD commands>
   Risk flags → co-reviewers: <list>
   Unknowns / questions: <list, each with who can answer>
   Plan: <3–7 steps>
   ```
9. **Resolve unknowns.** Technical choices inside the card are yours: decide, and record anything
   cross-cutting with `record-decision`. Questions about scope, money, outside systems or weakening a control
   go to the tech lead or `escalate-to-owner`. Never block silently for more than about 30 minutes of work
   (card "Budget").
10. **Read before changing.** Run `read-before-change` for the files and libraries you will touch.

## Rules
- MUST NOT edit anything before steps 1–4 pass.
- MUST restate every acceptance criterion. If you can't restate one as something observable, ask before
  building.
- MUST treat "Out of scope" on the card as a hard fence, even when the extra work looks small.
- MUST NOT start a card whose provider stubs are missing by writing the stub in someone else's paths.
- MUST NOT widen a card yourself. Bigger than planned → tell the tech lead (card "Budget").

## Done when
- The intake note exists, with all 8 fields filled.
- Every owned path is inside your role's paths in `operating-system.md`.
- Every unknown has an owner or an answer.
- Dependencies are either present or reported to the tech lead.

## References
- `invai-docs/waves/templates/task-card.md`, `invai-docs/waves/README.md`
- `invai-docs/team/operating-system.md` (ownership table, wave steps, who reviews whom)
- `CLAUDE.md` (change order, definition of done)
- Next playbooks: `read-before-change`, `respect-ownership`, `acceptance-tests-first` (QA),
  `verify-and-report`
