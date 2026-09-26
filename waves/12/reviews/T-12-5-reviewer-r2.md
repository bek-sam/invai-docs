# Review of T-12-5 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer + floor-engineer on Sonnet 5
- Verdict: **approve**

## Evidence I re-ran

| Command | Result |
|---|---|
| `git -C invai-web show d6c35ab --stat` / `git -C invai-floor show b9ef73a --stat` | web: `.gitignore`, `Dockerfile`, `nginx.conf`→`nginx.conf.template`, `scripts/render-nginx-conf.ts`, `src/lib/build/csp.ts(.test.ts)`, `vite.config.ts`; floor: same shape. All owned by web-engineer/floor-engineer; Dockerfile edits approved after the fact per tech lead |
| `pnpm exec vitest run src/lib/build/csp.test.ts` (both repos) | 4/4 pass, both repos |
| `env -u VITE_API_URL pnpm build` (both repos) | fails loudly: `Error: VITE_API_URL must be set to build for production...` |
| `VITE_API_URL=http://localhost:3000 pnpm build` (both repos) | succeeds |
| `VITE_API_URL=https://api.example.com node scripts/render-nginx-conf.ts` (both repos) | writes `nginx.conf` with `connect-src 'self' https://api.example.com` — no bare `https:` |
| `docker run --rm -v .../nginx.conf:... nginx:alpine nginx -t` (both repos, rendered config) | "syntax is ok" / "test is successful" |

## Round-1 blocking finding — resolved
`connect-src` is now derived from `VITE_API_URL` (`src/lib/build/csp.ts`'s `requireApiOrigin`/`connectSrc`, shared by `vite.config.ts` and `scripts/render-nginx-conf.ts`), with a hard build failure if the var is unset — no silent fallback to `'self' https:`. Verified the failure, the success case, and the rendered nginx header all directly above.

## Acceptance criteria
Unchanged from r1 except AC #1 (strict CSP): now fully met — `connect-src` is pinned to the API origin (or `'self'` for an explicit same-origin `""`), not a broad `https:`. All other criteria stand as reported in r1 (`T-12-5-reviewer-r1.md`).

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (web-engineer/floor-engineer files; Dockerfile grant confirmed by tech lead)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened (new `csp.test.ts`, 4 tests, purely additive)
- [x] Tenancy / idempotency / money-in-cents / en-es text — n/a
- [x] Decisions recorded (commit message + r1 file document the fix and its verification)

## Optional notes (not blocking)
Carried over from r1, still true and still not blocking: `style-src 'unsafe-inline'` in every CSP variant, `img-src` still broad `https:` in prod (only `connect-src` was fixed), HSTS sent unconditionally by web/floor rather than gated like the API's `env.isProd`.
