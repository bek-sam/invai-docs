---
name: wave-plan-review-pattern
description: How to review a tech-lead wave plan that proposes a copy/wording rule for PM approval
metadata:
  type: project
---

Wave plans (`invai-docs/waves/<n>/wave.md`) sometimes include a "Wording rule proposed for PM approval"
section when a card fixes copy that came out of the previous wave's integration gate (`waves/<n-1>/reviews/gate.md`
issues). Example: wave 20, wording rule for market R1 "past peak" / "peak under way" text and digest
percentage-point vs relative-percent formatting, from wave 19 gate issues 1 and 3.

**Why:** the tech lead and reviewer own wave/card files (read-only for me), but I own `invai-docs/specs/**`.
When a wording rule changes a spec's Copy table, I have to make the edit myself in my own review turn — the
tech lead can't touch specs, and leaving the spec stale means the next spec reader (QA writing acceptance
tests, a future wave) works from outdated copy.

**How to apply:** when reviewing a wave plan with a proposed wording rule —
1. Decide: approve as written, or give exact replacement en/es strings (never leave it to the builder to
   improvise copy).
2. Check the strings against `.claude/skills/write-plain-language-copy/glossary.md` and against sibling rows
   already in the same spec's Copy table (same verb choices, same key-naming style, same tense).
3. Check the wording rule is actually renderable with the data the code already has (grep the relevant
   backend module for the fields a new `{{placeholder}}` needs) — a copy string using a field the draft never
   populates is a real bug, not a nitpick, worth flagging with a file:line.
4. Edit the spec(s) named on the card: add the Copy row(s) plus a one-line addition to the rule/flow text if
   the behavior itself changed (not just the string), and append a dated Review log row explaining what was
   added and why (mirrors the existing round-1 review-log format already in each spec).
5. Write the verdict to `invai-docs/waves/<n>/reviews/plan-pm.md`: verdict, numbered required changes, final
   wording. Do not edit wave/card files — those stay the tech lead's.

See also `invai-docs/specs/market-signals.md` and `invai-docs/specs/weekly-digest.md` "Review log" entries
dated 2026-09-28 for the wave 20 worked example.
