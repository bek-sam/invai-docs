# Review of T-21-5 (round 1)

- Reviewer: product-designer on Claude Sonnet 5
- Author: web-engineer on Claude Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show ae906ad --stat` | 52 files changed, matches report; only owned paths (`src/content/**`, `src/routes/help/**`, `src/routes/legal/**`, `src/routes/signup.tsx`, `src/components/app-frame.tsx`, `src/i18n/{en,es}.ts`, `package.json`, `scripts/sync-content.mjs`, generated `routeTree.gen.ts`) |
| Read all 4 screenshots in `invai-docs/waves/21/reports/shots/` | Looked at each at native resolution (see below) |
| `git -C invai-web show ae906ad -- src/content/public-layout.tsx src/routes/help/\$slug.tsx src/routes/legal/\$slug.tsx src/routes/signup.tsx src/i18n/en.ts src/i18n/es.ts` | Read the copy, markup and i18n keys directly |
| Checked strings against `.claude/skills/write-plain-language-copy/glossary.md` | No words-to-avoid used; shop words match (gang sheet, taller, envíos, etiqueta, ganancia, prenda) |

I did not re-run `pnpm typecheck/lint/test/build` (already re-run and reported by the author with concrete output; my scope is UX/copy/a11y, not re-proving the build). No code was edited.

## Acceptance criteria (my scope: UI/UX/copy/a11y only)
| # | Met? | Evidence |
|---|---|---|
| 2 (states, draft banner) | Yes | `legal-terms-en-1440.png`: banner reads exactly "Draft, pending legal review" with icon + warning color + text (never color alone), `role="status"`. `es.ts` `legal.draftBanner` = "Borrador, pendiente de revisión legal" — correct, natural Spanish. |
| 3 (sign-up copy/links, Help entry) | Yes | `signup-links-en-1440.png`: exact required copy "By creating an account you agree to the Terms and Privacy Policy." with two distinct working links. Spanish ("Al crear una cuenta, aceptas los Términos y la Política de Privacidad.") is grammatically correct (masculine/feminine articles kept right, as the report claims) and uses tú-form register consistent with the rest of the app. Help entry added to the existing keyboard-reachable dropdown in `app-frame.tsx` — reuses an existing accessible pattern, no new a11y surface. |
| 4 (390/1440, en/es, typography) | Yes | `help-index-es-390.png`: no truncation, no horizontal scroll, comfortable line length, category groupings readable, Spanish text fits. `help-article-en-1440.png`: measure is `max-w-2xl` (~672px), good for long-form reading; bold/lists/headings render distinctly; missing images degrade gracefully to a labeled placeholder rather than a broken `<img>`. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` above)
- [x] Nothing outside scope for a UI/UX review
- [x] Copy matches the card's exact required strings (draft banner, sign-up agreement line) in both languages
- [x] Draft banner uses icon + color + text, not color alone
- [x] Glossary words used correctly in help content (checked against `write-plain-language-copy/glossary.md`); no internal words ("tenant", "webhook", etc.) leaked into copy
- [x] No raw i18n keys or English fallbacks visible in the Spanish screenshot
- [x] Article typography readable at 1440 and 390 (measure, heading hierarchy, spacing)
- [x] Targets: sign-up's Terms/Privacy links are inline text links (WCAG 2.5.8 exempts inline links from the minimum target size) — fine. The new `LangButton` toggle (`public-layout.tsx`) is a real `<button>` with a visible focus ring, `aria-pressed`, and ~28px effective height — meets the design system's own web minimum (24×24px, per `add-ui-component` skill) though smaller than the 44px I'd prefer for a primary tap target; not blocking since it matches the existing small language-toggle pattern used elsewhere in the app and is not the page's primary action.

## Optional notes (not blocking)
1. `legal-terms-en-1440.png` shows compliance-officer's draft content rendering raw authoring placeholders (`[[OWNER: ...]]`, `[COUNSEL: ...]`) directly on a page linked from the real sign-up flow. The renderer does the right thing visually (monospace/boxed, visibly distinct from real terms), and the draft banner above it is unmissable, so this isn't a defect in what T-21-5 built — it faithfully renders the source markdown with sanitized, non-HTML output as required. But before this goes live, the tech lead/compliance-officer should decide whether sign-up should link to a draft this raw, or whether the placeholder content needs a friendlier "this section is still being finalized" treatment for anything reachable pre-launch. Not a blocker for this card.
2. Minor, cosmetic: consider bumping `LangButton` padding on the public pages to match the app's 44px guidance for primary controls if it becomes a more prominent action later (e.g., if these pages get more standalone traffic than they do today as legal/help references). No action needed now.

Nothing else to flag. The work is plain-language, bilingual, accessible, and matches the card's required copy exactly.
