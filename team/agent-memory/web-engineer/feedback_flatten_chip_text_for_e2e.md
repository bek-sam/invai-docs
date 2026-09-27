---
name: feedback-flatten-chip-text-for-e2e
description: when a spec's copy table gives one literal sentence for a chip/badge ("Niche: X, Y"), render it as one text node, not adjacent sibling elements (e.g. per-item Badge components) — CSS gap doesn't add real whitespace/commas to the DOM text
metadata:
  type: feedback
---

Built a niche chip as separate `<Badge>` components per niche with a `gap-1.5` flex wrapper,
assuming the visual gap would read as a space to `getByText`/text-content assertions. It doesn't:
`textContent` concatenates adjacent elements with nothing between them ("Niche:Teachers", not
"Niche: Teachers"), and multiple sibling badges have no comma between them at all.

**Why:** both the spec's copy table and QA's e2e test literal-match the combined string
("Niche: Teacher" / "Niches: Teacher, Retirement"). Found by running the actual e2e test, not by
inspection — the rendered screenshot looked fine (CSS gap reads as space visually) while the text
assertion failed.

**How to apply:** when a spec gives one fixed sentence for a compound value (a label + a
comma-joined list), build that exact string in JS (`` `${label}: ${items.join(", ")}` ``) and
render it as a single text node/element, even if wrapping it in one `Badge` for visual styling.
Reserve separate sibling elements for values that are checked individually (e.g. vote buttons,
where each needs its own accessible name).
