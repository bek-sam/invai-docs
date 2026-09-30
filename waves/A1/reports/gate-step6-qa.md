# Gate step 6 root cause: golden-path.spec.ts:259 (browser) timeout

**Waiting call:** `clickIfShown(vendorPage, "Mark printed")` — `invai-web/e2e/golden-path.spec.ts:75`
(helper), called at `golden-path.spec.ts:287`. Trace shows its internal `locator.waitFor` started
at 61149ms and only errored at 355138ms (test.trace, "Wait for selector … Mark printed"), i.e. a
294s stall inside an 8s-configured wait — not a normal locator timeout.

**Evidence:** the vendor-portal screencast (trace.zip `screencast/page@2566…jpeg`) shows frames
every few seconds up to 14:20:51.690Z, then **no frame at all until 14:25:49.391Z** — a genuine
~298s renderer freeze, not CDP backpressure. The gate log shows the cause: `[web] … [vite]
(client) page reload e2e/.report/index.html` and `page reload
e2e/.results/.playwright-artifacts-0/traces/resources/…html` at 9:19:54–9:19:56 and again at
9:25:50–9:26:15 (`run-20260930T141402Z.log`). `invai-web/playwright.config.ts` sets
`outputDir: "e2e/.results"` and `reporter: [..., ["html", {outputFolder: "e2e/.report"}]]` —
both **inside** `invai-web/`, the same tree the live `:5173` Vite dev server watches
(`vite.config.ts` has no `server.watch.ignored`). While the browser suite runs against that same
dev server, Playwright's own trace/report writes are picked up by Vite's watcher and it force
full-page-reloads every connected tab (both `page` and `vendorPage`), stalling rendering and
tearing down the vendor portal's SSE/query state mid-step. Both post-failure screenshots (owner
page and vendor portal) render correctly ("Received"), confirming this is not a rendering or
state bug in the vendor portal itself.

**Why now, not in the last passing gate:** the same step already took 33.7s in
`run-20260930T045101Z.log` (vs. ~1s for neighboring steps) — the reload storm existed before too,
just under the 120s budget. This wave's much larger 18-month seed (more orders/sheets/shipments/
notifications — alerts badge shows 61, the sheet has 43 placements) makes every forced reload
slower to refetch/rehydrate, and a longer-running step accumulates more trace resource files
(more reload triggers), tipping the same pre-existing mechanism over the timeout.

**Cause layer:** test harness / environment — not backend, not the vendor-portal product code.

**Owner:** qa-engineer (own `invai-web/playwright.config.ts`), coordinate with web-engineer for
`vite.config.ts`.

**Proposed fix (not committed):** move `outputDir` and the html `reporter.outputFolder` in
`invai-web/playwright.config.ts` outside the watched tree (e.g. `../.e2e-out/invai-web/{results,report}`
or an env-driven temp dir), and/or ask web-engineer to add
`server.watch.ignored: ["**/e2e/.results/**", "**/e2e/.report/**"]` to `vite.config.ts`. Either
alone should stop the reload storm; tech lead to pick one before re-gate.

## Fix (applied, per tech lead grant)

`invai-web/playwright.config.ts` and `invai-floor/playwright.config.ts` (same pattern: html
`reporter.outputFolder` and `outputDir` both `e2e/.report` / `e2e/.results`, both repos' `:5173`
and `:5174` dev servers have no `server.watch.ignored`) now write to `../.e2e-out/invai-web/{results,report}`
and `../.e2e-out/invai-floor/{results,report}` — resolved next to each repo, not inside it, so
neither repo's Vite dev server ever sees the writes. `vite.config.ts` in both repos was not
touched. `typecheck`, `lint` and `playwright test --list` (35 tests in 5 files) all pass in
`invai-web`.

- `invai-web`: SHA `369705f`
- `invai-floor`: SHA `72a842d`

**Places that still name the old `e2e/.report` / `e2e/.results` path** (not edited — out of my
owned paths; tech lead to route to their owners):
- `invai-infra/scripts/ci/run-e2e.sh:161` — a log message only (`"...traces under
  invai-web/e2e/.results and invai-floor/e2e/.results"`), not a functional path use; still worth
  updating so it doesn't mislead whoever reads CI output.
- `invai-web/.github/workflows/e2e.yml:197-200` and `invai-floor/.github/workflows/e2e.yml:197-200`
  — artifact-upload glob paths (`invai-web/e2e/.report/**`, `invai-web/e2e/.results/**`,
  `invai-floor/e2e/.report/**`, `invai-floor/e2e/.results/**`); these now upload nothing and need
  the new `.e2e-out/` paths (platform-sre owns CI workflows).
- `invai-web/biome.json:36-37` and `invai-floor/biome.json:15` — lint-ignore entries for
  `!e2e/.report`/`!e2e/.results`; now dead (nothing there to ignore) but harmless; the new
  `.e2e-out/` dirs sit outside each repo so biome never sees them, no replacement needed unless an
  owner wants to prune the dead entries.
- `.claude/skills/run-golden-path/SKILL.md:69-74` — step 9/10 tell the reader to open
  `invai-web/e2e/.report` and look at `e2e/.results/**/trace.zip`; per the grant, skill files were
  not edited. Tech lead: the correct new paths are `invai-web/../.e2e-out/invai-web/report` (i.e.
  `invai-web-sibling/.e2e-out/invai-web/report`, or just `<workspace root>/.e2e-out/invai-web/report`)
  and `<workspace root>/.e2e-out/invai-web/results/**/trace.zip`.
- `.claude/agent-memory/qa-engineer/vite-reload-storm.md` — my own memory note on the root cause;
  left as-is (it correctly describes the bug and points at this report), no update needed since it
  doesn't assert the fix location.

Not committed by me (outside owned paths, reported above): CI workflow files, biome.json in
either repo, the `run-golden-path` skill, `run-e2e.sh`.
