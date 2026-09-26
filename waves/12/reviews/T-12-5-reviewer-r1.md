# Review of T-12-5 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer + floor-engineer on Sonnet 5
- Verdict: **changes-required**

## Evidence I re-ran

| Command | Result |
|---|---|
| `git -C invai-web show 5896ba5 --stat` / `-- vite.config.ts nginx.conf` | 2 files (nginx.conf, vite.config.ts), both owned by web-engineer |
| `git -C invai-floor show c7c171b --stat` / `-- vite.config.ts nginx.conf` | 2 files (nginx.conf, vite.config.ts), both owned by floor-engineer |
| `git -C invai-backend show 7411508` | 4 files: `api/app.ts`, `api/app.test.ts`, `modules/files/service.ts`, `modules/files/service.test.ts` — matches wave.md's explicit grant ("security-headers middleware hunk in `api/app.ts`", "SVG file serving to attachment") |
| `pnpm exec vitest run src/api/app.test.ts src/modules/files/service.test.ts` (invai-backend) | 2 files, 9 tests, all pass |
| `pnpm build` (invai-web) | succeeds; `dist/index.html` has one `<script type="module" src=...>`, no inline script, no `onclick=` |
| `pnpm build` (invai-floor) | succeeds; `dist/index.html` has one `<script type="module" src=...>`, no inline script; `dist/sw.js` + `dist/workbox-*.js` generated |
| `docker run --rm -v .../nginx.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine nginx -t` (web) | "syntax is ok" / "test is successful" |
| same, floor `nginx.conf` | "syntax is ok" / "test is successful" |
| `.claude/skills/independent-review/scan-test-weakening.sh`-style diff of `7411508~1..7411508` for the two changed test files | no `.skip`/`.only`/`fixme`/`it.fails` hits; new test is additive (asserts `attachment;` disposition), no assertion loosened |
| `git -C invai-backend/-web/-floor status --short` | invai-web/invai-floor clean; invai-backend has **unrelated uncommitted** edits to `src/modules/channels/{shopify,webhooks}.test.ts` — not part of `7411508`, not this card's files, left untouched |

## Acceptance criteria

| # | Met? | Evidence |
|---|---|---|
| 1. Strict CSP, no `'unsafe-inline'`, dev + prod | Partially | `script-src` is `'self'` (plus an exact sha256 hash for the dev Fast Refresh preamble) in dev, preview and nginx, in both repos — confirmed by reading `vite.config.ts`/`nginx.conf` and by the clean `dist/index.html` grep. **But** `prodCsp`/`nginx.conf`'s `connect-src` is `'self' https:` (not the card's "API origin and SSE"/narrow origin) — see blocking finding below. `style-src` carries `'unsafe-inline'` in every mode (dev, prod, nginx) — see optional note. |
| 2. HSTS/nosniff/Referrer-Policy/Permissions-Policy, exact values, web+floor+API | Met | `app.test.ts` asserts all four by exact string; web/floor send the same four from `server.headers`/`preview.headers`/`nginx.conf`. Note: web/floor send HSTS unconditionally (not gated like the API's `env.isProd`) — optional note, not blocking (RFC 6797: browsers ignore STS over plain HTTP). |
| 3. Uploaded SVGs never served inline | Met | `files/service.ts` forces `attachment` whenever `head.contentType === "image/svg+xml"`, overriding the caller's `disposition`; `downloadUrl` is the only file-serving code path in the backend (`grep -rn "presignGet"` → one call site). New test uploads a script-bearing SVG and asserts `attachment;` in the presigned URL; test passes. |
| 4. API sends the same header set as web/floor | Met | Same `app.test.ts` assertions, run against `/health` (JSON endpoint). |
| 5. Real browser run, zero CSP violations | Not independently re-run | Report describes a live `securitypolicyviolation`-listener pass with `window.__csp === []` for both apps, plus a listener self-test (deliberately triggering one violation first). I did not re-drive a browser this round (light review); the static evidence (clean `dist/` grep, passing header tests, valid nginx configs) is consistent with the report and gives no reason to doubt it. |

## Blocking findings

1. `invai-web/vite.config.ts:44` and `invai-floor/vite.config.ts:44` (`prodCsp`), mirrored in both repos' `nginx.conf` — `connect-src 'self' https:` is not narrow: it lets any XHR/fetch/EventSource target *any* HTTPS origin, not just the API and its SSE endpoint. A stored-XSS or compromised-dependency bug elsewhere in the SPA (unrelated to this card) could exfiltrate session/order data to an attacker-controlled HTTPS endpoint without tripping the CSP at all — which defeats a large part of why `connect-src` exists. The author's own report already flags this as a known gap ("prod origin isn't fixed yet"), but the dev CSP in the same file already pins a real constant (`API_ORIGIN`/`VITE_API_PROXY`) and the report confirms `VITE_API_URL` is "hardcoded per-build anyway" for the Docker "full" profile — so the same build-time value is available to narrow `prodCsp`'s `connect-src` to `'self' <API origin>` (SSE rides the same origin/path, no separate host needed). This should be fixed before this card ships, not carried as a follow-up, since it is the one directive most load-bearing for the card's threat model (S-G5/S-G6, XSS/exfiltration).

## Checks
- [x] Only owned paths changed (`git diff --stat` on each of the three commits — web: `nginx.conf`, `vite.config.ts`; floor: same; backend: `api/app.ts`, `api/app.test.ts`, `modules/files/service.ts`, `modules/files/service.test.ts`, all pre-granted in `wave.md`)
- [x] Nothing outside scope (no unrelated files in any of the three commits)
- [x] Tests exercise the behavior, and none were weakened (new SVG-attachment test and new header-exact-value assertions are additive; no `.skip`/loosened assertion found)
- [x] Tenancy / idempotency / money-in-cents / en-es text — n/a to this card (no new tables, no money, no new user-facing strings)
- [x] Decisions recorded where needed (report documents the port-conflict workaround and the connect-src/img-src trade-off; wave.md records the backend grant)

## Optional notes (not blocking)
- `style-src 'self' 'unsafe-inline'` is present in every CSP variant (dev, prod, nginx) in both repos. The card's AC #1 language ("not `'unsafe-inline'`", nonce/hash) is about `script-src` specifically (its own test only checks for inline `<script>`/`onclick=`), and React's `style` prop plus Tailwind's inline-style usage make a strict `style-src` a much bigger lift than this card's scope — but worth a follow-up card if the wave wants to close this too, since `script-src` (the actual XSS vector) is already clean.
- Same broad-`https:` pattern in `img-src` (prod/nginx) — works for MinIO/S3 today but is wider than needed; fixing it alongside the `connect-src` finding (same build-time origin constant) would tighten both in one pass.
- HSTS sent unconditionally by web/floor rather than gated the way the API gates on `env.isProd` — harmless (browsers ignore `Strict-Transport-Security` received over plain HTTP per RFC 6797) but inconsistent; a build-time flag would match the API's pattern for hygiene.
- Unrelated uncommitted changes to `invai-backend/src/modules/channels/{shopify,webhooks}.test.ts` exist in the shared tree (not part of `7411508`) — flagging only so the tech lead knows they're there; not this card's concern.
