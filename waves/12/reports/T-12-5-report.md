# T-12-5 report: CSP and security headers; SVG not served inline

Status: **done, not pushed.** Round 1 SHAs: `invai-web` `5896ba5`, `invai-floor` `c7c171b`,
`invai-backend` `7411508`. Round 2 (review r1 fix) SHAs: `invai-web` `d6c35ab`, `invai-floor`
`b9ef73a` (backend untouched this round). Workspace moved mid-task from
`~/Desktop/projects/invai` to `~/invai` (tech lead notice); all edits and verification below are
from the final location. No AWS dependency introduced or assumed anywhere in this card.

## Round 2: review r1 fix (connect-src was too broad)

`invai-docs/waves/12/reviews/T-12-5-reviewer-r1.md` blocked on `prodCsp`'s (and `nginx.conf`'s)
`connect-src 'self' https:` -- any HTTPS host, not just the API, which would let a stored-XSS bug
elsewhere exfiltrate freely. Fix, in both `invai-web` and `invai-floor`:

- New `src/lib/build/csp.ts` (unit-tested, `src/lib/build/csp.test.ts`, 4 tests each repo):
  `requireApiOrigin(raw)` derives the origin from `VITE_API_URL` -- the same env var the app
  itself reads (`src/lib/env.ts` / `src/lib/config.ts`) -- and **throws** if it's `undefined`
  (never set); an explicit `""` (same-origin deployment) is valid, not an error.
  `connectSrc(origin)` builds `'self'` or `'self' <origin>`. SSE needs no separate entry: both
  apps' realtime clients hit `${API_URL}${REALTIME_SSE_PATH}` (fetch-based in floor, `EventSource`
  in web), same origin as RPC, and both are governed by `connect-src`.
- `vite.config.ts` is now a function-form `defineConfig(({ command, isPreview }) => ...)`:
  `prodCsp` is computed per-invocation, calling `requireApiOrigin(process.env.VITE_API_URL)` for
  `build`/`preview` (the two commands that actually serve/produce `prodCsp`) -- a build without
  `VITE_API_URL` set now fails immediately with a clear error instead of silently falling back to
  a broad CSP. `devCsp` (plain `vite`/`pnpm dev`) is unaffected.
- `nginx.conf` is now `nginx.conf.template` (checked in) plus a gitignored generated
  `nginx.conf`: `scripts/render-nginx-conf.ts` substitutes the same derived `connectSrc(...)`
  into the template's `__CONNECT_SRC__` placeholder. `Dockerfile`'s build stage runs it right
  after `pnpm build` (same stage, same `VITE_API_URL` already set there) and the final stage now
  `COPY --from=build`s the generated file instead of a static one from the host tree.

Verified per repo: `node scripts/render-nginx-conf.ts` (and `pnpm build`) exits 1 with a clear
message when `VITE_API_URL` is unset, and succeeds when it's set; `vite preview` serves
`connect-src 'self' http://localhost:3000` (confirmed by curl); `nginx -t` against the rendered
`nginx.conf` plus a live `nginx:alpine` container curl, same result; `dist/index.html` still has
no inline `<script>`/`onclick=`; the new `csp.test.ts` (4/4) and each repo's full `pnpm test`
pass (web: 82/82, one pre-existing unrelated flake in `stations/receiving/logic.test.ts` on a
background rerun -- a 5s test timeout, nothing this change touches; floor: full suite green).
`tsc --noEmit` and `biome check` clean in both repos. `git status` confirmed only my files were
staged in each commit (web had unrelated concurrent edits to
`src/features/demo/is-own-demo.{ts,test.ts}` in the tree from another agent, left untouched).

## Acceptance criteria and their tests

1. **Strict CSP, no `'unsafe-inline'`, dev and prod build.** `invai-web/vite.config.ts` and
   `invai-floor/vite.config.ts` each define `devCsp` (for `server.headers`) and `prodCsp` (for
   `preview.headers`, and mirrored in `nginx.conf`). The built `dist/index.html` in both repos
   has only `<script type="module" src="...">` — no inline script, no `onclick=` — confirmed by
   building both and grepping `dist/` (the one `onclick=` hit in web's bundled JS is React's own
   `element.onclick = handler` DOM-property assignment, not an HTML attribute; CSP doesn't govern
   that). So `prodCsp`'s `script-src` is plain `'self'`. The Vite dev server is the one exception:
   `@vitejs/plugin-react` injects one fixed inline `<script type="module">` (the Fast Refresh
   preamble — same bytes every request, since neither app sets a custom `base`), allowed by its
   exact `sha256` hash (computed at config-load time from `react.preambleCode`, not hand-copied)
   instead of `'unsafe-inline'`.
2. **HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy` on every
   response, web/floor/API, exact values.** `app.ts`'s existing `secureHeaders()` already sent
   `nosniff` (Hono's default) and `Referrer-Policy: no-referrer`; added
   `permissionsPolicy: { camera: [], microphone: [], geolocation: [], payment: [] }` (was missing
   — Hono only emits the header when the policy object is non-empty). `app.test.ts` now asserts
   `referrer-policy`, `permissions-policy` and (in prod) `strict-transport-security` by exact
   string, not just presence. Web/floor send the same four headers plus HSTS from both the Vite
   dev server (`server.headers`) and the built app (`preview.headers` and `nginx.conf`
   `add_header ... always`). HSTS is sent unconditionally by web/floor (harmless over plain
   http — a browser only acts on it over https — and it needs to already be there once TLS
   terminates in front of nginx); the API keeps its existing `env.isProd` gate, unchanged by me.
3. **Uploaded SVGs never served inline.** `modules/files/service.ts`'s `downloadUrl` now forces
   `Content-Disposition: attachment` whenever the stored object's content type is
   `image/svg+xml`, regardless of the caller's requested `disposition` — attachment strategy,
   not sanitization, per the card's "pick one." New test in `service.test.ts`: uploads an SVG
   containing `<script>alert(1)</script>`, requests it with `disposition: "inline"`, asserts the
   presigned URL's `response-content-disposition` query param starts with `attachment;`. (An
   `<img src>` embed of an SVG never executes its scripts regardless of this header — the browser
   renders it in image mode — so this doesn't affect the existing `SignedImage`/`Thumbnail`
   preview components; it matters for a direct/shared link to the file, which is the actual XSS
   vector.)
4. **API sends the same header set as web/floor.** Covered by #2 above — `app.test.ts`'s
   `"sends security headers and CORS only for the web and floor origins"` test now checks all
   four non-HSTS headers by exact value on `/health` (a JSON endpoint), not just the CSP string.
5. **Real browser run, zero CSP violations.** See below.

## Real browser verification

Ran both apps' dev servers (the same ones Playwright's `baseURL` points at) with a
`document.addEventListener('securitypolicyviolation', ...)` listener attached before any
interaction — this catches CSP blocks that never show up in `console.error` (they're a browser
security-report event, not a `console.*` call) and never appear in the extension's network log
(a CSP-blocked `fetch()` never leaves the browser). Confirmed the listener actually fires by
deliberately hitting a disallowed origin (`http://localhost:9000` under `connect-src`, which is
allowed only for `img-src`) before the real run.

**Web** (`localhost:5273`, my own port — see "Port conflict" below): logged in as
`owner@desertbloom.test`, landed on Today, clicked into Orders → an order detail (item rows,
broken-image placeholders since this seed's designs have no uploaded artwork — a data gap, not a
CSP block), Gang sheets → a sheet detail that renders its real PNG preview from MinIO
(`http://localhost:9000`, confirming `img-src` is both necessary and sufficient).
`window.__csp` after the whole run: `[]`.

**Floor** (`localhost:5274`): station setup screen, "Try a demo station", PIN entry — a real
round trip to the API ("PIN not recognized" is a server-validated response, not a network
failure). `window.__csp`: `[]`.

**Static check**: `pnpm build` in both repos, `grep` confirms no inline `<script>`/`onclick=` in
`dist/index.html`.

**nginx** (the local stand-in for whatever serves `dist/` in prod, per the card's "no AWS/CDN
dependency" flag): `nginx -t` against both `nginx.conf` files (valid), then a live
`nginx:alpine` container serving each `dist/` with the real `nginx.conf` — curled and confirmed
all five headers with exact values.

## Port conflict (environmental, not code)

Standard ports 5173/5174/3000 were held by stale processes (a leftover `gate9/` checkout, and
another agent's floor/web tabs actively navigating in the same shared browser tab group — this
workspace runs several T-12 agents in parallel). Ran my own instances on `5273`/`5274`
(`vite --port`) plus a second API instance on `:3100` (`PORT=3100 WEB_ORIGIN=http://localhost:5273
FLOOR_ORIGIN=http://localhost:5274 pnpm exec tsx src/api/server.ts` — the CLAUDE.md-sanctioned
per-agent-port pattern) so Better Auth's `trustedOrigins` would accept my alt-port origin. CSP's
`connect-src` was pointed at `:3100` only for this manual run (a one-line constant edit) and
reverted to the real default (`:3000`) before committing — confirmed by re-reading the file and
re-running `pnpm build` after the revert. Never touched the shared `:3000` API or anyone else's
tab.

## Workspace move mid-task

Partway through, the tech lead moved the workspace from `~/Desktop/projects/invai` to `~/invai`.
My uncommitted edits (all four files, across three repos) survived the `mv` intact (confirmed via
`git diff --stat` at the new path). Killed my now-stale dev/API processes (their open file
handles pointed at the moved-away path, causing dynamic-import fetch failures), restarted them
from `~/invai`, and re-ran the full verification pass (build, typecheck, lint, backend tests,
browser CSP-violation check, nginx container check) from there before committing. No worktree was
in use, so `git worktree repair` didn't apply.

## Concurrent edits to shared files

`invai-backend/src/api/app.ts` and `src/modules/files/service.ts` both picked up other agents'
unrelated commits mid-task (a CORS `allowHeaders` addition, a `tenant-export` KIND_PERMISSIONS
entry for T-12-4). Both landed as separate commits before I staged mine; `git diff` on my final
commit shows only my own hunks (the `secureHeaders()`/`permissionsPolicy` block, and the
`forceAttachment` block), confirmed before `git add`.

## Verification run

- `invai-backend`: `pnpm exec tsc --noEmit`, `pnpm exec biome check` (4 changed files), and
  `pnpm exec vitest run src/api/app.test.ts src/modules/files/service.test.ts` — 2 files, 9
  tests, all pass — against a scoped `invai_test_t125` DB (templated off `invai_test`, dropped
  at the end).
- `invai-web` / `invai-floor`: `pnpm build` (both succeed, no type errors — `vite.config.ts`
  isn't covered by the repos' `tsconfig.json` `include`, so the build itself is the type-check
  for it), `pnpm exec biome check vite.config.ts`.
- Did not run the full `pnpm e2e` golden-path suites (out of the builder's token budget per
  `agent-brief.md`; the manual browser pass above covers the specific screens this card touches).
  The wave gate should run them.

## Known gaps / follow-ups for review

- Web/floor's `connect-src`/`img-src` in `prodCsp` and `nginx.conf` use broad `https:` rather than
  a pinned API/S3 origin, since the real prod origin isn't fixed yet (SST `StaticSite`/CloudFront
  is wave 10/11, explicitly deferred) and the local "full" Docker profile's `VITE_API_URL` is
  hardcoded per-build anyway. `script-src` (the actual XSS-relevant directive) stays exactly
  `'self'`, no wildcard.
- `HSTS` is sent unconditionally by web/floor rather than gated on an `isProd`-style check the way
  the API does it — there's no equivalent env signal in a static Vite/nginx config, and sending it
  over plain http is a no-op for the browser, so this seemed like the simpler correct choice
  rather than plumbing a new build-time flag through for it.
