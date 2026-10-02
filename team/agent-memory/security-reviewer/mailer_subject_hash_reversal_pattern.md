---
name: mailer-subject-hash-reversal-pattern
description: How to test whether a "hash instead of plaintext" logging fix actually protects low-entropy templated content (T-22-3, S-38 example)
metadata:
  type: feedback
---

When a card asks to check that a hash "is not reversible for short subjects" or similar, don't just
check the test proves the plaintext is absent from logs — that's necessary but not sufficient. Write a
quick brute-force PoC (plain node:crypto, no DB needed) against the *real* template the hashed value comes
from (grep for it, e.g. `src/modules/digest/render.ts` subject templates), using any other unhashed
context that's logged alongside it (e.g. `companyId` in the clear narrows "shop name" to zero unknowns).
If the search space is a few hundred thousand candidates or fewer, it's brute-forceable in seconds on one
core — unsalted/unkeyed `sha256Hex` (see its own doc comment in `crypto.ts`: "used to store station
tokens, long random secrets need no salt" — that's the precondition, and templated business text violates
it) is not a fix for low-entropy content, only `hmacHex(secret, value)` is.

**Why:** T-22-3 (2026-09-29) added `subjectHash: sha256Hex(subject).slice(0,16)` to stop weekly net
profit from reaching logs (B-139). The test only checked the literal subject string wasn't logged, which
passed — but the hash itself was fully reversible in 2.5s using the known template + the companyId already
logged in the clear next to it, completely defeating the control's purpose. Recorded as S-38 (Medium),
`invai-docs/security/v1-review.md`.

**How to apply:** Any time a card introduces a hash (not HMAC) as a log-safety measure for anything other
than a long random secret, grep for the template/format string that produces the hashed value, estimate
its real entropy given everything else logged alongside it, and if it's small, write the brute-force
script before approving. The fix is always the same: swap `sha256Hex` for `hmacHex(env.BETTER_AUTH_SECRET,
...)` (precedent: `addressHash` in `src/modules/shipping/service.ts`, also from T-22-3).

See also [[outbound_http_review_pattern]] for the general "prove it, don't just read it" habit.
