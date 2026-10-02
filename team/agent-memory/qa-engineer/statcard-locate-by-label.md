---
name: statcard-locate-by-label
description: invai-ui's StatCard shows an arrow (green up by default) whenever `delta` is a truthy string, even for text like "unchanged" — a real bug to test for, and a pattern for testing one glance-grid metric's delta without controlling exact seed values.
metadata:
  type: project
---

`invai-ui/src/app/stat-card.tsx`: `deltaDirection` defaults to `"up"` whenever `delta` is passed as
a non-empty string, so `invai-web`'s `glance-grid.tsx` (which sets `delta={item.change.formatted}`
unconditionally whenever `item.change` exists) shows a green up-arrow next to literal "unchanged"
text — exactly the T-20-2 AC2 bug ("unchanged" must have no arrow, neutral color).

**How to apply:** to test one metric's delta on a card-grid page (StatCard renders `<p>label</p>`,
`<p>value</p>`, optional `<p>delta>{icon}{text}</p>` as the only direct-child `<p>`s of its `Card`
div), locate by the label text and walk up to the nearest `rounded-lg` ancestor, then index into its
`<p>` children — this reads whatever the real (seeded) delta value is, so the assertion holds
without needing to force a specific before/after pair through the pipeline:
```ts
const card = page.locator("p", { hasText: /^Margin$/ }).first()
  .locator("xpath=ancestor::div[contains(@class,'rounded-lg')][1]");
const deltaP = card.locator("p").nth(2); // 0=label, 1=value, 2=delta if present
const text = (await deltaP.innerText()).trim();
const arrows = await deltaP.locator("svg").count();
```
Assert the text shape (e.g. `/pts$|^unchanged$/i`) and, when it's the "unchanged" case, that
`arrows === 0`. See [[dev-copy-db-grants]] for the env setup this ran against.
