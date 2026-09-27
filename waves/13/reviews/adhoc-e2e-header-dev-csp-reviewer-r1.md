# Review of ad hoc fix: E2E contract-version header + dev CSP MinIO (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: (ad hoc, found during the wave 13 HEAD live test run) — model not stated
- Verdict: approve

Scope: uncommitted changes only. Owned paths: `invai-web/e2e/helpers/api.ts`, `invai-web/vite.config.ts`,
`invai-floor/e2e/helpers/api.ts`. No commits ahead of `origin/main` in either repo.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web diff --stat` / `status --short` | `e2e/helpers/api.ts` (+9/-3), `vite.config.ts` (+1/-1); nothing else modified or untracked |
| `git -C invai-floor diff --stat` / `status --short` | `e2e/helpers/api.ts` (+6/-2); nothing else |
| `scan-test-weakening.sh invai-web origin/main` | `Result: no hits` (removed=0 added=0 assertions, no skips/mocks/config loosening) |
| `scan-test-weakening.sh invai-floor origin/main` | `Result: no hits` |
| web: `pnpm typecheck` | pass |
| web: `pnpm lint` | `Checked 145 files ... No fixes applied.` |
| web: `pnpm test` | `Test Files 15 passed (15)`, `Tests 82 passed (82)` |
| web: `VITE_API_URL=http://localhost:3000 pnpm build` | `✓ built in 1.29s` (only the pre-existing chunk-size warning) |
| floor: `pnpm typecheck` | pass |
| floor: `pnpm lint` | `Checked 76 files ... No fixes applied.` |
| floor: `pnpm test` | `Test Files 9 passed (9)`, `Tests 96 passed (96)` |
| floor: `VITE_API_URL=http://localhost:3000 pnpm build` | `✓ built in 493ms`, PWA `dist/sw.js` generated |
| `curl -sI http://localhost:5173 \| grep -i content-security` | `... connect-src 'self' http://localhost:3000 http://localhost:9000; ...` (everything else unchanged: `default-src 'self'`, hashed `script-src`, `object-src 'none'`, `base-uri 'none'`, `frame-ancestors 'none'`) |
| `curl -X POST :3000/rpc/floor/staff` with `authorization: Station <seed token>`, **no** version header | `426 CLIENT_TOO_OLD`, `"minVersion":"0.3.0","current":null` (reproduces the author's "before") |
| same call with `x-contract-version: 0.4.0`, body `{"json":{}}` | 200, staff list returned (gate passes with the header the helpers now send) |
| `curl -X OPTIONS :9000/invai-local/x -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: PUT"` | `204`, `Access-Control-Allow-Origin: http://localhost:5173`, `Allow-Methods: PUT` (so CSP was the only remaining blocker for the browser PUT) |

Not re-run, by instruction: `pnpm e2e` (web, floor) and `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts`
(they consume the fresh seed; the author reports 13/13, 15/15, 3/3). My curl reproduction above covers the
mechanism each suite was failing on.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | web `stationSession`/`floorSession` (`invai-web/e2e/helpers/api.ts:84-96`) add `[CONTRACT_VERSION_HEADER]: CONTRACT_VERSION`; `Session.fetch` applies `this.headers` last, so it is sent on every RPC. Floor `client()` (`invai-floor/e2e/helpers/api.ts:19-29`) adds it to the `RPCLink` headers; every floor spec (`floor.spec.ts`, `press.spec.ts`, `offline.spec.ts`) builds its station/floor clients through `client()`, and no other e2e file constructs `Station`/`Bearer` headers. Both import the constants from `@invai/contracts` (`compat.ts:8,19`, re-exported by `index.ts`), not a hard-coded string, matching `invai-floor/src/api/rpc.ts:35`. Backend gate reproduced: no header → 426, header → 200. |
| 2 | yes | `invai-web/vite.config.ts:33` adds the existing `S3_ORIGIN` (`http://localhost:9000`) to the **dev** `connect-src` only; the live header shows it. Minimal: one origin, no wildcard, `prodCsp` untouched. MinIO preflight allows PUT from :5173, so the XHR in `src/lib/upload.ts:31-32` is now unblocked. |
| 3 | yes | Scan: no hits in either repo. Changes are test helpers plus the dev-only CSP; `prodCsp`, `csp.ts` and all `src/**` are untouched; `pnpm build` output is unaffected. Adding the header in the floor `client()` also on non-floor calls is harmless (the gate ignores other auth modes, `orpc.ts:97-98`). |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`): exactly the three owned files.
- [x] Nothing outside scope: each hunk serves criterion 1 or 2.
- [x] Tests exercise the behavior, and none were weakened: scan clean; the helpers now satisfy a real backend control (ADR 0012) instead of bypassing it; the gate itself is unchanged and still rejects header-less tablets (426 reproduced).
- [x] Tenancy, idempotency, money, en/es: not applicable (no backend, schema, UI copy or request-path changes).
- [x] Decisions recorded where needed: none needed; follows ADR 0012 and the existing floor client pattern.

## Follow-ups (not blocking this diff)
1. **Production CSP gap (web).** `prodCsp` in `invai-web/vite.config.ts:49-59` uses
   `connect-src ${connectSrc(requireApiOrigin(VITE_API_URL))}` and `src/lib/build/csp.ts:31-33`
   (`connectSrc`) returns only `'self'` + the API origin; `scripts/render-nginx-conf.ts` derives the nginx
   header the same way. The presigned S3 bucket origin is not in it, so in any deployed build every browser
   presigned PUT (CSV import, design and other uploads via `src/lib/upload.ts`) will be blocked exactly as in
   dev before this fix. Suggested fix: derive the bucket origin from a build env (e.g. `VITE_S3_ORIGIN`),
   pin it (no wildcard, no `https:`), feed it to both `vite.config.ts` and `render-nginx-conf.ts`, with a
   `csp.test.ts` case. Owner: web-engineer, security-reviewer co-review (CSP is a control). Should be filed
   as a backlog item / next-wave card before any deploy.
2. Floor dev CSP (`invai-floor/vite.config.ts:34`) has `connect-src 'self'` only; fine today because the
   floor does not upload to S3. Note it if the floor ever gains uploads.

## Optional notes (not blocking)
- The web helper sets the header per session type, the floor helper on every client. Both are correct;
  the asymmetry is only stylistic.
