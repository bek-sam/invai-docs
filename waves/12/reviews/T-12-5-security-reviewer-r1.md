# Review of T-12-5 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: web-engineer + floor-engineer on Sonnet 5
- Verdict: **changes-required**

## Evidence I re-ran

| Command | Result |
|---|---|
| Read `invai-web/vite.config.ts`, `invai-floor/vite.config.ts`, both `nginx.conf` in full (5896ba5, c7c171b) | `script-src 'self'` (+ exact sha256 hash for dev preamble) everywhere; no `'unsafe-eval'` anywhere (`grep -rn "unsafe-eval" invai-web invai-floor invai-backend` → no hits) |
| Read `invai-backend/src/api/app.ts` (7411508) | `strictTransportSecurity: env.isProd ? "max-age=31536000; includeSubDomains" : false` — HSTS correctly gated to prod on the API |
| `pnpm exec vitest run src/api/app.test.ts src/modules/files/service.test.ts` (invai-backend) | 9/9 pass |
| `docker run --rm nginx:alpine nginx -t` against both `nginx.conf` | both valid |
| `pnpm build` both repos + `grep onclick=`/inline-`<script>` on `dist/index.html` | clean in both |
| Read `invai-floor/vite.config.ts` VitePWA config, `src/main.tsx` (`registerSW` from `virtual:pwa-register`), built `dist/sw.js` | SW is registered from the bundled main chunk (not an injected external/inline script), `sw.js` uses native `importScripts` (not `eval`), precache list is same-origin assets only, `navigateFallbackDenylist` excludes `/rpc`, `/events`, `/api` — nothing here needs a CSP relaxation |
| `grep -rn "presignGet\|Content-Disposition" invai-backend/src/lib/s3.ts invai-backend/src/modules/files/service.ts` | one file-serving code path (`downloadUrl`); SVG force-attachment is a choke point, not one of several routes that could diverge |

## Checklist (playbook §4 + card-specific)

- [x] `script-src`/`object-src`/`base-uri`/`frame-ancestors` strict, no `'unsafe-inline'`/`'unsafe-eval'`, in prod builds (web, floor, API) — **met**
- [ ] `connect-src` narrow to the API origin and SSE — **not met in prod** (see blocking finding)
- [x] `img-src` still allows MinIO/S3 presigned images — met (dev: pinned `S3_ORIGIN`; prod/nginx: `https:`, broader than needed but functional — see note)
- [x] HSTS only where it matters — API gates on `env.isProd`; web/floor send it unconditionally, which is a no-op over plain HTTP per RFC 6797 §7.2 (UAs must ignore STS delivered over an insecure transport), so not a real exposure
- [x] SVGs always sent as attachment — `files/service.ts` forces `Content-Disposition: attachment` for `image/svg+xml` regardless of requested `disposition`; test covers a `<script>`-bearing SVG; single code path, no bypass found
- [x] Floor PWA service worker still works under the CSP — verified (see evidence row above); no `worker-src` needed since same-origin `default-src 'self'` covers it
- [x] nginx configs valid — `nginx -t` passes for both
- [x] No new tenant/PII/payment surface introduced by this card — correct, header/CSP/attachment-only change
- [x] Backend edits stay inside the wave.md grant (`api/app.ts` headers hunk, SVG-to-attachment in `files/service.ts`) — confirmed by `git show --stat`

## Blocking findings

1. `invai-web/vite.config.ts` (`prodCsp`) and `invai-web/nginx.conf`, mirrored in `invai-floor/vite.config.ts`/`nginx.conf` — `connect-src 'self' https:` accepts a connection to *any* HTTPS origin, not just the API and its SSE stream. This is the one directive that actually bounds data exfiltration if any future XSS (this card doesn't introduce one, but the CSP exists precisely for the next one) or a compromised third-party script gets a foothold: with `connect-src ... https:`, exfiltrating auth tokens/order data to `https://attacker.example` is a normal fetch, not a CSP violation. The dev CSP in the same file already proves this is fixable now — it pins a real `API_ORIGIN` constant — and the task report confirms the prod API origin is already fixed per Docker build (`VITE_API_URL` "hardcoded per-build anyway"), so there's no technical blocker to threading that same value into `prodCsp`/`nginx.conf` instead of falling back to `https:`. Recommend: build `prodCsp`'s `connect-src` from the same env var Vite already injects at build time (e.g. `import.meta.env.VITE_API_URL`), falling back to same-origin only if unset, and drop the bare `https:`.

## Optional notes (not blocking)
- `style-src 'self' 'unsafe-inline'` in every mode (dev/prod/nginx, both repos): outside this card's literal AC (which is scoped to `script-src`'s nonce/hash), but worth flagging since it is technically an `'unsafe-inline'` grant in the CSP. Practical justification: React's `style` prop and Tailwind's compiled inline styles would require a much larger refactor to run under a strict `style-src`, and the exploitable impact (CSS-based data leakage via attribute selectors, page defacement) is far below `script-src`'s — which is the directive that's actually strict here. Not asking for a fix this round; flagging so it's a conscious, recorded trade-off rather than an oversight.
- Same `https:` breadth in `img-src` (prod/nginx) as in `connect-src` — works today, would tighten for free alongside the `connect-src` fix using the same origin constant.
- Backend's `env.isProd` gate on HSTS is the right pattern; web/floor could match it with a build-time flag for consistency, but there is no live exposure from doing it unconditionally today.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy / idempotency / money-in-cents / en-es text — n/a
- [x] Decisions recorded where needed
