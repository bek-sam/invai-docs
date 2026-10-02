# T-26-5: Web "Listing photos" screen

| Field | Value |
|---|---|
| Wave | 26 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008) |
| Spec | `specs/listing-photos.md` |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | product-designer (sonnet, new screen) |
| Risk flags | ui |
| Model | sonnet |

## Read first
- `.claude/agents/web-engineer.md`; playbooks `build-dashboard-screen`, `write-plain-language-copy` (+ its `glossary.md`).
- An existing AI listing screen and its route file in `invai-web/src` (find with `grep -rn "listings" src/routes | head`), the design list/detail screen, `@invai/ui` components already used there, `src/lib/format.ts` (dates and numbers only through it).
- Contract `invai-contracts/src/contract/photos.ts`, ADR 0023; the backend from T-26-4 (`photos.*` procedures).
- `invai-docs/team/agent-brief.md`.

## Owned paths (edit)
- `invai-web/src/**` (new route and components for listing photos, nav entry), `invai-web/src/i18n/{en,es}.ts`, `invai-web/scripts/i18n-es.json` (and `scripts/i18n-extra-en.json` if you use template-literal keys). Never run `pnpm i18n`.

## Read-only paths
- `invai-web/e2e/**` (qa-engineer), every other repo, `invai-ui/**` (ask the product-designer for a missing component; build locally inside your route meanwhile).

## Depends on
- T-26-1 contract; T-26-4 router callable on the dev DB.

## Acceptance criteria
1. A "Listing photos" entry sits next to AI listings in the nav for owner, admin, office and designer (hidden for floor roles), and a design's detail page links to it with that design preselected.
2. **Step 1, pick a design**: searchable list of the shop's designs with thumbnails.
3. **Step 2, analysis** (the API may answer `pending`: show progress and poll until ready): style, audience, detected text, recommended blank colors as swatches with names, and contrast warnings in plain words ("Light art on a light shirt is hard to see. Try Black or Navy."). Sample (mock) analysis is labelled as sample.
4. **Step 3, choose**: garments (tee, hoodie, crewneck, tank), blank colors (the shop's blank colors plus recommended ones), views, channels; a live estimate "N photos, M credits" from `photos.estimate`; the generate button is disabled with the reason when credits are short.
5. **Step 4, results**: a grid grouped by channel and slot; each image shows its check result (pass, or the failure in plain words: "Background isn't pure white", "Product fills 78% (Amazon needs 85%)", "Drawn illustration: Amazon wants a photo for the main image"). Rendering shows progress and updates without a page reload (poll or the existing realtime pattern).
6. **Approve** single images or all passing ones, **reject**, then **Download zip** (link appears when ready) and **Attach to AI listing draft** (pick a draft of the same design; confirmation names the count). Unapproved images can't be downloaded or attached; the UI says why.
7. The billing credits table labels the new credit kinds: add `creditKind.photo_image` and `creditKind.photo_scene` to `src/i18n/en.ts` (~645), `es.ts` and `scripts/i18n-es.json` (~541) (plan review item 3).
8. Errors from the API map to translated messages (credits exhausted, imaging unavailable, not found); no raw codes.
9. English and Spanish complete (no raw keys, no English fallbacks in es), light and dark themes, usable at 390 px (no horizontal scroll; grid becomes one column; buttons don't wrap), keyboard reachable, images have alt text from the analysis.

## Verification
- `cd invai-web && pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 40`
- Browser: you have the `:3000` slot for this card (web dev CSP allows only API :3000, B-220). Start the API (`PORT=3000 OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm dev:api`), worker, imaging on `:8000` and web on `:5173` from the repos (not `dev:all`, which reseeds if missing; never `db:reset`). Sign in as `designer@desertbloom.test`, run steps 1–6 for a dark design on a white and a black tee plus a hoodie; screenshots at 1440 px and 390 px, en and es, one in dark mode (at most 6, look at each). Refused: `presser@` can't see the nav entry and the route shows the no-access page.
- Record PIDs; stop every process you started at the end so the gate finds :3000/:5173/:8000 free.

## Out of scope
- Lifestyle scenes and push to Shopify (wave 27). E2E specs (qa-engineer). Shared UI components (product-designer).

## Commit and report
- Commit only owned paths, message ending with the co-author line from your instructions. Don't push; only the tech lead pushes after the gate.
- Report: `invai-docs/waves/26/reports/T-26-5.md` (verify-and-report, at most 60 lines, screenshot paths, PIDs); reply in at most 8 lines.
