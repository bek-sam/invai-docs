---
name: release-checklist
description: Prepare an InvAI release for the owner's go-ahead. Pin one SHA per repo, prove all suites green on a fresh seed, review migrations for expand/contract safety, write the rollback plan, gather release notes, audits and SBOMs, then ask the owner. Use before any staging or production deploy, a pilot go-live, a v* tag, or when someone says "cut a release" or "ready to ship".
---

# Release checklist

The owner gets one page that proves exactly which code ships, that it works, how the schema changes, and how
to undo it, before anything is deployed.

## When to use
- Before every `deploy-to-environment` run (staging or production).
- Before a pilot shop starts on a new build.
- Before tagging `v*` in `invai-infra` (a tag push deploys production through `.github/workflows/deploy.yml`).

## Steps
1. **Open the record.** Copy `checklist.md` (this folder) to `invai-docs/ops/releases/<version>.md` (folder to
   be created; platform-sre owns `invai-docs/ops/**`). Version: `v<major>.<minor>.<patch>`, the next after the
   last tag (`git -C invai-infra tag --list 'v*' | sort -V | tail -1`; none exist yet, so the first is
   `v0.1.0` unless the owner says otherwise).
2. **Freeze the SHAs.** For each repo: `git -C <repo> fetch origin && git -C <repo> rev-parse origin/main`.
   Everything must be pushed; `git -C <repo> status --short` and `git -C <repo> log origin/main..HEAD` must be
   empty. Fill table §1. Check each repo's CI run for that SHA is green
   (`gh run list -R bek-sam/<repo> --branch main --limit 3`).
3. **Repo checks** at those SHAs, in every code repo (`verify-and-report` step 2 commands). Paste the last
   lines into §6.
4. **Golden path** on a fresh seed: `run-golden-path`, all three suites. Paste results.
5. **Reviews.** For every card merged since the last release, each required reviewer (the card's reviewer
   and co-reviewers) has a file `invai-docs/waves/<n>/reviews/T-<n>-<k>-<role>-r<round>.md`, and each role's
   latest round says `approve`: `ls invai-docs/waves/*/reviews/`. A missing file, or a latest round that
   isn't `approve`, stops the release.
6. **Security gates.**
   - No open High in `invai-docs/security/v1-review.md`.
   - `tenant-isolation-audit` ran on this release.
   - `dependency-and-container-audit` ran within 30 days (Amazon's scan interval) and this release's code was
     scanned; SBOMs generated (`pnpm sbom --sbom-format cyclonedx --prod` per Node repo).
7. **Migrations.** List them:
   `git -C invai-backend diff --name-only <last release SHA> <new SHA> -- drizzle/`. For each, fill §3 using
   `zero-downtime-migration`: expand before contract, `lock_timeout`, no table-rewriting DDL, backfills as
   batched jobs. `backend-foundation` reviews any migration. Note that `deploy.yml` doesn't run migrations yet
   (research 11 G3, backlog B-03): until it does, the migrate step is a manual prerequisite in
   `deploy-to-environment`.
8. **Contract compatibility.** `git -C invai-contracts diff <last> <new> -- src/` shows only additions (new
   fields optional, no removed or renamed procedures). The web SPA and floor PWA may run one version behind
   for hours (cached service worker).
9. **Rollback plan** (§4): previous SHAs, whether the previous app runs on the new schema, the data restore
   point, who decides and on which signal (SLO fast burn from `define-slo`, 5xx spike, post-deploy smoke
   failure).
10. **Release notes.** Ask the docs-writer for shop-facing notes in English and Spanish (`release-notes`).
    Internal notes list known issues from `invai-docs/build/qa-report.md`.
11. **Review.** security-reviewer reviews the record; the tech lead reviews it because it is release-affecting
    (`operating-system.md`, "Who reviews whom").
12. **Ask the owner.** `escalate-to-owner`: "Deploy <version> to <stage>?", options (deploy now / deploy at a
    set time / hold), recommendation, default "hold". Put the OI id at the top of the record. The owner then
    triggers `deploy-to-environment`.

## Rules
- MUST NOT deploy, tag `v*`, or push a tag. The owner does (`.claude/hooks/guard-bash.py` blocks deploy
  commands).
- MUST NOT ship a SHA whose CI is red or whose cards lack an approving review.
- MUST NOT ship a destructive (contract-phase) migration in the same release as the code that stops using the
  column.
- MUST NOT include real shop data or real keys in the record.
- MUST re-run steps 2–4 if any repo moves after the record is written.

## Done when
- `invai-docs/ops/releases/<version>.md` has every section filled, with commands and results as evidence.
- Every gate box is ticked, or the release is marked blocked with the reason.
- security-reviewer and tech lead reviews are recorded.
- The owner-inbox entry exists with a safe default.

## References
- `checklist.md` (this folder)
- `invai-docs/research/11-platform-scale-playbook.md` §4 (migrations, safe deploys, rollback), §10 gaps
- `invai-docs/research/12-security-quality-playbook.md` §6 (CI gate summary)
- `invai-docs/build/runbook.md` §7 (SST stages), `invai-infra/.github/workflows/deploy.yml`
- Related: `run-golden-path`, `zero-downtime-migration`, `deploy-to-environment`, `release-notes`
