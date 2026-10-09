# Review of T-29-3 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: web-engineer on Sonnet 5.5 (invai-web 8d134d7)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (web) | exit 0 |
| `pnpm exec biome check` on the 8 changed files | clean, no fixes |
| `pnpm vitest run src/content` / full `pnpm test` | 3 files 22 passed / 26 files 181 passed, exit 0 |
| `pnpm build` with no env / `VITE_API_URL=http://localhost:3000 pnpm build` | throws "VITE_API_URL must be set" / built OK. Pre-existing: `vite.config.ts` untouched since d7029ff (T-23-1); the throw is the deliberate CSP guard |
| Red on base: new test + new component copied into a 4559618 worktree | 4 of 9 fail (line breaks, `---`, unsafe links, purged label); image and raw-HTML cases pass on base (base renderer never emits `<img>`; React escapes) |
| Mutations on 8d134d7: `isSafeAppPath` -> `startsWith("/")`; AI image branch disabled | link test fails (caught) / all 9 pass (not caught, see note 1) |
| Node probe of `isSafeAppPath` (24 inputs) + AI parse of 13 nesting probes | rejects `//`, `/\`, `\/`, `javascript:`, `data:`, leading space, `/\t/`, `/\n/`, `/\r/`, NUL, NBSP, U+2028, U+3000, fullwidth solidus; accepts `/%2F%2F`, `/%5C`, `/%09/`, `/` + U+200B (all stay a same-origin path, never decoded into an authority). Links/images inside bold, italic, heading, table, quote, list, `<url>`, ref-style and `[![i](x)](/o)`: zero link or image nodes |
| `scan-test-weakening.sh invai-web 4559618` | only hits: two `as Record` casts in the new test; 0 assertions removed, 32 added |
| `grep -rn dangerouslySetInnerHTML src` | none |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | B-270 sample renders strong/h4/ul/ol/table, no `**` `###` pipe left; half `**up` stays text |
| 2 | yes | AI paragraphs join lines with a newline + `whitespace-pre-line`; mock joins answers with blank lines (mock.ts:136,639) so they become separate paragraphs; user messages keep the old `<p>` |
| 3 | yes | probes above; parser drops images to alt text and links to text unless a safe app path; renderer re-checks `internal && isSafeAppPath`; ImagePlaceholder has no `<img>` |
| 4 | yes | `markdown.test.ts` not in the diff and passes; content mode path unchanged (`parseMarkdown` without opts) |
| 5 | yes | compact headings `text-sm`; table `w-max min-w-full` inside `overflow-x-auto` |
| 6 | yes | en.ts, es.ts, i18n-es.json have `artworkStatus.purged` with the exact strings; screens use `t("artworkStatus.<status>")`; test walks `ITEM_ARTWORK_STATUSES` from installed contracts (includes `purged`) |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (8 files: assistant route, new answer component, content/markdown*, 3 i18n files)
- [x] Nothing outside scope (no backend or prompt change)
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy/idempotency/money n/a; en and es in sync in all three files
- [x] Decisions: option name and `internal` flag in the report; nothing cross-cutting

## Optional notes (not blocking)
1. The image case in markdown.ai.test.ts can't tell the AI parser branch from the old renderer (mutation survives). Add a parser-level assertion (AI blocks contain no `image` node) so a renderer change can't silently reopen it.
2. In-app answer links do full page loads (plain `<a>`), as the report says.
No servers started; scratch worktree removed; invai-web tree clean.
