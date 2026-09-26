# Review of T-12-5 (round 2)

- Reviewer: security-reviewer on Sonnet 5
- Author: web-engineer + floor-engineer on Sonnet 5
- Verdict: **approve**

## Evidence I re-ran

| Command | Result |
|---|---|
| Read `src/lib/build/csp.ts` (both repos) | `requireApiOrigin` throws on `undefined` (unset), treats `""` as a deliberate same-origin choice, else `new URL(raw).origin` — no path/query leak into the header; `connectSrc` emits `'self'` alone when same-origin, `'self' <origin>` otherwise |
| `pnpm exec vitest run src/lib/build/csp.test.ts` (both repos) | 4/4 pass |
| `env -u VITE_API_URL pnpm build` (both repos) | build fails loudly, no silent `https:` fallback |
| `VITE_API_URL=https://api.example.com node scripts/render-nginx-conf.ts` (both repos) then `grep connect-src nginx.conf` | `connect-src 'self' https://api.example.com` — no bare `https:` anywhere |
| `docker run --rm nginx:alpine nginx -t` against the rendered `nginx.conf` (both repos) | valid |
| `git -C invai-web/-floor show <sha> -- Dockerfile` | build stage now runs `render-nginx-conf.ts` after `pnpm build`, using the same `VITE_API_URL` the build stage already sets; final stage copies the rendered `nginx.conf` from the build stage (not the repo's, which is now a gitignored artifact) — the header nginx serves cannot drift from the origin the JS bundle actually calls |

## Checklist re-check (r1 blocker only; rest unchanged from r1)
- [x] `connect-src` narrow to the API origin and SSE — **now met**. SSE rides the same origin as RPC (`EventSource`/`fetch` are both governed by `connect-src`; floor's commit message confirms `src/realtime/sse.ts` uses fetch-based SSE, not a separate host), so pinning the one API origin covers it.
- [x] No new bypass introduced by the fix itself: `requireApiOrigin` uses `new URL(raw).origin`, which normalizes away any path/query/credentials in `VITE_API_URL` rather than interpolating the raw string into the CSP header (no header-injection surface from a malformed env var).
- [x] The generated `nginx.conf` is gitignored and rebuilt from `nginx.conf.template` every image build inside the Dockerfile's build stage — no risk of a stale hand-edited `nginx.conf` silently shipping with the old broad policy.

## Blocking findings
None. Round 1's `connect-src` finding is resolved with a build-time-enforced, single-source-of-truth fix (same derivation feeds `vite.config.ts` and the nginx template), and a build without the required env var now fails instead of degrading to a permissive CSP.

## Optional notes (not blocking, unchanged from r1)
- `style-src 'self' 'unsafe-inline'` remains in every mode — accepted trade-off noted in r1 (React `style` prop / Tailwind), `script-src` is what matters for XSS and stays strict.
- `img-src` still `https:` broad in prod/nginx — only `connect-src` was in scope for this fix; tightening `img-src` the same way (MinIO/S3 origin from an env var) would be a natural follow-up but isn't required by this card.
- HSTS still sent unconditionally by web/floor (no `isProd`-style gate) — harmless per RFC 6797, noted for consistency only.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy / idempotency / money-in-cents / en-es text — n/a
- [x] Decisions recorded where needed
