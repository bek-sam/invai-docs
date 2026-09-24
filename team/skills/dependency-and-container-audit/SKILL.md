---
name: dependency-and-container-audit
description: Audit InvAI's supply chain — pnpm audit and pip-audit, pnpm safety settings and lockfiles, GitHub Actions pinned by SHA with least permissions, images pinned by digest and non-root, secret and image scans, SBOMs (research 12 gaps G15–G18), with Amazon's 30-day scan and 7/30-day fix clocks. Use monthly, before each release, when adding a dependency, and after an ecosystem incident.
---

# Dependency and container audit

Every repo's dependencies, CI actions and container images are scanned, pinned and owned, and every High or
Critical finding has a fix date inside Amazon's clock.

## When to use
- Every 30 days (Amazon requires a vulnerability scan every 30 days; research 12 correction 1).
- Before every release (a code scan per release), as part of `release-checklist`.
- A card adds or upgrades a dependency, a CI action or a base image.
- After an ecosystem incident (a worm like Shai-Hulud, a rewritten action tag): also rotate tokens (research
  12 §1.5).

## Steps
Run from the workspace root with `export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"`.
Write results to `invai-docs/security/dependency-audits/<YYYY-MM-DD>.md` (folder to be created,
security-reviewer owns it).

1. **Node dependencies** in each of
   `invai-contracts invai-ui invai-backend invai-web invai-floor invai-infra`:
   ```
   (cd <repo> && pnpm audit --prod --audit-level high)
   ```
   Record every High and Critical with package, path, fixed version. Moderate and Low go in the file too (S-32
   lists the known dev-only esbuild ones).
2. **Python dependencies** (imaging):
   ```
   cd invai-imaging
   uv export --no-dev --locked --no-hashes --format requirements-txt -o /tmp/imaging-req.txt
   uvx pip-audit -r /tmp/imaging-req.txt --disable-pip --no-deps; rm /tmp/imaging-req.txt
   ```
3. **pnpm and lockfile safety.** In each Node repo:
   - `git -C <repo> ls-files pnpm-lock.yaml` prints the file (committed), and CI installs with
     `--frozen-lockfile` (`grep -n "frozen-lockfile" <repo>/.github/workflows/*.yml`).
   - `pnpm-workspace.yaml` (backend, contracts, web, floor; ui and infra have none, so pnpm defaults apply)
     doesn't turn off `minimumReleaseAge`, `strictDepBuilds` or `blockExoticSubdeps`.
   - Each `allowBuilds` entry is reviewed (backend today: `esbuild`, `msgpackr-extract`).
   - Each `minimumReleaseAgeExclude` entry has a reason comment and is removed once older than the age limit
     (backend lists oRPC 1.15.4 and hono 4.13.9 with no comment today).
   - Imaging CI uses `uv sync --locked` (G20; today it runs `uv sync --all-groups`).
4. **G15, Actions pinned and scoped:**
   ```
   grep -rnE "uses: [^@]+@" invai-*/.github/workflows/*.yml | grep -vE "@[0-9a-f]{40}"   # unpinned actions
   grep -L "^permissions:" invai-*/.github/workflows/*.yml                              # no top-level permissions
   ```
   Target: every `uses:` is `@<40-char sha> # vX.Y.Z`, every workflow has `permissions: contents: read` at the
   top and widens per job only where needed. On 2026-09-24: 39 unpinned `uses:`, and the 6 app `ci.yml` files
   have no `permissions:` (only `invai-infra/.github/workflows/deploy.yml` has one).
5. **G16, images pinned by digest, no `:latest`:**
   ```
   grep -nE "^FROM |image:|docker run|COPY --from=" invai-*/Dockerfile invai-*/.github/workflows/*.yml invai-infra/local/docker-compose.yml | grep -v "@sha256:"
   ```
   Known on 2026-09-24: `ghcr.io/astral-sh/uv:latest` (imaging Dockerfile), `cgr.dev/chainguard/minio:latest`
   (backend CI), `quay.io/minio/minio:latest` (local compose), and unpinned `node:24-slim`, `nginx:alpine`,
   `python:3.13-slim`, `pgvector/pgvector:pg17`, `valkey/valkey:8`. Get a digest with
   `docker buildx imagetools inspect <image>:<tag>`.
6. **G17, containers not root:** `grep -L "^USER" invai-*/Dockerfile` must print nothing. Today all four
   (backend, web, floor, imaging) lack `USER`.
7. **G18, secrets, images, SBOM** (none run in CI yet; backlog B-08):
   - No `.env` tracked: `for r in invai-*; do git -C $r ls-files | grep -E '(^|/)\.env$'; done` prints
     nothing.
   - Secret scan of history with gitleaks (not installed locally; run its container pinned to a version you
     checked): `docker run --rm -v "$PWD/<repo>:/repo" ghcr.io/gitleaks/gitleaks:<version> git /repo`.
   - Image scan with Trivy (container, pinned version): build with `cd invai-infra && pnpm local:full`, then
     `docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:<version> image --severity HIGH,CRITICAL --exit-code 1 <image>`.
   - SBOM per Node repo: `(cd <repo> && pnpm sbom --sbom-format cyclonedx --prod > /tmp/<repo>-sbom.json)`;
     attach to the release (`release-checklist`), keep 12 months.
   - GitHub secret scanning and push protection on all 8 repos: a repo setting, so the owner turns it on
     (`escalate-to-owner`; `gh repo edit` is blocked by the hook).
8. **Set fix clocks.** From the day the finding is known: **Critical ≤ 7 days, High ≤ 30 days** (Amazon DPP,
   research 12 §1.5). Add each to `invai-docs/security/v1-review.md` with a due date and owner (the repo's
   owner role; CI and Dockerfiles are platform-sre). A Critical in a runtime dependency reachable from the API
   is also an `escalate-to-owner` entry the same day.
9. **Fix through cards,** never in the audit: the tech lead makes the card (backlog B-08 scanning in CI, B-21
   CI hardening). Re-run this audit after the fix and link the evidence.

## Rules
- MUST NOT turn off pnpm's `minimumReleaseAge`, `strictDepBuilds` or `blockExoticSubdeps`, or add
  `--no-frozen-lockfile`, to get a build through.
- MUST NOT pin by tag and call it pinned. Actions by full SHA, images by `@sha256:` digest.
- MUST NOT paste secrets found by a scan into any file or report. Record the path and commit only, and treat a
  real secret as an incident (`incident-response`: rotate first).
- MUST keep scanner containers themselves pinned to a checked version, not `:latest`.
- A new dependency needs: a reason, maintained upstream, compatible licence, no install script (or a reviewed
  `allowBuilds` entry), lockfile committed (research 12 §4).

## Done when
- The dated audit file lists, per repo: audit results, G15–G18 status with counts, pnpm/uv safety checks, and
  SBOM paths.
- Every High and Critical has an owner and a due date inside 7/30 days in `security/v1-review.md`.
- Anything needing repo settings or spend is in `owner-inbox.md`.

## References
- `invai-docs/research/12-security-quality-playbook.md` §1.5 (supply chain), §6 (CI gate), §7 G15–G20
- `invai-docs/security/v1-review.md` (S-32 and the SP-API list)
- `invai-docs/waves/backlog.md` (B-08, B-21)
- Each repo's `pnpm-workspace.yaml`, `Dockerfile`, `.github/workflows/`
