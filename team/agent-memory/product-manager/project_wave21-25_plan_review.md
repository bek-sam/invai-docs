---
name: wave21-25-plan-review
description: PM review of tech-lead wave plans 21-25 (2026-09-28) — verdicts, the B-131 spec-ownership call, and the wave-10/11 resequencing determination
metadata:
  type: project
---

Reviewed 2026-09-28. Verdicts written to `invai-docs/waves/<n>/reviews/plan-pm.md`:
- Wave 21 (docs/legal/help): approve.
- Wave 22 (P2 sweep backend): approve with changes — T-22-1's scope ref lists item 4 (gang sheets, untouched by the card) and omits item 8 (profit, needed for the TikTok-fee AC that T-22-5 consumes).
- Wave 23 (P2 sweep screens/floor/AI): approve with changes — B-131's fix (`specs/market-signals.md` Step 3, seasonality index formula) must be PM-authored, not an engineering grant reviewed by PM. `invai-docs/specs/**` is exclusively PM-owned per `team/operating-system.md` rows 22/97. T-23-4's card should not list `specs/**` as an owned path for ai-engineer/backend-engineer.
- Wave 24, 25 (deployable/operable, agent parts): approve. These resume roadmap waves 10/11, which the owner deferred 2026-09-25 "until ready to go live" — that was a resequencing decision (order became 6→7→8→9→12→13→14→15), not a ban on writing the code; the roadmap itself says the code "will be ready and in mock mode". Waves 24/25 only build/locally verify (hard fence: no deploy, no aws, no secrets, no accounts), so they don't reopen the 2026-09-25 decision. No new owner sign-off needed to build this wave, only to later run `sst deploy`.

**B-131 follow-up owed:** I need to write the actual Step 3 spec text change in `invai-docs/specs/market-signals.md` (detrend before computing the seasonality index — currently SI is computed from raw/trended data, so a rising niche's growth leaks into SI and then contaminates the trend's deseasonalization) before/alongside T-23-4 starts. Not yet done as of this review — only the determination that it's needed was recorded.

**Non-blocking note passed to tech lead both waves:** `waves/backlog.md` still labels this content "wave 25"/"wave 26" (pre-renumbering); actual folders are 24/25. Cosmetic, tech-lead's file.
