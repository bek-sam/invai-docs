# Review of T-5-3 (round 1) — product-designer co-review

- Reviewer: product-designer on Sonnet 5
- Author: backend-foundation + web-engineer on Opus 5.5
- Verdict: approve

Scope: the checklist, demo entry points/banner/reset confirm, Today's stat links and hints, and
en/es copy and layout. Code quality and tenancy are the primary reviewer's and security-reviewer's
files.

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `invai-web/src/features/onboarding/checklist.tsx`, `steps.ts`, `demo/demo-banner.tsx`, `demo/menu-items.tsx`, `demo/try-demo-button.tsx`, `routes/_app/index.tsx` | see notes below |
| Screenshots viewed: `1-new-shop-checklist-en.png`, `2-demo-today-en.png`, `4-reset-confirm-es.png` (own selection of 3, per token budget) | see per-screen notes |
| `invai-web-t53-review` @ `3da9a73`: `vitest run src/features/onboarding src/features/demo` (part of the full suite re-run) | 3 files (`is-own-demo.test.ts`, `steps.test.ts`, plus checklist covered indirectly), all passing |
| `git diff a2566b2 3da9a73 -- src/i18n/en.ts src/i18n/es.ts` | 49/49 additions, 0 deletions each — 1:1 key parity |

## Per-screen notes

**Screenshot 1 (new shop, empty checklist, en).** 0 of 11, all steps open, three-column grid on
desktop, clear iconography (open circle vs. check). The "Try with sample data" callout only shows
below the checklist when the workspace is empty (`isEmptyWorkspace`: no channel, no blanks, no
designs) and not while already in a demo (`!isDemo` guard in `checklist.tsx`) — correct, avoids
offering the demo from inside the demo. Copy is honest about the tradeoff ("Your shop stays as it
is").

**Screenshot 2 (demo Today, en).** The banner reads clearly as a persistent, non-dismissible-except-by-action
strip (`role="status"`, an amber/info tone, a flask icon) distinct from the blue email-verification
banner above it — good visual hierarchy, no confusion about which banner does what. 8/11 done is
legible at a glance with the progress bar. Stat cards (Due today 7, Overdue 8, etc.) read as real
numbers, not zero-state placeholders — the sample data reads as a populated shop, which is the
point of a "look around first" flow.

**Screenshot 4 (reset confirm, es).** Modal copy is direct and loss-aware ("Se borra todo lo que
cambiaste aquí… Tu tienda real no cambia"), destructive-styled confirm button (red), a plain
Cancel next to it. Meets the bar of "irreversible action gets an explicit, specific confirm" — it
doesn't just say "Are you sure?", it says what's lost and what's safe. `demo.reset` on the banner
requires this dialog; `demo.leave` doesn't (correct — leaving isn't destructive, it's kept for next
time).

## Accessibility
- Checklist items: `min-h-9` (36px) touch target — clears WCAG 2.1 AA's 24×24 CSS px minimum
  (2.5.8) comfortably; below the 44px "enhanced" recommendation but consistent with the rest of
  the app's list-row sizing (not a T-5-3-specific regression).
- Each checklist row carries an `sr-only` "Done"/"Not done yet" status in addition to the icon and
  the strikethrough — screen-reader users get the state without relying on color or a
  visually-struck-through label alone. Good.
- Demo banner: `role="status"` announces it politely when it mounts (e.g., right after `start`),
  which matters here because the page navigates via `router.invalidate()` + `navigate({to:"/"})`
  after the mutation — a screen-reader user needs to be told they're now somewhere new.
- Dismiss (`X`) button has `aria-label="Hide checklist"` — icon-only button, correctly labeled.
- Reset confirm dialog uses the existing `ConfirmDialog` component with a `destructive` prop —
  consistent with the rest of the app's destructive-action pattern (matches T-5-1's void-confirm
  dialog reviewed last round), not a bespoke one-off.
- I did not personally re-run a contrast checker or a keyboard-only pass this round (screenshots
  and code review only, per the token budget); nothing in the component code suggests a
  keyboard trap (all interactive elements are `Button`/`DropdownMenuItem`/`AnyLink`, no custom
  `onClick`-only `div`s).

## Copy and i18n
- 41 new keys, all present in both `en.ts` and `es.ts` (confirmed by diff, no deletions). Spot
  read: `demo.bannerBody`, `demo.resetBody`, `onboarding.progress` all read as plain, second-person,
  jargon-free language, matching the house style elsewhere.
- Alert headlines are now translated from `alert.kind` (`alertKindLabel`, a switch with no
  `default`, so a new `Alert["kind"]` the backend adds later will fail typecheck here rather than
  silently rendering blank — good defensive design for a cross-repo contract dependency). The
  detail line stays English-only outside `en`, cleanly hidden rather than shown half-translated
  (`alertDetail`'s `language.startsWith("en")` gate) — the report's disclosed known gap
  (`Alert.data` needed for full translation) is the right shape for a follow-up, not something
  this card needed to solve.

## Ruling on question 5 (slug-based own-demo detection)
`isOwnDemo` (`invai-web/src/features/demo/is-own-demo.ts`) checks `org.demo && org.slug ===
"demo-" + org.id`. From a **design/UX robustness** standpoint (the security angle is
security-reviewer's, and correctly finds no exploit path here since the backend enforces the real
boundary independently): this is fragile in the sense that it's an implicit contract between two
repos with no explicit field — if the backend's slug format ever changes (say, a future
human-readable demo company name influences the slug), the web's banner would silently stop
appearing on someone's own demo, or (less likely, since the format is `demo-<uuid>` and uuids
aren't guessable) never trigger falsely. The blast radius of getting this wrong is purely
cosmetic: wrong banner visibility, not wrong data. `is-own-demo.test.ts` pins the exact convention
with a real assertion (`demo=true, slug="demo-c1"` → true; `demo=true, slug="desert-bloom-tees"` →
false), which at least means a change to the convention breaks a test immediately rather than
shipping silently. **Not blocking**, but I agree with the report's own follow-up: this should
become an explicit `Org.demoOwned` boolean on the contract (architect) rather than a slug
convention two repos have to agree on by reading each other's source.

## Blocking findings
None.

## Checks
- [x] Only owned web paths changed — `routes/_app/index.tsx`, `features/demo/**`,
  `features/onboarding/**`, the demo entry in `app-frame.tsx`, own i18n keys.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior — `is-own-demo.test.ts` and `steps.test.ts` are real, unmocked
  assertions on pure functions; no weakened tests found in this card's own range.
- [x] en/es parity, layout at 390px (screenshot 6 in the report, not independently re-shot this
  round — code review of the responsive classes, `sm:`/`lg:` grid breakpoints on the checklist and
  `flex-col sm:flex-row` on the banner, is consistent with no-horizontal-scroll at phone width).
- [x] Decisions recorded — slug convention and its known-gap follow-up documented in the report.

## Optional notes (not blocking)
- The checklist's `AnyLink` rows navigate away from Today entirely to fix a step (e.g. "Add your
  ship-from address" → `/settings/shipping`); there's no inline "mark as done and stay" shortcut.
  That's consistent with "each step links to where it's done" as the card asked, not a gap.
- `DemoMenuItems`' "Show setup checklist" entry only appears when `me.onboarding?.dismissed` is
  true, and is gated ahead of the demo start/leave entries in the menu — good ordering (the most
  likely action, resuming setup, sits above the less common demo entry).
