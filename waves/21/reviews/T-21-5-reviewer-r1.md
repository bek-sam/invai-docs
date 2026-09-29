# Review of T-21-5 (round 1)

- Reviewer: reviewer on Claude Opus 5.5
- Author: web-engineer on Claude Opus 5.5 (per report; card Model says sonnet. Risk flag is `ui` only, so no cross-model rule applies)
- Verdict: **approve**

Scope reviewed: `invai-web` commit `ae906ad` (the only commit in `d092a4b..ae906ad`), plus the card, the architect plan note and the report. Other agents' uncommitted `e2e/digest-dates.spec.ts` and `dist-qa3190/` were left alone.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (invai-web, Node v24.21.0) | exit 0, no output |
| `pnpm lint` | `Checked 176 files … Found 1 warning.` exit 0. The warning is `src/content/markdown.test.ts:106` (optional-chain suggestion), a file this commit adds. The report calls it "pre-existing, unrelated", which is wrong, but it is a warning only |
| `pnpm test` | `Test Files 19 passed (19)`, `Tests 117 passed (117)` |
| `VITE_API_URL=http://localhost:3000 pnpm build` | `✓ built in 1.35s` (only the existing >500 kB chunk warning); `dist/` removed afterwards |
| `pnpm check:content` against the real sibling `invai-docs` | exit 0 (committed copies match the source) |
| Drift check in a scratch copy of both trees (scratchpad, deleted afterwards): appended to `help/es/receiving.md`, added `legal/new.md`, deleted `src/content/help/en/sku-mapping.md`, then `--check` | exit 1, with three messages: `help/en/sku-mapping.md … missing from src/content`, `help/es/receiving.md differs … run pnpm sync:content`, `legal/en/new.md … missing`. After `sync:content`, `--check` gives exit 0. With `invai-docs` moved away, `--check` prints "isn't checked out … skipping" and exits 0 (the skip-with-message the card asks for) |
| Scratch renderer test (`src/content/zz-review-scratch.test.ts`, deleted straight after; `git status` clean of it). It fed `<script>`, `<img onerror>`, `<iframe>`, `<svg onload>` in a table cell, `**<b>…</b>**`, and links with `javascript:`, `JAVASCRIPT:`, `data:`, `vbscript:` and `https:` through `parseMarkdown` → `MarkdownBlocks` → `renderToStaticMarkup` | Every tag came out as escaped text (`&lt;script&gt;…`, `&lt;iframe …`). There are no raw elements. `javascript:` hrefs were rewritten by React 19.3 to `javascript:throw new Error('React has blocked a javascript: URL…')`. `data:` and `vbscript:` hrefs pass through unchanged (see note 1) |
| `curl -sI http://localhost:4431/legal/terms` on my own `vite preview` (build with `VITE_API_URL=http://localhost:3999`, where nothing listens, so any API call would show up as a failed request) | `200`, CSP `default-src 'self'; script-src 'self'; … object-src 'none'; base-uri 'none'; frame-ancestors 'none'`. That is the wave-12 policy. The commit touches no file in `vite.config.ts`, `src/lib/build/**` or `public/` |
| Playwright pass (scratch script, headless Chromium), en and es × 390 and 1440 px, over `/help`, `/help/getting-started`, `/help/receiving`, `/legal/terms`, `/legal/privacy`, `/legal/dpa`, `/help/nope`, `/legal/nope`, `/help/../legal/terms` | No console errors or warnings, page errors, failed requests or requests to any origin other than the preview origin on any of the 36 loads. So the public routes call no API. Draft banner count is 1 on every legal page in the right language ("Draft, pending legal review" / "Borrador, pendiente de revisión legal") and 0 on help pages. Unknown slugs render `NotFoundState`. The index's first link navigates client-side to `/help/getting-started`. The page overflows sideways at 390 on `/legal/privacy` and `/legal/dpa` only (note 2) |
| Same pass on `/signup` at 1440 in en and es | Terms and privacy links exist (`href=/legal/terms`, `/legal/privacy`, `target=_blank`). Text is "By creating an account you agree to the Terms and Privacy Policy." and "Al crear una cuenta, aceptas los Términos y la Política de Privacidad." I looked at the es screenshot: the line wraps cleanly above the button |
| `scan-test-weakening.sh invai-web d092a4b` | `removed=0 added=28 … Result: no hits` |
| `git diff --stat d092a4b ae906ad` | 52 files, +3492/−1, all inside owned globs (see Checks) |
| Cleanup | Killed my `vite preview` (PID 31324, :4431); `lsof` shows nothing listening. `dist/` and scratch files removed. No API, DB or Redis used |

Author screenshots I looked at: `legal-terms-en-1440.png` and `help-article-en-1440.png`. I also took and looked at my own `signup-es` 1440 and `privacy-390` overflow shots.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `sync:content` and `check:content` behave as specified. The drift, re-sync and no-sibling runs are in the table above. The committed copies match `invai-docs` today. `loader.test.ts` asserts `listHelpArticleSlugs("es")` equals the en list and that every en slug and every `LEGAL_SLUGS` entry parses in both languages. It is new with the loader, so it can't pass on base, and the author showed it fail on a removed es file. Wiring it into web CI is platform-sre's follow-up, as the architect's A1 note says |
| 2 | Yes | All four routes render in the app language (live pass above). The renderer builds React elements from typed nodes only, with no `dangerouslySetInnerHTML` anywhere in the diff. My adversarial scratch test shows raw HTML is emitted as escaped text. CSP is unchanged and served as `script-src 'self'`. The draft banner shows on every legal page in en and es |
| 3 | Yes | The sign-up agreement line and links work in en and es (live). The Help entry is a `DropdownMenuItem asChild` → `<Link to="/help">` (`src/components/app-frame.tsx:318-323`), built exactly like the existing "Account and security" item next to it. That is a Radix menuitem reached by Tab to the user-menu trigger, then Enter or Space, then the arrow keys. I verified this by reading the code, not by driving it live: a signed-in shell needs an API on its own Redis DB, and my check for a free Redis DB was refused by the sandbox. The public header's language buttons are Tab-reachable (focus lands on "English" after two Tabs) |
| 4 | Partly (not blocking this author) | I saw 390 and 1440, en and es, with no console errors on every new route (36 loads). "Screens smoke passes with the new routes" was not run, and `/help` and `/legal/*` are not in `e2e/screens.smoke.spec.ts`. The card doesn't give the owner `e2e/**`, and the QA gate owns that suite. **Tech lead: add these routes to the QA gate's smoke run or give qa-engineer a follow-up.** The substance of the check passed in my pass |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed. The commit touches `package.json` (two script lines: `sync:content`, plus `check:content`, which AC1 requires), `scripts/sync-content.mjs`, `src/content/**`, `src/routes/help/**`, `src/routes/legal/**`, `src/routes/signup.tsx` (the agreement line only), `src/components/app-frame.tsx` (the Help entry only, +7 lines), `src/i18n/{en,es}.ts` (9 keys each) and `src/routeTree.gen.ts` (generated by the router plugin)
- [x] Nothing outside scope. `/legal/dpa` and `/legal/subprocessors` come along from the same content and the same fixed slug list, so they add no new surface
- [x] Tests exercise the behavior, and none were weakened (scan: no hits; only new tests)
- [x] Tenancy, idempotency and money: not applicable (static public pages, no API). en/es: every new key exists in both catalogs, and the Spanish is natural (gender agreement "los Términos … la Política" is right)
- [x] Decisions recorded where needed. The hand-rolled renderer (no new dependency) and the public routes outside `/_app` are in the report's Decisions. Neither is cross-cutting

## Optional notes (not blocking)
1. `src/content/markdown-view.tsx:184`: external links pass any scheme to `href`. `javascript:` is only neutralised by React 19's built-in blocking and the `script-src 'self'` CSP, and `data:`/`vbscript:` pass through. The content is first-party (`invai-docs`), so there's no exploit today. A one-line allowlist (`^(https?:|mailto:|/|#)`, otherwise render as text) would make "disallow" hold in the renderer itself, as the architect's note suggested.
2. `src/content/markdown-view.tsx:166`: inline `code` doesn't wrap. On `/legal/privacy` (scrollWidth 417) and `/legal/dpa` (437) at 390 px, the span `invai-backend/src/integrations/channels/shopify/common.ts:265-267` makes the whole page scroll sideways. Adding `break-words` or `[overflow-wrap:anywhere]` fixes it. (Content note for compliance-officer: the public legal drafts cite internal source paths.)
3. `src/content/markdown-view.tsx:65`: `li` is `flex flex-col`, which drops `display: list-item`, so the bullets and **step numbers** disappear. The help articles' numbered "Fix it" steps show without numbers (visible in `help-article-en-1440.png`), and so do the Terms bullets. Wrapping the item's children in an inner `div` keeps the markers. This is for the product-designer co-review.
4. `src/content/markdown-view.tsx:27`: markdown `#` renders as `h2`, and `/help` doesn't drop its first heading, so the help index page has no `h1` (the article and legal pages do).
5. The 9 hand-added Spanish keys aren't in `scripts/i18n-es.json`. If anyone runs `pnpm i18n` again, they will fall back to English. The agent brief forbids that run, so this is only a footnote.
6. The report calls the lint warning "pre-existing, unrelated file", but `markdown.test.ts` is new in this commit.
