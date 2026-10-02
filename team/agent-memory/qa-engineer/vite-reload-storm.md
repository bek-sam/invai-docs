---
name: vite-reload-storm
description: golden-path.spec.ts step 6 (vendor portal) timed out because Vite's dev server reloads the browser tab mid-test
metadata:
  type: project
---

`invai-web/playwright.config.ts` writes `outputDir: "e2e/.results"` and the html
`reporter.outputFolder: "e2e/.report"` inside `invai-web/`, which the live `:5173` Vite dev
server watches with no `server.watch.ignored`. While `pnpm e2e` runs against that same dev
server, Playwright's own trace/report writes trigger Vite full-page reloads on the open test
tabs (`[web] [vite] (client) page reload e2e/.report/...` in the gate log), stalling rendering.

**Why:** wave A1 gate (`run-20260930T141402Z.log`), step 6 timed out at 120s; screencast frames
in the failure trace.zip show a genuine ~298s renderer freeze coinciding exactly with those
reload log lines. The same step took 33.7s (not failing) in the prior gate
(`run-20260930T045101Z.log`) — the mechanism is pre-existing, just marginal; A1's much bigger
18-month seed makes every forced reload slower to rehydrate, tipping it over the timeout.

**How to apply:** before blaming a golden-path browser step's timeout on product code, check the
gate log for `[vite] (client) page reload` lines around the hang and check trace.zip's
`screencast/` frame timestamps for a real gap (not just a slow locator). If found, it's a
test-harness issue (`outputDir`/report path colliding with the watched dev tree), not a product
bug — fix is to move Playwright's output outside `invai-web/` or add `server.watch.ignored` in
`vite.config.ts` (needs web-engineer), not to weaken the test or investigate the vendor portal.
See [[gate-traps]] for other gate-run pitfalls.

**Fixed (2026-09-30, `invai-web` SHA `369705f`, `invai-floor` SHA `72a842d`):** both
`playwright.config.ts` now write to `../.e2e-out/<repo>/{results,report}` (sibling of the repo,
never watched). `invai-floor` had the identical pattern (`:5174` dev server, no
`server.watch.ignored` either) and got the same fix. `vite.config.ts` in neither repo was
touched. Stale references to the old `e2e/.report`/`e2e/.results` paths remain in
`invai-infra/scripts/ci/run-e2e.sh`, both repos' `.github/workflows/e2e.yml` and `biome.json`, and
`run-golden-path` SKILL.md steps 9-10 — see the "Fix" section of
`invai-docs/waves/A1/reports/gate-step6-qa.md` for the full list; none of those were mine to edit.
