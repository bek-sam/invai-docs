---
name: usability-test-plan
description: Write a usability test plan and script (en/es) that the owner runs with a real shop user, such as a presser on the floor tablet or an office worker clearing orders, then turn the owner's notes into ranked findings. Use before building a risky new flow, before a pilot goes live, or when an audit can't settle a UX question.
---

# Usability test plan

The owner gets a ready-to-run session kit (tasks, script, setup, note sheet) in the tester's language, and the
team gets findings tied to what real shop staff did, not what they said.

## When to use
- A new floor flow or a big web change is about to be built or has just landed (`build-floor-flow`,
  `build-dashboard-screen`).
- Before a pilot goes live, to check its presser, packer and office user can finish the core tasks without
  help.
- A `ux-audit` finding is disputed ("staff will figure it out").
- Churn or support tickets point at one screen.

## Steps
1. **Write one research question.** For example: "Can a Spanish-speaking presser in gloves press 5 shirts,
   including a mismatch, with no help?" or "Can an office user clear 20 `needs_mapping` orders in under 5
   minutes?"
2. **Pick the participants** (the owner recruits; you never contact anyone):
   - 5 people per round finds most problems; 3 is fine for a quick check between waves.
   - Match the real users: floor staff (presser, picker, packer, receiver), office or order prep, owner, and a
     DTF vendor for the portal.
   - Cover the segment: a small shop's owner who does every job; a mid-size shop's specialist.
   - Floor sessions run in the participant's language. Plan for Spanish.
3. **Choose the setup.**
   - Seed data only (Desert Bloom Tees) on a local laptop or tablet. A shop's real data is only allowed
     locally and only with the owner's approval.
   - Floor: a 10-inch tablet or a 1280×800 browser, a real USB or Bluetooth scanner if possible, a printed
     gang sheet (open the sheet PDF from **Production → Gang Sheets**), and some blanks with barcodes. Paired
     with `stationToken` from `invai-backend/seed-output.json`, PINs 1111–1188.
   - Note what to reset between sessions. Ask the tech lead for a fresh seed; don't `db:reset` the shared DB
     yourself.
4. **Write 3–6 tasks** as shop goals, not UI instructions. Say "Press this order's shirt", not "Click Press".
   Each task has:
   - a start state (screen, logged in as whom, which order or sheet),
   - a success criterion you can observe,
   - a time limit,
   - one planted problem where it matters: a wrong blank, a personalization overflow, an unmapped SKU or a
     missing item at pack.
5. **Write the script** in `script-template.md` (this folder) form, in English and Spanish. Keep Spanish
   natural and shop-floor plain (`write-plain-language-copy`). Don't translate UI labels differently from the
   app's `es` strings; check `invai-web/src/i18n/es.ts` and `invai-floor/src/i18n/es.ts`.
6. **Define what's measured** per task: success (yes, with help, no), time, errors (wrong press attempted,
   wrong item packed), and a 1–7 ease rating after the task. Add 1–2 open questions at the end.
7. **Save the kit** at `invai-docs/design/usability/<slug>/plan.md`, with the script and a blank note sheet.
8. **Hand it to the owner** with `send-owner-draft`: the kit, a consent line for the participant (no recording
   of faces without consent; never record buyer names), the time needed (30–45 min), and equipment. Add an
   `escalate-to-owner` entry if the plan needs spending (a gift card for the participant) or real data.
9. **After the sessions,** the owner's notes arrive. Write `invai-docs/design/usability/<slug>/findings.md`:
   - a task-by-task table (success rate, median time, errors),
   - findings ranked with the support severity scale (blocks shipping > wrong print > staff time > annoyance)
     and how many participants hit each,
   - quotes (translated, and kept in Spanish when given in Spanish), with participants as P1–P5 and no names.
10. **Route the results** as in `ux-audit` step 9: `invai-ui` fixes yourself, cards for web and floor through
    the tech lead, and a note to customer-success if training (not the product) is the fix.

## Rules
- MUST have the owner run every session with a real person. Agents never contact shops or staff.
- MUST write floor scripts in Spanish as well as English, and test in the participant's language.
- MUST use seed data unless the owner approved real data for a local-only session.
- MUST NOT help the participant during a task. The script says what to say when they're stuck.
- MUST NOT store names, faces, voices or shop names in the repo. Use P1–P5 and the segment.
- MUST NOT count "I liked it" as success. Only completed tasks and observed errors count.

## Done when
- `design/usability/<slug>/plan.md` has the question, participants, setup, tasks with success criteria, en and
  es script, measures and a note sheet.
- The kit is in the owner inbox as a draft.
- After the sessions, `findings.md` has per-task results and ranked findings, each routed to a fix, card or
  training note.

## References
- `script-template.md` (this folder)
- `.claude/agents/product-designer.md` (who you design for)
- `invai-docs/build/demo-guide.md` steps 7–9 (floor) and 2–3 (office)
- Related playbooks: `ux-audit`, `send-owner-draft`, `escalate-to-owner`, `onboard-shop`
