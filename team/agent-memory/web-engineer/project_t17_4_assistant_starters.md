---
name: project-t17-4-assistant-starters
description: wave 17 added 5 new/untranslated assistant tool names and replaced ad-hoc suggestion chips with 4 spec starter questions (T-17-4, 2026-09-26)
metadata:
  type: project
---

Wave 17 (`invai-docs/waves/17/`) gave the assistant "business analyst" tools: `compare_periods`, `get_ad_performance`, `get_design_insights`, `get_fulfillment_health` (new in T-17-2), plus `get_production_status` which existed as a backend-only tool since T-13 but had no web tool-chip label until T-17-4. All 10 tool names now have `assistant.tool.<name>` labels in `invai-web/src/i18n/{en,es}.ts`.

The assistant's empty-conversation screen used to show 5 arbitrary suggestion chips (`assistant.q1`–`q5`); T-17-4 replaced them with the spec's 4 starter questions (`assistant.starter.review|ads|designs|shipping`, `specs/assistant-business-analyst.md` "Web" section) reusing the same click-to-send `ask()` handler — no new component needed, it was a copy/i18n change to `invai-web/src/routes/_app/assistant.tsx`.

**Why it matters for later cards:** if a future wave adds more analyst tools, follow the same pattern — add the enum value in contracts, then add both `assistant.tool.<name>` labels by hand (never `pnpm i18n`, per the agent brief), matching the existing "Checked X" (en) / "Revisó X" (es) verb-noun pattern for chips that look up data, and a distinct verb for tools that don't just "check" (e.g. `compare_periods` → "Compared periods"/"Comparó periodos").
