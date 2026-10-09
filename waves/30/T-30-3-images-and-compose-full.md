# T-30-3: Multi-stage non-root images pinned by digest; compose `full` profile runs the API golden path

| Field | Value |
|---|---|
| Wave | 30 |
| Scope ref | `always-in-scope: security, reliability` (deploy prep, owner order 2026-10-09); backlog B-21 (image part), B-76 (compose `full`, ignore files) |
| Spec | `waves/24/T-24-3.md` (replaced by this card), `research/12` S-G15–17, `research/11` §10 |
| Owner | platform-sre |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (sonnet) |
| Risk flags | security (base images, secrets in layers, users) |
| Model | sonnet |

Role file: `.claude/agents/platform-sre.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/platform-sre/` (read MEMORY.md first).

## Owned paths (edit)
- `invai-backend/Dockerfile`, `invai-web/Dockerfile`, `invai-floor/Dockerfile`, `invai-imaging/Dockerfile`, and their ignore files. The build context of backend, web and floor is the workspace root, which is not a git repo, so use BuildKit's per-Dockerfile ignore file (`<repo>/Dockerfile.dockerignore`), not a root `.dockerignore`; `invai-imaging/.dockerignore` stays.
- `invai-infra/local/docker-compose.yml` (`full` profile services only; the infra services stay byte-identical), `invai-infra/scripts/full.sh` (new runner), `invai-infra/README.md` (a short `full` section)
- Report: `invai-docs/waves/30/reports/T-30-3.md`

## Read-only paths
- All source code, `package.json` files, `tsup.config.ts` (T-30-2), `sst.config.ts`, `.github/**` (CI changes are wave 31), the shared dev DB `invai`

## Depends on
- T-30-2's build commit (the tech lead gives you its SHA). Entry points: `dist/api/server.js`, `dist/worker/index.js`, `dist/db/{bootstrap,migrate,reference-seed}-cli.js`; migrations in `/app/drizzle`.

## Acceptance criteria
1. Every image is multi-stage; every base image (node, python, uv, the static web server) is pinned by digest (`name:tag@sha256:...`), none on `latest`; the runtime stage runs as a non-root user with a fixed uid; each has a `HEALTHCHECK` (api, imaging, web, floor; worker if it has a probe, else say why); the runtime holds production dependencies only.
2. No secret in any layer: `docker history --no-trunc` shows none, and no `.env*`, `seed-output.json`, `.git`, `node_modules` from the host, `e2e/` or test files are in the image (show a `find` inside each image).
3. The backend image runs api, worker and the three CLIs by command, with `drizzle/` at `/app/drizzle`.
4. Web and floor: `VITE_API_URL` is a build argument (a runtime env var does nothing for a Vite build); the static server serves the SPA fallback, sends no server version, and listens on an unprivileged port.
5. `docker compose --profile full` uses its **own database `invai_full`** (created idempotently by a one-off step) and Valkey DB 9, so it never touches the shared dev DB `invai`; a one-off `migrate` service runs bootstrap → migrate → reference seed from the backend image as the owner role. Because Postgres roles are cluster-wide, the app role's password in the `full` profile stays `invai` (the local value), so dev and tests keep working; say so in the README.
6. `invai-infra/scripts/full.sh up | seed | down` builds one image at a time, starts the profile, seeds `invai_full` with the demo seed from the host (`DATABASE_URL` pointed at `invai_full`, `SEED_OUTPUT_FILE=/tmp/invai-full-seed.json`, `REDIS_URL` on DB 9), and stops only the `full` services (infra and volumes stay). `down --purge` also drops `invai_full` and the built images.
7. **Proof:** on the seeded `full` stack, `cd invai-web && E2E_API=1 E2E_API_URL=http://localhost:3000 pnpm e2e e2e/api-golden-path.spec.ts --reporter=line` passes 13/13; web and floor answer 200 with the SPA on `/` and a deep link; imaging `/health` ok. If production mode blocks plain-http localhost (secure cookies, CSP), run api/worker with `NODE_ENV=production ALLOW_MOCKS=true` where it works and report exactly what needed development mode and why.
8. Disk: build one image at a time, prune your own dangling layers, report each image size; stop if free space drops below 6 GB (`df -h /`).

## Verification
- `docker build` of the four images; the AC2 checks; `bash -n invai-infra/scripts/full.sh`; `cd invai-infra && pnpm typecheck && pnpm lint`.
- The AC7 run. You hold the :3000, :5173, :5174, :8000 slot: check `lsof -iTCP:3000 -iTCP:5173 -iTCP:5174 -iTCP:8000 -sTCP:LISTEN -P` is empty before starting; never stop a process you didn't start.
- Record every PID and container you start; leave the `full` profile down at the end (`full.sh down`), the infra containers up, the dev DB untouched.

## Out of scope
- CI workflows, action pinning, image scanning (B-21 rest, B-08: wave 31), SST, any deploy or registry push, source code changes (a blocker goes to the report under "Blocked by other owners").

## Commit and report
- Commit only your paths, message ends with the attribution line. Don't push; only the tech lead pushes after the gate.
- Report ≤ 60 lines in `verify-and-report` format, with progress lines as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
