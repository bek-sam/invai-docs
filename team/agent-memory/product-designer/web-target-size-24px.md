---
name: web-target-size-24px
description: Web (invai-web/invai-ui) minimum touch target is 24x24px per add-ui-component skill, not the 44px stated in my role principles; floor stays 64px+.
metadata:
  type: project
---

`add-ui-component` skill states: "targets ≥ 24 × 24 px on web, ≥ 64 px for floor components." My role file's
general principle says "44 px targets (floor 64 px+)" for accessibility. These aren't contradictory in
practice — 44px is the WCAG-recommended comfortable minimum I should push for on primary actions, but 24x24
(WCAG 2.2 §2.5.8) is the actual enforced floor for invai-ui web components. Inline text links are exempt from
target-size minimums entirely under 2.5.8.

**Why:** Found during T-21-5 review (2026-09-29): a new small language-toggle `<button>` on public help/legal
pages was ~28px tall. Didn't block on it since it met the skill's stated 24px web minimum and matched an
existing small-toggle pattern elsewhere in the app.

**How to apply:** When reviewing web components, don't block solely for being under 44px if they clear 24×24
and aren't a primary/destructive action. Do push for 44px+ on primary CTAs, and always require 64px+ on any
floor-facing component (`build-floor-flow`, `[[floor-64px-non-negotiable]]` if that memory exists).
