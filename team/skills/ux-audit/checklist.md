# UX audit checklist

Tick per screen. Anything unticked is a finding.

## Prevent the expensive mistake
- [ ] Floor: a mismatch shows full-screen red BLOCKED with Expected vs Scanned, and nothing lets the user continue (no "press anyway").
- [ ] Destructive or costly actions (cancel order, void label, buy labels in bulk, approve a trademark-flagged draft) need an explicit confirm; reversible ones use undo instead.
- [ ] Holds, cancels and `needs_mapping` / `needs_artwork` are visible where the next person works (pick list, sheet build, pack).

## Urgency
- [ ] Ship-by and at-risk come first; `ShipByBadge` and `StatusBadge` colors mean the same thing everywhere.
- [ ] Relative times ("4 weeks ago") are translated in Spanish and don't read as urgent when the order is done.
- [ ] Today answers "what's late, what's blocked, am I making money" without scrolling at 1440.

## Speed for repeat work
- [ ] Office can filter, select all and act in bulk; filters are remembered.
- [ ] Keyboard works for the main action; the command palette finds the screen.
- [ ] 5,000-row lists stay responsive (virtualized) and show counts.

## Language (en / es)
- [ ] Every string is translated, including toasts, errors, empty states and dates.
- [ ] Shop words: blank, transfer, gang sheet, press, tote, pack. No system words (tenant, entity, payload).
- [ ] Errors say what happened and what to do next.
- [ ] Spanish fits: no clipped buttons or broken table headers.

## States
- [ ] Loading, empty (with the next action), error (with retry), partial (some rows failed) and success.
- [ ] Long names (40-character design, long personalization) don't break the layout.
- [ ] Plan-limit hit (`PLAN_LIMIT_REACHED`, HTTP 402) explains what to do.

## Layout and access
- [ ] Today and Orders work at 390 px with no horizontal scroll.
- [ ] Light and dark both meet WCAG 2.1 AA contrast; focus is visible.
- [ ] Touch targets: 44 px on the web, 64 px or more on the floor (gloves).
- [ ] No meaning by color alone: icons or words back up green and red.
- [ ] Floor: sound on PRESS and BLOCKED, readable from 1 m, works offline and shows queued scans.

## Evidence
- [ ] No console errors or failed requests (the `shoot.mjs` output).
