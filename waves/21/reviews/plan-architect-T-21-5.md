# T-21-5 plan review — architect

**Verdict: approve with changes**

## Checked
- Content-bundling approach: `pnpm sync:content` copies `invai-docs/help/{en,es}/*.md` (docs-writer,
  T-21-4) and `invai-docs/legal/**` (compliance-officer, T-21-1) into `invai-web/src/content/**`,
  committed so the web builds alone. Reasonable for a static SPA with no CMS.
- Markdown rendering safety: AC2 already requires "no raw HTML from markdown: sanitize or disallow"
  and that the wave-12 CSP stays as set. Checked `invai-web/vite.config.ts` — the production CSP is
  `script-src 'self'` with no `unsafe-inline`/`unsafe-eval` (`src/lib/build/csp.ts`,
  `src/lib/build/csp.test.ts`, T-12-5). That already blocks inline `<script>` and inline event
  handlers (`onerror=`) even if a markdown-to-HTML path slipped one through, so the card's explicit
  "sanitize or disallow" requirement is real defense in depth, not redundant. No CSP change is
  implied or needed by this card.
- `invai-web/package.json` has no markdown library today, so this card adds one. Not a blocker: a
  static (non-CDN) markdown renderer bundled at build time fits the CSP as-is. Note in the report
  which library was chosen and confirm it needs no `unsafe-eval` (some syntax-highlighters do).

## Required changes
1. **No mechanism keeps `src/content/**` from going stale.** AC1's unit test only checks en/es slug
   parity *within* `src/content`; nothing checks `src/content` against the `invai-docs/help` and
   `invai-docs/legal` sources it was copied from. Once T-21-1/T-21-4 land, docs-writer and
   compliance-officer can keep editing their markdown after this card ships, with no signal to
   web-engineer that `pnpm sync:content` needs a re-run and a re-commit — the live help/legal pages
   silently diverge from the source of truth (the same drift risk `add-contract-procedure` prevents
   for the API). Add one of: a checksum/mtime comparison the sync script itself can assert in CI
   (`invai-web/.github/workflows/ci.yml`, out of this card's owned paths — note it as a follow-up
   for platform-sre if the check needs to live there), or at minimum a `runbook.md`/README line
   (docs-writer's or web-engineer's) naming who re-runs `sync:content` when help/legal content
   changes, plus a `pnpm sync:content --check` mode that fails when the copies differ from the
   source. State the chosen approach in the report; a wave 25 CI card (T-25-2/T-25-1) can enforce it
   once it exists.

## Notes (non-blocking)
- Confirm the chosen markdown library renders only known-safe constructs (no raw HTML pass-through
  by default is the simplest correct choice, e.g. a renderer without a raw-HTML plugin enabled)
  rather than rendering + sanitizing after the fact — fewer places to get wrong.
