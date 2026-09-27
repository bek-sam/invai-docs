---
name: assistant-history-shop-context-pattern
description: T-17-3's tool-memory-line and shop-context-block pattern for the assistant is safe as built — what to re-check if it's extended
metadata:
  type: project
---

T-17-3 (2026-09-26, `invai-backend@5ee0453`) added two things to the assistant loop that are
injection/PII-sensitive by nature, and both checked out clean:

1. **Tool memory line** (`toolMemoryLine` in `src/modules/ai/service.ts`): each earlier assistant
   turn gets a `[Tools used earlier: name (summary); ...]` line prepended to its history text,
   capped at 600 chars, brackets/angle-brackets/newlines stripped, then still passed through the
   gateway's `stripPii(sanitizeText(...))`. It's safe **because** every `summary` string in
   `src/modules/ai/assistant-tools.ts` is built only from counts, money and `CHANNEL_RULES` labels
   — never a design/campaign/connection name or buyer field. It also reads only `name`+`summary`
   from stored `toolCalls`, never `input`.
2. **Shop context block** (`shopContext` in the same file): time zone (`Intl`-validated, falls
   back to UTC), computed weekday/date, and channel **labels** from the fixed `CHANNEL_RULES` map
   — never a channel connection's own name or the shop's display name. Sent as an uncached second
   system block, after the byte-identical cached prefix (`assistantSystem` in
   `src/ai/providers/anthropic.ts`); proven byte-identical across two shops with different
   timezones/channels in `service.test.ts`.

**Why it matters going forward:** both are safe only because they're built from a *closed*
vocabulary (numeric templates, fixed enums) rather than shop free text. If either is ever changed
to include something a shop or buyer typed (a connection nickname, a campaign name, a design
name, a buyer note), that's a new injection/PII surface and needs its own `<data>`-block treatment
or explicit scrubbing, not just character stripping.

**How to apply:** when reviewing a change to `toolMemoryLine`, `shopContext`, or any new assistant
tool's `summary`/`answer` text, check whether the new text could carry shop- or buyer-entered free
text. If yes, that's a new finding, not covered by this pattern being "already reviewed safe".
