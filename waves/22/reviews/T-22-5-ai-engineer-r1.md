# Review of T-22-5 (round 1)

- Reviewer: ai-engineer on Sonnet 5
- Author: backend-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 19c16a5 --stat` / `-- src/modules/ai/service.ts` | Diff is exactly `foldAttributes()` (new, exported) + one call-site line in `toContent`, plus `listing-attributes.test.ts`. No prompt, model, gateway, credits or validator change. |
| `node_modules/.bin/vitest run --reporter=dot src/modules/ai src/ai` (invai_t22_5a, REDIS_URL redis://localhost:6379/11) | `Test Files 13 passed (13)`, `Tests 171 passed (171)`, exit 0 (includes the new fold test) |
| dropped `invai_t22_5a` after | done |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC5 (B-167): one attributes shape end to end per ADR 0017 | yes | `foldAttributes` trims keys, drops empty keys, first-key-wins, `__proto__` stays plain data (`Object.fromEntries` on a `Map`, never object-literal spread); matches ADR 0017 rules 2–3 exactly. Test covers all three fold cases plus the `__proto__` prototype-pollution case explicitly. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — grant was `src/modules/ai/service.ts`, mapping only; the hunk touches nothing else (no prompt text, `models.ts`, gateway, credits or `validators/listing.ts` change)
- [x] Nothing outside scope
- [x] `toContent`'s output still flows through `normalizeListing`/schema validation unchanged (`grep` shows `toContent` call sites at lines 477/488 unchanged); structured-output parsing of `copy.attributes` (`{key,value}[]`) happens upstream in the gateway before `foldAttributes` ever runs, so the Zod-schema contract for `ListingCopy` is untouched
- [x] Model-output text reaches only a plain string map (`Record<string,string>`), never a channel payload unsanitised and never raw HTML; `Object.fromEntries` on a `Map` means a `"__proto__"` key from the model becomes an own data property, not prototype pollution (asserted by the new test) — this is the "prototype" risk the grant called out, and it's closed
- [x] AI evals/unit tests unaffected: full `src/modules/ai` + `src/ai` suite green (171/171), same counts as the architect's r1 pass
- [x] Decisions recorded where needed — ADR 0017 applied verbatim, no new decision needed

## Optional notes (not blocking)
None.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
