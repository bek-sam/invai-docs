---
name: project_t21_5_help_legal_pages
description: T-21-5 in-app Help/legal pages — browser-tool fallback and a markdown-title duplication gotcha
metadata:
  type: project
---

2026-09-29 T-21-5 (in-app Help and legal pages, B-98 web half): resumed a stalled session that had
already built `src/content/**` (hand-rolled Markdown parser/renderer, `loader.ts`, `sync-content.mjs`)
but no routes, nav entry, sign-up links, i18n keys, or the AC1 en/es-parity unit test. Finished those.

**Why:** two things worth remembering for future screenshot/verification passes:
1. `mcp__claude-in-chrome__tabs_context_mcp` blocks on a browser-picker question when multiple Chrome
   extensions are connected, and a subagent has no way to answer it (no AskUserQuestion tool, no
   human in the loop). Don't get stuck here — `@playwright/test`'s bundled Chromium
   (`import { chromium } from "@playwright/test"`) is already a devDependency in `invai-web`; drive
   it directly with a throwaway script for build-and-screenshot verification instead.
2. Help/legal markdown files carry `title` in frontmatter that duplicates the body's own leading
   `# Heading` (docs-writer's and compliance-officer's convention). If a route renders both
   `article.title` as an `<h1>` and the full `article.blocks` via the markdown renderer, the title
   shows twice. Drop `blocks[0]` before rendering when it's a heading block.

**How to apply:** reuse both on the next content-rendering or public-page card; the browser-tool
fallback applies to any subagent screenshot task, not just this one.
