---
name: release-notes
description: Write InvAI release notes from pushed, reviewed work only - an internal changelog for the owner and a short en/es "what's new" for shops, grouped by who notices (office, floor, owner). Use after a wave is integrated and pushed, before a release (release-checklist), or when the owner asks "what changed".
---

# Release notes

The owner knows exactly what shipped and what it means for shops, and shops get a short, true "what's new" in
English and Spanish that the owner sends.

## When to use
- Wave step 8 (report to the owner), after the tech lead pushed the integrated wave to `main`.
- As part of `release-checklist` before a release to a pilot environment.
- When the growth-marketer needs launch material (they adapt the notes; they don't invent features).

## Steps
1. **Find the range.** The last notes are the newest file in `invai-docs/help/release-notes/` (created on
   first use); its header records the commit of each repo. For each of the 8 repos (`invai-backend`,
   `invai-contracts`, `invai-floor`, `invai-imaging`, `invai-infra`, `invai-ui`, `invai-web`, `invai-docs`):
   ```
   git -C <repo> log --oneline <last-hash>..origin/main
   ```
   Only what is on `origin/main` counts. Local commits and unpushed branches are left out.
2. **Map commits to cards.** Read `invai-docs/waves/<n>/wave.md`, the task cards and `waves/<n>/reviews/`.
   Include a change only if its review approved it. Note cards that were cut or failed.
3. **Sort each change** by who notices it:
   - **Office and owner** (web): Today, Orders, SKU Mapping, Gang Sheets, Shipping, Profit, Listings,
     Settings,
   - **Floor** (tablet): Pick, Press, QC, Pack, and login and pairing,
   - **Vendor** (portal): Sheet inbox, Shops,
   - **Behind the scenes:** reliability, security, performance, integrations moving from mock to real. Shops
     see these only when they change something for them.
4. **Verify each user-facing change in the running app** on the seed shop, and copy the screen and button
   names from `invai-web/src/i18n/en.ts` / `es.ts` and `invai-floor/src/i18n/*.ts`. A change you can't see in
   the app doesn't go in the shop notes.
5. **Write the internal changelog** (owner audience) with `template.md`: every card, its effect, the evidence
   (review file), known gaps, migrations or settings the owner must know about, anything that needs the owner
   (keys, deploy go-ahead).
6. **Write the shop notes**, English and Spanish:
   - lead with the change that saves the most time or prevents a wrong print or a late order,
   - 3–7 items, one or two sentences each: what's new and where to find it,
   - link a help article for anything that changes how staff work (`write-help-article`),
   - fixes named by the symptom the shop saw ("Imports from Walmart no longer skip orders with two items"),
   - floor changes in Spanish first-class; pressers may only read that part.
7. **Check the claims.** No numbers without a source (e.g. film use from `qa-report.md` or a metric file).
   Nothing about marketplaces, AI or privacy without the compliance-officer's review.
8. **Save** `invai-docs/help/release-notes/<YYYY-MM-DD>.md` (both audiences, shop notes in en and es), and
   record each repo's `origin/main` hash in the header.
9. **Queue for the owner:** the shop notes go out only through `send-owner-draft`. Tell the growth-marketer
   (when active) that new notes exist.

## Rules
- MUST include only work that is pushed to `origin/main` and approved in review.
- MUST describe what the user sees, in shop words, with names copied from the app.
- MUST give shops en and es versions with the same content.
- MUST list known gaps and anything behind a mock (for example "labels use the test carrier until EasyPost
  keys are added") in the internal changelog.
- MUST NOT promise upcoming features or dates in shop notes.
- MUST NOT mention other shops, pilots by name, or any customer data.
- MUST NOT publish or send anything. The owner sends.

## Done when
- `help/release-notes/<date>.md` has the repo hashes, the internal changelog tied to cards and reviews, and
  shop notes in en and es.
- Every shop-facing item was seen in the running app and links a help article where staff work changes.
- The shop notes are in the owner inbox as a draft.

## References
- `template.md` (this folder)
- `.claude/agents/docs-writer.md`, `invai-docs/team/operating-system.md` (wave steps 6–8)
- `invai-docs/waves/<n>/` (cards and reviews), `invai-docs/build/qa-report.md`
- Related playbooks: `release-checklist`, `write-help-article`, `send-owner-draft`, `launch-plan`
