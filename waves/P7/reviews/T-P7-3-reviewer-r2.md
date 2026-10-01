# Review of T-P7-3 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: web-engineer on Claude Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show --stat a23e4ef` | 5 files, 5 insertions / 7 deletions: `scripts/i18n-es.json`, `src/i18n/en.ts`, `src/i18n/es.ts`, `src/routes/_app/-assistant.test.ts`, `src/routes/_app/assistant.tsx` |
| `git -C invai-web show a23e4ef` (full diff, read in full) | see below |
| `pnpm vitest run src/routes/_app/-assistant.test.ts --reporter=dot` | 1 file, 5/5 passed |
| `pnpm typecheck` (invai-web, head) | `tsc --noEmit` clean (confirms `es.ts`'s `Messages`-typed key still lines up with `en.ts`) |
| `git -C invai-web status --short` | only qa-engineer's uncommitted `e2e/**` + `.scratch-hold-probe.ts` (per instructions: not this card, ignored) |

## Acceptance criteria (round-1 criteria, re-checked for round-2 scope)
| # | Met? | Evidence |
|---|---|---|
| r1 AC2 (copy no longer implies the shop owner can raise the cap) | yes | All 4 string instances changed in lockstep: `src/i18n/en.ts` default, `src/i18n/es.ts` default, `scripts/i18n-es.json`, and the inline `t(...)` fallback in `assistant.tsx`. Old: "Your shop's AI limit... ask the owner to raise it." / "...pídele al propietario que lo aumente." New: "Today's AI limit has been reached. Try again tomorrow." / "Se alcanzó el límite de IA de hoy. Vuelve a intentarlo mañana." — no "shop's", no "owner"/"propietario", consistent with my r1 optional note (the cap is `AI_DAILY_TENANT_CAP_CENTS`/platform-wide, not owner-adjustable) |
| r1 AC5 (tests exercise the mapping, none weakened) | yes | `-assistant.test.ts`'s only change is `expect(msg).toContain("today")` → `expect(msg).toContain("Today")`, matching the new default's capitalized sentence-initial "Today's..." — still checks the real assertions (`toContain`, `not.toBe` the raw server string); the other 4 tests (credits_exhausted, refusal, internal, unknown/missing) are untouched and still green |

## Nothing else changed
`git show a23e4ef` confirms exactly: the 4 string-copy edits + the 1 test-assertion case change. No logic, no new keys, no other file touched. `scripts/i18n-es.json` and `es.ts`/`en.ts` stay in sync (one key, one new value in all three).

## Blocking findings
none

## Checks
- [x] Only owned paths changed (5 files above, all inside `invai-web/src/{i18n,routes}` + `scripts/i18n-es.json`, matching r1's owned-path scope)
- [x] Nothing outside scope: this round only fixes the r1 optional note's exact wording problem, nothing broader
- [x] Tests exercise the behavior, none weakened: assertion target changed only to match the new (still plain-language, still non-echoing) default string; `not.toBe(rawServerMessage)` kept
- [x] en/es strings present and in sync across `en.ts`, `es.ts`, `i18n-es.json`; tú-form Spanish kept ("Vuelve", "intentarlo")
- [x] Decisions: none needed, this is a copy fix per my r1 note

## Optional notes (not blocking)
- My r1 note also flagged `es.ts`'s "propietario" vs. the catalog's usual "dueño" — moot now, "propietario" was removed along with "owner" in this fix.
