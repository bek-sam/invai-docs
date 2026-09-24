---
name: ux-audit
description: Audit a running InvAI flow (web dashboard, vendor portal or floor tablet) with screenshots at 1440, 390 and 1280×800 in English and Spanish, light and dark, and write ranked findings that become task cards. Use for "UX review", "audit this screen", before pilots, or after a UI wave lands.
---

# UX audit

A flow is walked for real as the role that uses it, and every problem is a ranked, screenshotted finding
someone can build from.

## When to use
- After a wave that changed any screen (the designer co-reviews every UI task).
- Before a pilot onboarding, on the screens that pilot's staff will use first.
- When customer-success logs a "staff time" or "annoyance" ticket about a screen.
- On request: "is this screen any good?"

## Steps
1. **Pick the flow and the role.** One flow per audit, for example "office clears needs-mapping orders" or
   "presser presses a personalized shirt". Use the demo guide steps (`invai-docs/build/demo-guide.md`) as the
   script. Roles: `owner`, `office`, `designer` on the web; `presser`, `packer`, `receiver` on the floor;
   `vendor` on the portal.
2. **Check the app is up; don't restart shared processes.** `curl -s localhost:3000/health` and `curl -sI localhost:5173`. If they're down and no one else is running, start with `cd invai-infra && pnpm dev:all`
   and stop it when done. Never `db:reset` a shared DB.
3. **Screenshot the web screens** with the helper in this folder (it signs in, sets the language, and shoots
   all three viewports):
   ```
   export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
   cd invai-web
   OUT=../invai-docs/design/audits/<date>-<flow>/shots
   node ../.claude/skills/ux-audit/shoot.mjs $OUT office@desertbloom.test en /orders "/orders?view=needs_mapping" /catalog/sku-mapping
   node ../.claude/skills/ux-audit/shoot.mjs $OUT office@desertbloom.test es /orders "/orders?view=needs_mapping" /catalog/sku-mapping
   THEME=dark node ../.claude/skills/ux-audit/shoot.mjs $OUT office@desertbloom.test en /orders
   ```
   Route names come from `invai-web/src/lib/nav.ts`; the full list is in
   `invai-web/e2e/screens.smoke.spec.ts`. The script also prints console errors and 5xx responses; copy them
   into the findings.
4. **Walk the floor on a tablet viewport (1280×800).** Pair with `stationToken` from
   `invai-backend/seed-output.json` on http://localhost:5174, log in with a PIN (1111–1188, for example
   presser `1155`), and use `?dev=1` for simulated scans. Drive it with Playwright (see
   `invai-floor/e2e/press.spec.ts` for the pairing steps) or the claude-in-chrome skill. Capture: PRESS
   (green), BLOCKED (red) with Expected vs Scanned, QC fail reason picker, pack progress, and the offline
   state.
5. **Look at every screenshot** (Read the PNG). Don't write a finding from the code alone.
6. **Check against the list** in `checklist.md`: blocking states, urgency, bulk speed, plain language in both
   languages, states (loading, empty, error, partial), accessibility, touch targets, and phone width for Today
   and Orders.
7. **Rank each finding** by severity, using the same scale as support tickets:
   - S1 **blocks shipping** or lets a wrong print through,
   - S2 **wrong print risk** or wrong data shown,
   - S3 **staff time** (extra clicks, slow bulk work, confusing step),
   - S4 **annoyance** or cosmetic.
   Then order by segment reach (does it hurt a small shop's owner doing everything, or 20 floor staff?).
8. **Write the audit** at `invai-docs/design/audits/<date>-<flow>.md`: flow, role, build (`git -C invai-web log -1 --oneline`), then one row per finding: id, screen, screenshot link, what's wrong, who it hurts,
   severity, proposed change (with en/es copy if copy changes), owner repo.
9. **Turn findings into work.** You own `invai-ui` and `invai-docs/design/**` only:
   - a missing or broken shared component: fix it in `invai-ui` yourself (`add-ui-component`),
   - anything in `invai-web` or `invai-floor`: propose a task card to the tech lead with the finding ids, and
     a spec if it's a new screen,
   - S1 findings: tell the tech lead the same day; they go into the next wave as bugs.
10. **Re-audit after the fix lands:** shoot the same routes, and add before and after pairs to the audit file.

## Rules
- MUST audit the running app as the real role, in English **and** Spanish. Floor staff often read Spanish, so
  untranslated floor text is at least S3.
- MUST treat any floor screen that allows pressing past a mismatch as S1.
- MUST keep every screenshot free of real shop or buyer data. Use the seed shop only.
- MUST NOT edit `invai-web` or `invai-floor`. Findings there become cards.
- MUST NOT show pilot staff the audit or ask them to test. Sessions with real users go through
  `usability-test-plan` and the owner.

## Done when
- `invai-docs/design/audits/<date>-<flow>.md` exists, with screenshots at 1440, 390 and 1280×800 (floor:
  1280×800) in en and es, and dark mode for at least the main screen.
- Every finding has a severity, a screenshot and a proposed change.
- S1 and S2 findings have a proposed card or an `invai-ui` fix. Console errors found are listed.

## References
- `shoot.mjs`, `checklist.md` (this folder)
- `.claude/agents/product-designer.md` (users and principles)
- `invai-docs/build/demo-guide.md` (the flows), `invai-docs/research/01-shop-workflow.md`
- Related playbooks: `usability-test-plan`, `add-ui-component`, `build-dashboard-screen`, `build-floor-flow`,
  `write-plain-language-copy`
