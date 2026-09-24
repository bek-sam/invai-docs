# Release <version> (<YYYY-MM-DD>)

- Target stage: staging / production
- Prepared by: platform-sre. Reviewed by: tech-lead (release-affecting), security-reviewer
- Owner go-ahead: OI-<n> (status: …)

## 1. What ships (one SHA per repo, all on `main`, all pushed)
| Repo | SHA | Last release SHA | Commits since | CI green at this SHA? |
|---|---|---|---|---|
| invai-contracts | | | | |
| invai-ui | | | | |
| invai-backend | | | | |
| invai-imaging | | | | |
| invai-web | | | | |
| invai-floor | | | | |
| invai-infra | | | | |
| invai-docs | | | | n/a |

## 2. Gates
- [ ] Repo checks green in all 7 code repos at these SHAs (commands and results below)
- [ ] `run-golden-path` on a fresh seed: API 13/13, browser 13/13, screens smoke, floor suite
- [ ] Every card in the release has, from each required reviewer, a latest review file (`invai-docs/waves/<n>/reviews/T-<n>-<k>-<role>-r<round>.md`) that says `approve`
- [ ] No open High finding in `security/v1-review.md`; Criticals/Highs from the last audit inside 7/30 days
- [ ] `tenant-isolation-audit` ran this release (date: …)
- [ ] `dependency-and-container-audit` ran within 30 days (date: …); SBOMs attached
- [ ] Contracts are additive only (web and floor may be one version behind the API for hours)
- [ ] Mocks still work with no keys (the golden path proves it)

## 3. Migrations
| File (`invai-backend/drizzle/`) | What it does | Expand or contract? | Locks a hot table? | Backfill? | Reviewed by |
|---|---|---|---|---|---|
- [ ] Old code works on the new schema (expand first; contract only a release later)
- [ ] No `ALTER COLUMN TYPE`, no `SET NOT NULL` without a validated check, no non-concurrent index on big tables, no `DROP COLUMN` still read by code
- [ ] Migration runs as its own step before the app rolls out (today `deploy.yml` has no migrate step: research 11 G3, backlog B-03)

## 4. Rollback plan
- App: redeploy the previous release's SHAs / images: …
- Schema: this release's migrations are additive, so the previous app runs on the new schema: yes / no (if no, the plan is: …)
- Data: RDS point-in-time restore target time if data is damaged (see `backup-restore-drill`): …
- Who decides to roll back, and the signal: SLO fast burn, 5xx spike, golden-path smoke failure after deploy

## 5. Release notes
- Shop-facing notes (en/es) by docs-writer (`release-notes`): link …
- Internal changes and known issues: …

## 6. Evidence
| Command | Result |
|---|---|
