---
name: add-ui-component
description: Add or change a shared React component in @invai/ui (invai-ui) for invai-web and invai-floor - Radix primitives via radix-ui, cva variants, theme tokens, accessible names and keyboard use, en/es strings, a playground entry, tests, and a consumer check in both apps. Use for "new component", "design system", "shared UI", "kit component", "variant", "theme token".
---

# Add a UI component

A kit component that both apps can use as-is: accessible, themed from tokens, translated, shown in the playground, tested, and proven to build in web and floor.

## When to use
- The product-designer (owner of `invai-ui/**`) adds or changes a component, a variant or a theme token.
- A web or floor engineer built something locally because the kit lacked it: this playbook moves it into the kit. Web and floor engineers don't edit `invai-ui` themselves; they review as consumers.

## Steps
1. **Check it doesn't exist.** Read `invai-ui/README.md` (component list) and `src/index.ts`. Prefer a new variant of an existing component over a near-duplicate.
2. **Pick the folder:** `src/components/` (base shadcn-style, e.g. `button.tsx`), `src/app/` (dashboard-level, e.g. `empty-state.tsx`, `status-badge.tsx`), `src/floor/` (tablet, e.g. `pin-pad.tsx`, `scan-result.tsx`).
3. **Build on primitives.** Interactive behavior (dialogs, menus, popovers, tabs, selects) comes from the unified `radix-ui` package, never hand-rolled focus traps. Variants with `class-variance-authority`; class merging with `cn` (`src/lib/cn.ts`). Check the installed APIs in `node_modules` first.
4. **Style only from tokens** in `src/styles/theme.css` (`--color-*`, status colors `success`/`warning`/`danger`/`info`). No raw hex values. Check light and dark (`.dark` class or `data-theme="dark"`). Changing a status color changes `Badge`, `StatusBadge`, `StatCard`, `ScanResult` and `ShipByBadge` together.
5. **Accessibility (WCAG 2.2 AA):**
   - every control has an accessible name (visible label or `aria-label`), icons are `aria-hidden`;
   - full keyboard use with a visible focus ring that is never hidden (2.4.11);
   - targets ≥ 24 × 24 px on web, ≥ 64 px for floor components (floor `Button` size is `h-20`);
   - status is never color alone: color plus icon plus text;
   - any drag interaction has a non-drag alternative (2.5.7).
6. **Strings:** a component that renders its own text uses `useTranslation()` and adds keys to `src/i18n/locales/en.json` and `es.json` with real Spanish. Text passed in by props is the app's job. Never hard-code English.
7. **Types and props:** export the component and its `Props` type from `src/index.ts`. Keep props minimal and data-agnostic; domain enums come from `@invai/contracts` (as `StatusBadge` uses `OrderItemState`). Money in cents, sizes in inches, like the rest of the platform.
8. **Playground:** add it to `playground/App.tsx` with each variant and state (loading, empty, disabled, error), then `pnpm playground` (http://localhost:5175) and look at it in light and dark.
9. **Tests** with `@testing-library/react` next to the file (`*.test.tsx`, see `src/floor/pin-pad.test.tsx`): renders with role and name, keyboard interaction, the props that change behavior.
10. **Check the kit:** `pnpm typecheck && pnpm lint && pnpm test`.
11. **Consumer check:** both apps link the kit (`link:../invai-ui`), so run in each:
    ```
    export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
    for r in invai-web invai-floor; do (cd ../$r && pnpm typecheck && pnpm build) || echo "BROKEN: $r"; done
    ```
    Tailwind v4 only generates the kit's classes because each app's `src/styles.css` has `@source "../../invai-ui/src";`.
12. **Hand-off:** tell the web and floor engineers what to replace (their local copy, if any) and ask one of them to review as the consumer.

## Rules (MUST / MUST NOT)
- MUST NOT break an existing prop or variant without a migration note to both apps in the same change.
- MUST NOT add a dependency without checking bundle size impact on the floor (initial JS ≤ 150 KB gzip, research 11 §6.1).
- MUST keep brand-neutral channel badges (no marketplace logos).
- MUST keep components free of data fetching and app state; they take props.

## Done when
- The component is exported, in the playground (light and dark, every state) and was looked at.
- Tests pass; `pnpm typecheck && pnpm lint && pnpm test` in `invai-ui`, and typecheck plus build in `invai-web` and `invai-floor`.
- en and es strings exist; a consumer engineer reviewed it.

## References
- `invai-ui/README.md`, `src/index.ts`, `src/styles/theme.css`, `playground/App.tsx`
- `invai-docs/research/12-security-quality-playbook.md` §3.7 (WCAG 2.2), §3.8 (i18n)
- `.claude/agents/web-engineer.md`, `.claude/agents/floor-engineer.md` (consumer rules)
- Related: `build-dashboard-screen`, `build-floor-flow`, `ux-audit`, `write-plain-language-copy`
