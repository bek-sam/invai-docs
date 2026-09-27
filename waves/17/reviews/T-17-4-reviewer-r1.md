# Review of T-17-4 (round 1)

- Reviewer: reviewer on claude-sonnet-5
- Author: web-engineer on claude-opus-5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show 11ffbfe --stat` | 3 files: `src/i18n/en.ts`, `src/i18n/es.ts`, `src/routes/_app/assistant.tsx` — exactly the card's owned paths |
| `git -C invai-web status --short` | clean before and after |
| `pnpm typecheck` | `tsc --noEmit` clean |
| `pnpm lint` | `Checked 145 files in 95ms. No fixes applied.` |
| `pnpm test` | `Test Files 15 passed (15)`, `Tests 82 passed (82)` |
| `VITE_API_URL=http://localhost:3142 pnpm build` | `✓ built in 1.41s` (same pre-existing >500kB chunk warnings, unrelated to this diff) |
| `grep -n '"get_\|"compare_periods"' invai-contracts/src/schemas/ai.ts` vs. `sed -n '/tool: {/,/},/p' src/i18n/{en,es}.ts` | all 10 contract enum names present, spelled identically, in both catalogs |
| `grep -rn "assistant.q[1-5]"` across `invai-web/src` | no hits — the old keys are fully removed, nothing left dangling |
| Read 3 of the report's screenshots (`desktop-en-light-empty.png`, `mobile-es-dark-empty.png`, `desktop-en-light-answered.png`) | see below |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | all 10 `assistant.tool.<name>` keys present in both `en.ts`/`es.ts`, verified against the live contract enum, not just the report's claim; `desktop-en-light-answered.png` shows the real chip "Checked advertising" rendered from a live mock-provider call |
| 2 | yes | `desktop-en-light-empty.png` shows exactly the 4 spec starter texts as buttons ("Give me a weekly business review", "Are my ads paying off?", "Which designs are rising or falling?", "Am I shipping on time?"); clicking one is wired to the pre-existing `ask(s)` handler (`onClick={() => void ask(s)}`), and the answered screenshot proves a click actually sends and gets a real reply |
| 3 | yes | `mobile-es-dark-empty.png`: 390×844, dark, Spanish — all 4 starters wrap onto 2 rows with no truncation, no raw `assistant.starter.*` keys, no horizontal scroll; the buttons are plain `<button type="button">` with their visible text as children (native accessible name, native keyboard focus/activation) — unchanged pattern, not something this diff had to add |
| 4 | yes | `git show --stat` and the full diff both confirm only the tool-chip/starter-question lines changed; the chat log, composer, sidebar and credits markup are untouched |

## Judgment: dropping the 5 old suggestion chips for the spec's 4 starters
The 5 removed chips ("TikTok margin this week", "top-profit designs last month", "blanks running out in 7 days", "orders at risk of shipping late", "Etsy vs Amazon late-shipment rates") covered stock, single-channel margin and channel-comparison scenarios the new 4 don't show as buttons. But: (a) the spec's "Web" section names exactly these 4 starters by id (`assistant.starter.review|ads|designs|shipping`), and the card's AC2 requires exactly this set — this wasn't the engineer's discretionary choice, it's what was assigned; (b) nothing is actually lost functionally — the composer still takes any free-text question, and the tools behind the old prompts (`get_stock`, `get_orders_summary`, `get_channel_performance`) are untouched and still answer those same questions when typed, they're just no longer pre-populated as example buttons. This reads as an intentional narrowing to the four analyst-mode entry points the new prompt (T-17-3) is built around, not a regression. No finding.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`assistant.tsx`, `i18n/en.ts`, `i18n/es.ts`, assistant keys only — no other key blocks touched)
- [x] Nothing outside scope
- [x] Tests pass; no test changes in this diff (i18n/UI-only), nothing to weaken
- [x] Tenancy / idempotency — n/a, UI-only, no new request paths
- [x] En/es text: plain, active voice, matches the existing glossary tone; the "Checked advertising"/"Revisó publicidad" vs. "Checked listings"/"Revisó anuncios" split is a deliberate, sound disambiguation (the report's stated reasoning holds: "anuncio" would otherwise do double duty for both "ad" and "listing" in Spanish)
- [x] No PII in the new strings (all static UI copy)
- [x] Decisions recorded in the report (why `assistant.q1`–`q5` were deleted outright rather than left dangling; why `vite build`/`preview` was used instead of `pnpm dev` given the CSP's hard-coded `connect-src`)

## Optional notes (not blocking)
- Product-designer co-review is correctly waived per `wave.md` (decision 0011); I looked at 3 screenshots as instructed and they match the report's claims exactly, including the live mock-provider answer text and ROAS/TACoS formatting from T-17-2.
