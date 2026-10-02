---
name: hash-vs-hmac-for-logs
description: When logging a substitute for sensitive text, use hmacHex (keyed), not sha256Hex — sha256Hex is only safe for long random secrets
metadata:
  type: feedback
---

Never use `sha256Hex` (`src/lib/crypto.ts`) to log a stand-in for low-entropy or guessable text
(email subjects, addresses, any templated string with a small number of unknowns). Use
`hmacHex(env.BETTER_AUTH_SECRET, value)` instead, sliced the same way.

**Why:** `sha256Hex`'s own doc comment says it's for long random secrets (station tokens) that
need no salt. S-38 (T-22-3 round 2, security review) proved a digest-mail subject hashed with
plain `sha256Hex` was reversible in ~2.5s by brute force, because the template
(`"Your week at {{shop}}: net profit {{net}} ({{change}})"`) has too little entropy once the shop
name is already known from an adjacent unhashed log field. The fix mirrors the existing
`addressHash` pattern in `invai-backend/src/modules/shipping/service.ts:2246` (already
`hmacHex`-keyed) — that pattern should have been the template from the start.

**How to apply:** Before adding any `*Hash`/`*LogFields` helper that substitutes for text in a log
line, check whether the underlying value is a long random secret (→ `sha256Hex` is fine) or
anything else a human wrote or a template produced (→ `hmacHex(env.BETTER_AUTH_SECRET, ...)`).
Grep `sha256Hex(` in `src/integrations` and `src/modules` before adding a new one, and prefer
copying `addressHash` over writing a new pattern.
