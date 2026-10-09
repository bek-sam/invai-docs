# T-29-3 security review, round 1
Reviewer: security-reviewer (Opus 5.5). Author: web-engineer (sonnet). Commit: invai-web 8d134d7.
Verdict: **approve** (no blocking findings; no new S-id logged)

Threat model: model output echoes attacker-controlled order text (prompt injection). Caller: any signed-in staff viewing the assistant. Worst outcome sought: data exfiltration via a rendered request, or a click that changes state or leaves the app.

## Evidence I re-ran
- `pnpm vitest run src/content --reporter=dot` -> 3 files, 22 tests passed.
- Scratch probe (deleted; invai-web `git status` clean) fed 22 hostile answers to `parseMarkdown(s,{source:"ai"})` and asserted no `image` node and no link outside a single-slash path: images (inline, alone, in table cell, list, blockquote, bold, nested in a link `[![a](https://e/i.png)](/orders)`), reference-style `![x][1]` / `[x][1]` + `[1]: http://`, autolink `<http://e>`, bare URL, raw `<img onerror>`, entities (`&lt;img&gt;`, `&#60;`), `[x](//e)`, `[x](/\e)`, `javascript:`, titled `(/x "t")`, U+2028 in path. 22/22 passed; zero image nodes; only `/x`, `/%0d%0a//e.com`, `/login?redirect=..` survive as links (same-origin paths).
- Reference-style links and autolinks have no parse rule, so they render as literal text; entities stay literal (React escapes; no `dangerouslySetInnerHTML` in the diff).

## Findings
- Image/exfil: the parser drops images in AI mode (inline and image-only paths); no other rendered element makes a request (`<a>` has no prefetch, no CSS url()). OK.
- CSP is NOT a backstop: prod `img-src 'self' data: blob: https:` (vite.config.ts:56, nginx.conf.template:17) allows any https image, so the parser drop is the sole control. The primary review noted the "no image" test passes even without the drop; keep that as a follow-up for the owner. Low hardening, optional: narrow prod `img-src` to the S3/API origin like the dev CSP (vite.config.ts:31). Owners web-engineer / platform-sre; not blocking.
- In-app links: the SPA has no `redirect=`/`returnTo` consumer and no `/logout` route (grep of routes and lib). State-changing public routes need a secret token (`/unsubscribe` POSTs to `/l/:token`; `verify-email` fires on a token) that the attacker cannot know. Links are plain same-origin `<a>` (full navigation), no `target=_blank`. Residual: a misleading link label can send a user to a real in-app page; low, no state change on GET.
- Tables: cell content goes through the same inline filter. OK.

## Clocks
No new finding, no fix clock started. Open items: none (optional img-src hardening above).
