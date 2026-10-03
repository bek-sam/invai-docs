# Review of T-27-4 (round 2, S-52 only)

- Reviewer: security-reviewer on opus
- Author: integrations-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command / check | Result |
|---|---|
| `git show dca1668` | 4 files: client.ts (opt-in flag), media.ts (productUpdate sets false), media.test.ts (+1 test), security.test.ts |
| security.test.ts diff | one word: `it.fails(` → `it(`; body and assertions unchanged |
| `grep -rn retryServerErrors src` (non-test) | only client.ts def/branch and media.ts:275; default `!== false` keeps retry for every other caller |
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/integrations/channels` | 12 files, 83 passed (r1: 81 + 1 expected fail; +1 new media test, S-52 proof now passes) |

## Finding status
- S-52 (Medium, integrity): fixed. A 5xx on the media `productUpdate` now reaches the caller once; the caller's retry runs the read-back. Reads and other mutations still retry 5xx. Marked fixed in `security/v1-review.md`.

## Checks
- [x] Only owned paths changed (channels/shopify/**); my test file changed by the agreed one-word flip only
- [x] No weakened tests; new media test asserts one update call and that reads still retry
- [x] No new findings
