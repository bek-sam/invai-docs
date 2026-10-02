# T-27-5: Web: lifestyle scenes, AI and drawn badges, disclosures, push to Shopify

| Field | Value |
|---|---|
| Wave | 27 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008, phase B) |
| Spec | `specs/listing-photos.md` |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (additions to the wave 26 screen; product-designer reviewed the screen in wave 26) |
| Risk flags | ui |
| Model | sonnet |

## Owned paths (edit)
- `invai-web/src/**` (the listing photos route and its components), `src/i18n/{en,es}.ts`, `scripts/i18n-es.json` (+ `i18n-extra-en.json` if needed). Never run `pnpm i18n`.

## Acceptance criteria
1. Step 3 gains "Lifestyle scenes" (count 0–6, scene suggestions from the analysis to pick from); the estimate shows the extra credits; when the provider is the sample one, a note says "Sample scenes: real photo generation isn't turned on for this shop."
2. Cap and credit refusals show plain messages (daily photo limit reached, try tomorrow; not enough credits; the platform limit is reached, try later) in en and es.
3. Each image shows badges: "AI-generated" (ai_scene), "AI person" (synthetic performer), "Drawn illustration" (drawn templates), and the design-lock result; failed drift images show "We couldn't keep your design exact in this scene, so it was discarded. No credits charged."
4. Attaching AI images to a draft shows a confirmation that Etsy's AI disclosure will be set, and Amazon images with an AI person carry the required tag.
5. "Push to Shopify": choose a Shopify connection and product (per the contract's `productRef`), push approved images, see per-image results; a second push shows them as already there. Hidden when the shop has no Shopify connection.
6. en/es complete, light/dark, 390 px, keyboard reachable.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 40`; browser on the `:3000/:5173/:8000` slot as in T-26-5 (designer@, keys blanked, provider unset); at most 6 screenshots (en/es, 390 px, dark), look at each. Stop everything you started.

## Commit and report
- Commit own paths, co-author line; don't push. Report `invai-docs/waves/27/reports/T-27-5.md` (≤ 60 lines); reply ≤ 8 lines.
