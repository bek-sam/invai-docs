# Review of T-P7-3 (round 2)

- Reviewer: product-designer on Claude Opus 5.5
- Author: tech lead (copy choice), implemented by web-engineer, on Claude Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show a23e4ef` | 5 files, exactly the `spendCap` string (en.ts, es.ts, scripts/i18n-es.json) plus one test assertion updated for the new text |
| `git -C invai-web show a23e4ef --stat` | confirms no other key, component or path touched |
| `invai-docs/team/skills/write-plain-language-copy/glossary.md` | no glossary term applies to this string; no internal word, no blame, no vague error |
| `grep -rn "upgrade.limit.aiCredits\|cantAnswer" invai-web/src/i18n/{en,es}.ts` | sibling assistant error strings are same length/register; new string matches |

## Round-1 findings re-checked
1. "or ask the owner to raise it" clause — **resolved.** New EN/ES drop it entirely; text no longer implies any shop-side control over a cap that can be the platform-wide pool.
2. "propietario" vs "dueño" inconsistency — **resolved** (the whole owner-reference clause was removed, so the wrong word is gone, not just replaced).

## Copy check (write-plain-language-copy)
- Says what happened ("today's AI limit reached") and what to do next ("try again tomorrow") — no false claim, no guidance that can't work.
- Tú form kept in ES ("Vuelve a intentarlo"), matches catalog register.
- Under 15 words both languages; no internal terms (cap, tenant, platform) leaked into UI text.
- Placeholder-free string, nothing to keep in sync.
- Test change (`toContain("today")` → `toContain("Today")`) tracks the new text's capitalization only; not a weakened assertion.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] en/es present and in sync (en.ts, es.ts, scripts/i18n-es.json all updated together)
- [x] Copy says what happened and what to do next, and nothing false

## Optional notes
- None.
