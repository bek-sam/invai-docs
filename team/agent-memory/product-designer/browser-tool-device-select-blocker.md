---
name: browser-tool-device-select-blocker
description: As a subagent (co-reviewer etc.) the claude-in-chrome tool can require picking between connected Chrome devices, but AskUserQuestion isn't available to answer it — plan for code-level review as fallback.
metadata:
  type: feedback
---

`mcp__claude-in-chrome__tabs_context_mcp` can error with "Multiple Chrome browsers are connected... call AskUserQuestion" when more than one device is linked to the account. As a spawned subagent (e.g. product-designer co-reviewer), `AskUserQuestion` is often not in the tool list, so this can't be resolved — browser-based screenshotting is then unavailable for that session.

**Why:** happened during T-23-2 review (2026-09-29): dev server started fine on :5190, but no screenshots could be taken because device selection couldn't be answered, and the author's referenced screenshot files also weren't present anywhere on disk to fall back on.

**How to apply:** when this happens, don't block the review on it — do a thorough code-level trace instead (exact i18n strings, the component that renders them, tone/color/icon logic, button size tokens) and say plainly in the review's evidence table that pixel screenshots weren't captured and why. Still stop any dev server you started. If a future session does have `AskUserQuestion` available, use it to pick a browser rather than giving up on screenshots.
