# Review of T-24-1 (round 1) — web-engineer co-review

- Reviewer: web-engineer on Sonnet 5
- Author: platform-sre on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show c1d53a8` | only `src/lib/build/csp.ts` and `vite.config.ts` touched; matches the grant (prod `connect-src` only); `devCsp` array untouched |
| `pnpm typecheck` | clean |
| `pnpm test --reporter=dot src/lib/build` | 1 file / 4 tests passed (existing `requireApiOrigin`/`connectSrc(api)` cases only) |
| `pnpm build` (no `VITE_API_URL`) | fails loudly: `VITE_API_URL must be set to build for production…` — same pre-existing guard, unchanged by this diff |
| `VITE_API_URL=http://localhost:3000 pnpm build` | `✓ built in 1.51s` |
| `node_modules/.bin/biome check src/lib/build/csp.ts vite.config.ts` | clean |
| `invai-web/.github/workflows/ci.yml` | job sets `env: VITE_API_URL: http://localhost:3000` before `pnpm build`, so the missing-var failure is handled in CI, not just documented |
| Direct exercise of `uploadOrigin` (bucket https, `?x=1` query, `*.amazonaws.com`, `ftp://`, `http://evil.com`, `http://localhost:9000`, `http://127.0.0.1:9000`, blank, undefined) | matches the report: valid https/localhost pass through origin-only; wildcard/non-https throw the named error; blank/undefined → `""` (no extra origin), never a silent widen |

## Acceptance criteria (B-190 hunk only)
| # | Met? | Evidence |
|---|---|---|
| Grant stays inside `vite.config.ts` + `csp.ts`, prod `connect-src` only | Yes | diff `--stat` above; dev CSP (`devCsp`, `server.headers`) byte-identical |
| Dev CSP/dev server unchanged | Yes | only the `command === "build" \|\| isPreview` branch changed |
| Missing-`VITE_API_URL` build failure intended, documented, CI-handled | Yes | pre-existing guard (review r1, T-12-5), unchanged; CI job sets it |
| `csp.ts` tests cover the new origin | **No** | `csp.test.ts` still only covers `requireApiOrigin`/`connectSrc(api)`; no case for `uploadOrigin` or `connectSrc(api, s3)` |

## Blocking findings
None. The missing-test gap is real but not blocking this round (see note).

## Checks
- [x] Only owned/grant paths changed
- [x] Nothing outside scope
- [ ] Tests exercise the new behavior — `uploadOrigin`/`connectSrc(api, s3)` have no unit test (see note); behavior itself verified live by me, the author and the primary reviewer with matching adversarial cases
- [x] No PII/tenancy/money surface in this hunk (build-time CSP string only)
- [x] Decisions: N/A for this hunk (author's report covers the infra-side choices)

## Optional notes (not blocking)
1. `src/lib/build/csp.test.ts` needs cases for `uploadOrigin` (valid bucket origin with query stripped, `http://localhost`/`127.0.0.1`, wildcard throws, non-https throws, blank/undefined → `""`) and `connectSrc(api, s3)` joining both. Agree with the primary reviewer this isn't scope creep for platform-sre (not in the named grant) and isn't a functional defect (live-exercised correctly by three people now) — but it's my file to add. I'll pick it up as a fast follow so this security-relevant validation has a permanent regression test, rather than block T-24-1 (an infra-prep card with no real deploy) on it.
2. `scripts/render-nginx-conf.ts` still calls the one-arg `connectSrc(origin)` (no S3 origin) — correctly flagged by the author as outside this grant; same fast-follow.
