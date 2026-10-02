---
name: review-checks-ai-provider
description: Checks that paid off (or were needed) when reviewing AI provider / SDK integration cards where no real key exists and tests stub the HTTP layer
metadata:
  type: project
---

Stub-HTTP tests cannot catch API-contract mistakes; read the installed SDK to close that gap.
**Why:** T-P8-ai-openai (2026-10-01) shipped an OpenAI provider with no key. The fetch stub proves request
shape and gateway accounting, but not what the live API rejects. Things worth reading in `node_modules`
instead of trusting the report: `ReasoningEffort` union (does `'none'` exist), `helpers/zod.js` +
`lib/transform.js` (strict schema throws on `.optional()` without `.nullable()`; grep prompt schemas for
`.optional(`), whether `store:false` loops replay reasoning items with `include: ["reasoning.encrypted_content"]`,
and whether `input_tokens_details.cached_tokens` is subtracted from `input_tokens` (double-billing otherwise).
**How to apply:** any card adding or changing an LLM/SDK provider; list the `.d.ts` files read in the evidence table.

Full-suite runs overlapping another agent's edits or test run give phantom failures.
**Why:** my first full run on this card reported 1 failed file while the author committed a follow-up
(3889bf6) mid-run; re-run on a stable tree with `pgrep -fl vitest` empty passed. Filtering with
`grep -E "FAIL |Test Files|Tests  "` on a saved log survives the noisy stderr; `tail` alone loses the FAIL line.
**How to apply:** before the full suite, `git status --short` + `pgrep -fl vitest`; save the log to /tmp and grep it.

The guard-bash hook blocks a single Bash call that chains many commands ("too many scripts"); split reads
into separate parallel calls. Memory lives at `/Users/bekbolsun/invai/.claude/agent-memory/reviewer/`
(workspace root), not inside a repo.
