---
name: probe-parsers-with-backend-template
description: When web parses a backend-built free-text string, probe it with a throwaway test that builds input from the exact backend template
metadata:
  type: feedback
---
2026-09-30 T-P2-4: to check a web helper that parses a backend-built message (orders/service.ts:639), copy the backend's template literal into a throwaway vitest file in the repo. Run it on the edge cases (null from, reason with parens or a colon, empty reason, wrong format), then delete the file and check `git status` is clean.

**Why:** the author's tests used hand-written strings. Building the input from the real template proves the parser and the producer agree.

**How to apply:** use this for any card that parses `message`/`summary` text, until typed codes (reasonCode, B-224) replace it.
