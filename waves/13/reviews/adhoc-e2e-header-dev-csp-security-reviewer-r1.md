# Review: ad-hoc — dev CSP connect-src + E2E contract-version header (security co-review, round 1)

- Reviewer: security-reviewer (Opus 5.5), 2026-09-26
- Change: uncommitted diff in `invai-web/vite.config.ts`, `invai-web/e2e/helpers/api.ts`, `invai-floor/e2e/helpers/api.ts`
- Risk flags considered: files (presigned upload), CSP (B-24 / T-12-5 follow-through)

## Verdict: approve

No blocking findings. One follow-up (production CSP blocks presigned uploads) is confirmed and handed to
web-engineer + platform-sre; it is not introduced by this diff and does not block it.

## Diff read

1. `invai-web/vite.config.ts` `devCsp`: `connect-src 'self' ${DEV_API_ORIGIN}` → `connect-src 'self' ${DEV_API_ORIGIN} ${S3_ORIGIN}`
   (`S3_ORIGIN = "http://localhost:9000"`, already present in `img-src`).
2. `invai-web/e2e/helpers/api.ts`: `stationSession` / `floorSession` add `[CONTRACT_VERSION_HEADER]: CONTRACT_VERSION`.
3. `invai-floor/e2e/helpers/api.ts`: `client()` adds the same header.

## Evidence I re-ran

| Command | Result |
|---|---|
| `invai-web: pnpm typecheck && pnpm lint` | tsc clean; `biome check .` 145 files, no fixes |
| `invai-web: vitest run src/lib/build` | `Tests 4 passed (4)` (csp.test.ts) |
| `invai-floor: pnpm typecheck && pnpm lint` | tsc clean; `biome check .` 76 files, no fixes |
| `curl -D - http://localhost:5173/` (running dev server) | `connect-src 'self' http://localhost:3000 http://localhost:9000` — dev header carries the change |
| `curl -X OPTIONS -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: PUT" http://localhost:9000/invai-local/x` | `204`, `Access-Control-Allow-Origin: http://localhost:5173` — once CSP allows it, MinIO accepts the browser PUT |
| `node -e … connectSrc(requireApiOrigin("https://api.example.com"))` | `'self' https://api.example.com` — prod connect-src has no bucket origin |
| `grep S3\|bucket\|amazonaws src/lib/build/csp.ts nginx.conf.template` | no hits |

Not run: full `pnpm test`/`pnpm build`/E2E (the change is a dev-server header and test helpers; the reviewer
and QA own the golden-path re-run).

## Q1. Is the dev CSP change correct and minimal?

Yes.
- `devCsp` is only wired into `server.headers` (`vite.config.ts`, `server: { port: 5173, headers: { "Content-Security-Policy": devCsp, … } }`).
  `preview.headers` uses `prodCsp`; `pnpm build` output is served with `nginx.conf` rendered by
  `scripts/render-nginx-conf.ts` from `src/lib/build/csp.ts`. Neither reads `devCsp` or `S3_ORIGIN`. The
  prod path is unchanged.
- The origin added is exact (`http://localhost:9000`), which equals the presigner endpoint locally
  (`invai-backend/.env`: `S3_ENDPOINT=http://localhost:9000`, no `S3_PUBLIC_ENDPOINT`, path-style). No
  wildcard, no scheme source.
- Threat: an XSS in the dev app could now `fetch` local MinIO. MinIO requires a signature for every write and
  the bucket is private, so the only new reachable target is a loopback service on the developer's machine.
  No tenant data boundary, no prod exposure. Nothing that matters is weakened; `script-src`, `object-src`,
  `base-uri`, `frame-ancestors` are untouched.

## Q2. Production connect-src lacks the bucket origin — confirmed

- `src/lib/build/csp.ts` `connectSrc()` returns `'self'` plus the API origin only; `vite.config.ts` `prodCsp`
  and `nginx.conf.template` (`connect-src __CONNECT_SRC__`) both use it.
- In AWS the backend presigns against real S3 (`invai-infra/sst.config.ts` sets `S3_BUCKET`, no
  `S3_ENDPOINT`/`S3_PUBLIC_ENDPOINT`), so `uploadUrl` is `https://<bucket>.s3.<region>.amazonaws.com/...`,
  a third origin. `src/lib/upload.ts` PUTs it with `XMLHttpRequest`, which `connect-src` governs, so every
  browser upload (designs, artwork, CSV import, template backgrounds) fails in prod with "storage unreachable".
- This is a functional break, not a security hole (fails closed). Tracked as follow-up **F-1** below.
- Floor is unaffected: `invai-floor/src` has no presigned PUT (grep for `uploadUrl`/`XMLHttpRequest`: none);
  it only needs `img-src`.

### Recommended fix shape (F-1, owners: web-engineer for `csp.ts`/`vite.config.ts`/`render-nginx-conf.ts`, platform-sre for `sst.config.ts`)

1. **One build env var, pinned exact origin:** add `VITE_UPLOAD_ORIGIN` (or `VITE_S3_ORIGIN`), required at
   build time like `VITE_API_URL` (`requireUploadOrigin()` throws when undefined; `""` = same-origin/proxied
   uploads). Reduce it with `new URL(raw).origin` and append it in `connectSrc(apiOrigin, uploadOrigin)`, used
   by both `prodCsp` and `render-nginx-conf.ts` so the two stay identical.
2. **Virtual-hosted-style only.** The origin must be the bucket's own host
   (`https://<bucket>.s3.<region>.amazonaws.com`), never `https://s3.<region>.amazonaws.com` (path-style —
   shared by every bucket in the region, so an XSS could PUT exfiltrated data into an attacker's bucket),
   never `https://*.amazonaws.com`, `*.s3.amazonaws.com` or `https:`. Keep `S3_FORCE_PATH_STYLE` false in
   AWS. Reject in `requireUploadOrigin()` any value whose host is `s3.amazonaws.com` / `s3.<region>.amazonaws.com`
   or contains `*`.
3. **Single source of truth for the host.** Set the backend's `S3_PUBLIC_ENDPOINT` and the web build's
   `VITE_UPLOAD_ORIGIN` from the same SST value (e.g. `https://${files.nodes.bucket.bucketRegionalDomainName}`),
   so the presigned URL host and the CSP origin cannot drift. (If a CDN/custom domain fronts uploads later,
   change both together.)
4. **Tests:** extend `src/lib/build/csp.test.ts`: the upload origin is present and exact; a path-style or
   wildcard value throws; `undefined` throws. Plus an E2E/preview smoke that a presigned PUT succeeds under
   `pnpm preview` headers.
5. **Bucket CORS (same card, platform-sre):** SST's `Bucket` default CORS is `allowOrigins: ["*"]`, methods
   `DELETE GET HEAD POST PUT` (`.sst/platform/src/components/aws/bucket.ts:1116-1124`). Signatures still gate
   access, but pin `cors: { allowOrigins: [web.url], allowMethods: ["PUT", "GET", "HEAD"], allowHeaders: ["content-type", "content-length"] }`
   (Low, hardening).
6. **Verify the header actually ships in AWS (platform-sre):** `sst.aws.StaticSite` (CloudFront) serves
   `invai-web`/`invai-floor` in `sst.config.ts`, not the nginx image, so the CSP in `nginx.conf` may not be
   sent at all there. Confirm CloudFront response headers carry the same CSP, or F-1 is moot and B-24 is
   not in force in AWS. Not proven in this review — needs a deploy or synth check.

Clock: functional/hardening, not a DPP vulnerability; target before the first AWS staging deploy
(release-checklist gate), not the 7/30-day clocks.

## Q3. Other security impact in the diff

- E2E helpers sending `x-contract-version`: test code only. The header is a client-declared compatibility
  gate (`invai-contracts/src/compat.ts`: backend refuses floor/station calls below
  `MIN_FLOOR_CONTRACT_VERSION` with `CLIENT_TOO_OLD`). It is not an auth or tenancy control; sending the
  current version from tests doesn't bypass anything, and a real attacker can set any header anyway. No
  secrets, tokens or PII added. `authz.test.ts` coverage is unaffected (backend suite not touched).
- No weakened tests: no `.skip`/`.only`, no loosened assertions in the diff.

## Checklist

- [x] Ownership: `vite.config.ts` and `e2e/helpers/**` — web-engineer / qa-engineer paths; not mine to judge scope beyond security.
- [x] Prod CSP unchanged (read `prodCsp`, `csp.ts`, `nginx.conf.template`, `render-nginx-conf.ts`).
- [x] No wildcard or scheme source added.
- [x] No PII, secrets or credentials in the diff.
- [x] Tenancy / auth / idempotency: n/a (no backend change).

## Blocking findings

none

## Follow-ups (non-blocking)

| id | severity | area | description | owner | due |
|---|---|---|---|---|---|
| F-1 | functional (fails closed) | web CSP / files | Prod `connect-src` has no bucket origin; browser presigned PUT uploads fail in AWS. Fix shape above (pinned virtual-hosted bucket origin from one SST value). | web-engineer + platform-sre | before first AWS staging deploy |
| F-2 | Low | infra / files | SST bucket CORS defaults to `*` origins and all methods; pin to web origin, PUT/GET/HEAD. | platform-sre | same card as F-1 |
| F-3 | needs verification | infra / CSP | StaticSite (CloudFront) may not send the nginx CSP at all in AWS; confirm B-24 headers ship. | platform-sre | before first AWS staging deploy |

## Optional notes

- `prodCsp` `img-src ... https:` is still broad (pre-existing, both apps). The same pinned bucket origin from
  F-1 could replace `https:` in `img-src` later (hardening).
