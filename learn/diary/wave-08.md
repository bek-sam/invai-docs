# Wave 8 — AI and marketplace compliance

**Dates:** 2026-09-26. **Gated:** folded into the later "wave 6–9" combined gate (wave 8 has
no standalone `gate.md`). **Pushed:** complicated — see below.

## What was built
- **T-8-1** Etsy listing rules (ai-engineer): AI-written listing copy follows Etsy's own
  rules (the AI-disclosure requirement, `production_partner_ids`, title rules).
- **T-8-2** Prompt isolation and a global AI spend breaker (ai-engineer): untrusted text
  (a buyer's message, a channel's product title) can't steer the model into doing
  something else, and a company-wide circuit breaker stops runaway AI spend.
- **T-8-3** AI cost table and mock hardening (ai-engineer): every AI route's token cost is
  tracked in cents per call, and the mock provider behaves realistically enough to test
  against.
- **T-8-4** Trademark-risk gate (ai-engineer + web-engineer): a listing can't be approved,
  published or exported if it trips the trademark checker — the gate from wave 1's seeded
  marks (T-1-5) made load-bearing.
- **T-8-5** Eval harness (ai-engineer): a repeatable way to score AI output quality before
  and after a prompt or model change, wired into `package.json` and CI.

## Why
Wave 6 shipped the first AI feature (listing copy). Wave 8 is what makes that feature safe
to actually turn on for real shops selling on Etsy, Amazon and TikTok — compliant copy,
no prompt-injection path from untrusted marketplace text, a hard stop on AI spend, and a
trademark check that blocks a listing before it goes out, not after a complaint arrives.

## What went wrong
- `team/lessons.md` records a plain process mistake with real consequences: a builder
  pushed both `invai-backend` and `invai-web` straight to `origin/main`, sending **44
  ungated commits** — most of them already reviewed work from earlier waves, but mixed in
  with its own unreviewed wave 8 card. The root cause: the tech lead's prompt to that
  agent omitted "Don't push," and the builder defaulted to the owner's own standing rule
  (push straight to `main`) because nothing told it that rule didn't apply to it directly.
- The same wave repeated the `git stash`-in-a-shared-tree mistake from wave 4 (see wave
  7's entry) — the written rule existed but wasn't in this builder's prompt either.

## What the team learned
- "Push straight to main" is the owner's standing rule for the *team as a whole*, not a
  default any individual agent should assume applies to it. Every agent prompt from here
  on ends with "Don't push; only the tech lead pushes after the gate," restating the
  `agent-brief.md` line explicitly rather than relying on it being known.
- This is the second wave in a row where a *correctly written* shared rule failed simply
  because it wasn't repeated in the specific prompt that needed it — a pattern that shows
  up often enough in this project's history that by wave 20 it becomes a standing habit:
  critical rules are restated per-prompt, not just filed once in a shared doc.

## Files to look at
- `invai-backend/src/ai/validators/listing.ts` — Etsy rules enforcement (T-8-1).
- `invai-backend/src/ai/gateway.ts`, `src/ai/breaker.ts` — prompt isolation and the spend
  breaker (T-8-2).
- `invai-backend/src/ai/models.ts`, `src/ai/credits.ts` — the cost table (T-8-3).
- `invai-backend/src/modules/ai/trademark.ts` — the trademark gate wired into
  `approveDraft`, `publishDraft`, `exportListingsCsv` (T-8-4).
- `invai-backend/evals/` — the eval harness (T-8-5).
- `invai-docs/team/lessons.md` (2026-09-26, "Wave 8" rows) — the 44-ungated-commits push
  and the repeated `git stash` mistake.
