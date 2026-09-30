# Review of T-23-7 (round 1)

- Reviewer: security-reviewer on Opus 5.5
- Author: platform-sre on Sonnet
- Verdict: approve

## Scope of this review
Co-review under decision 0019 ("CI permissions"): least privilege, action pinning, no
`pull_request_target`, no secret expansion into `run:`, no script injection from
`github.event.*`, `persist-credentials`, artifact hygiene, service-image pinning, no
deploy/aws steps. Not re-reviewed here (left to `reviewer`): AC1/AC2 functional coverage,
`actionlint`, ownership/scope beyond the security lens.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C <repo> show --stat <sha>` for all 7 commits | Matches the card's owned paths: `.github/workflows/**` in contracts/ui/backend/web/floor/imaging, `invai-infra/scripts/ci/run-e2e.sh` only (invai-infra `9fe0c55` stat: 1 file). `invai-infra/.github/workflows/deploy.yml` untouched (not in the commit's file list; confirmed by reading it — still tag-pinned `@v4`, still has the 6 `secrets.*_DEPLOY_KEY` `ssh-key:` lines, out of this card's scope). |
| `grep -rn "uses:" invai-*/.github/workflows/*.yml` | Every action in every touched `ci.yml`/`e2e.yml` is `owner/repo@<40-hex-sha> # vX` (checkout, pnpm/action-setup, setup-node, astral-sh/setup-uv, upload-artifact). Only `invai-infra/deploy.yml` (untouched) still uses tag refs. |
| `gh api repos/actions/checkout/git/refs/tags/v4 --jq .object.sha` → `11d5960a326750d5838078e36cf38b85af677262` | Matches every `actions/checkout` pin used. |
| `gh api repos/pnpm/action-setup/tags --jq '.[]|select(.name=="v4")|.commit.sha'` → `b906affcce14559ad1aafd4ab0e942779e9f58b1` | Matches every `pnpm/action-setup` pin used. |
| `gh api repos/actions/setup-node/tags --jq '.[]|select(.name=="v4")|.commit.sha'` → `49933ea5288caeca8642d1e84afbd3f7d6820020` | Matches every `actions/setup-node` pin used. |
| `gh api repos/actions/upload-artifact/tags --jq '.[]|select(.name=="v4")|.commit.sha'` → `ea165f8d65b6e75b540449e92b4886f43607fa02` | Matches the pin in backend/web/floor `e2e.yml`. |
| `gh api .../astral-sh/setup-uv/git/refs/tags/v6` (annotated tag) → dereferenced via `git/tags/<obj>` → `d0cc045d04ccac9d8b7881df0226f9e82c39688e` | Matches the pin in backend/web/floor `e2e.yml` and imaging `ci.yml`. Note: `setup-uv` is now at v10; v6 still resolves correctly but is several majors behind — a freshness note for `dependency-and-container-audit`, not a pinning defect. |
| `grep -rn "permissions:" invai-*/.github/workflows/*.yml` | Exactly one top-level `permissions:\n  contents: read` block per touched workflow, no job-level widening anywhere. |
| `grep -rn "pull_request_target" invai-*/.github/workflows/*.yml` | No hits. |
| `grep -rn "secrets\." invai-*/.github/workflows/*.yml` | Hits only in the untouched, out-of-scope `invai-infra/deploy.yml` (the 6 `ssh-key: ${{ secrets.*_DEPLOY_KEY }}` lines). None in any touched `ci.yml`/`e2e.yml`. |
| `grep -rn "github\.event\|github\.head_ref\|github\.actor" invai-*/.github/workflows/*.yml` | No hits in touched files. (The **old** `invai-web`/`invai-backend` `ci.yml` used `ref: ${{ github.head_ref \|\| github.ref_name }}` as a checkout `with:` input for the sibling repo — not a `run:` shell-injection vector, but still a removed pattern; this PR replaces it with a fixed `ref: main`, which is strictly safer.) |
| `grep -rn "persist-credentials" invai-*/.github/workflows/*.yml` | No hits anywhere — see finding S-41. |
| Read full `ci.yml`/`e2e.yml` in all 7 repos | Service images pinned by digest: `pgvector/pgvector@sha256:...`, `valkey/valkey@sha256:...`; MinIO started via `docker run` also pinned by digest (`cgr.dev/chainguard/minio@sha256:...`), replacing the prior `:latest`. No `aws`/`sst deploy` step in any touched workflow. |
| `gh api repos/bek-sam/<repo> --jq .private` for all 7 repos | All `true` — the author's "all repos are private" claim checks out. |
| Read `invai-infra/scripts/ci/run-e2e.sh` (`9fe0c55`) and `invai-backend/src/db/seed/index.ts:193-194` | Confirms the seed script prints the demo password, PINs and the fresh station token to stdout, captured into `.ci-e2e-logs/seed.log` by the script's `tee`, uploaded by `actions/upload-artifact` only `if: failure()` — see finding S-40 (judged non-blocking). |
| Diff old vs new `invai-web`/`invai-backend` `ci.yml` (`git show <sha> -- .github/workflows/ci.yml`) | Confirms the removed code: two-step branch-then-main `checkout` fallback with `ssh-key: ${{ secrets.CONTRACTS_DEPLOY_KEY }}` / `UI_DEPLOY_KEY`, replaced by a single plain `ref: main` checkout with no `ssh-key:`/token, which fails closed (401/404) until the sibling repo is made readable — matches the author's report and this card's AC3 ("no secrets... added"). |

## Acceptance criteria (AC3, the security-relevant one)
| # | Met? | Evidence |
|---|---|---|
| AC3 — every action pinned by full SHA | Yes | All `uses:` lines in touched workflows are 40-hex SHAs with a version comment; 5 distinct pins independently verified against upstream tags above. |
| AC3 — top-level `permissions: contents: read`, nothing broader | Yes | One top-level block per workflow, no job/step overrides, confirmed by grep and by reading every file. |
| AC3 — no secrets | Yes (with a caveat) | No `secrets.*` in any touched workflow; the sibling checkouts are honestly left broken rather than given a secret, as the commit messages say. Caveat: CI-only **dummy** values (`ci-only-secret-32-chars-minimum-xxxx`, a static all-zero `FIELD_ENCRYPTION_KEY`, `invai`/`invai-secret` MinIO creds) are hardcoded as plain `env:` — these are not GitHub secrets, are documented as dummies, and only ever touch a same-job, same-run, torn-down MinIO/Postgres, so this is correct, not a finding. |
| AC3 — no deploy or `aws` steps | Yes | None in any touched workflow; `deploy.yml` (the only file with `aws-actions/configure-aws-credentials` and `sst deploy`) is untouched. |
| AC3 — no `pull_request_target` | Yes | No hits anywhere. |

## Blocking findings
None.

## Findings recorded (non-blocking, filed in `security/v1-review.md`)
- **S-40** (Low, CI secrets hygiene, owner platform-sre): the seed script's stdout — including
  a freshly-issued, cleartext station token — lands in `.ci-e2e-logs/seed.log`, which
  `actions/upload-artifact` uploads whenever the E2E job fails. Judged non-blocking: the token
  is random per run and scoped to a Postgres service container destroyed at job end (no live
  target to use it against once the artifact exists), the password/PINs it also prints are
  already public in `CLAUDE.md`, and the repos are private. Still worth a follow-up (redact the
  seed's secret-shaped lines before `tee`, or add `--quiet-secrets` to the seed script for CI)
  before this log-then-upload-on-failure pattern gets reused somewhere less ephemeral.
- **S-41** (Low, CI hardening, owner platform-sre): no `actions/checkout` step across the 6
  touched repos sets `persist-credentials: false`. Impact is bounded today because every
  workflow's only `permissions:` block is `contents: read`, so a token read out of git config by
  a compromised install script could only re-read repo contents — but it's a one-line, no-risk
  fix worth doing now, before CI runs untrusted `pnpm install` scripts as routine.

Neither finding blocks this card: both are pre-existing-pattern hardening gaps with a bounded,
already-mitigated (S-41) or already-expired-by-teardown (S-40) blast radius, not a control this
card removed or weakened. Both are recorded with an owner for a future card.

## Recommendation for the owner: sibling-repo read access (owner step, not to be built here)
The card correctly refuses to add a secret to get the sibling checkouts working (AC3), leaving
that as an owner decision. Options, in order of preference:

1. **A GitHub App, installed on exactly these 7 repos with `Contents: Read` only** (no other
   permission), minting a short-lived (~1 hour) installation token per job via the official
   `actions/create-github-app-token` action. Two long-lived secrets total (`APP_ID`,
   `APP_PRIVATE_KEY`), reused unchanged across every consuming workflow; every token it mints
   auto-expires within the hour and the whole credential can be killed in one action (uninstall
   the App) if it ever leaks. This is the safest option and GitHub's own recommended replacement
   for machine-to-machine PATs/deploy keys.
2. **A single fine-grained PAT, scoped to `Contents: Read-only` on exactly these 7 repos, with
   the shortest practical expiry (90 days) and a calendar reminder to rotate.** Simpler to set up
   than an App (one secret value, no extra action), but it's a static, longer-lived credential
   with no automatic expiry inside its window — acceptable as a pragmatic first step if the App
   is more setup than the owner wants right now.
3. **Not recommended: per-repo SSH deploy keys** (the pattern this card removed). Each source repo
   needs its own keypair, and because up to 5 sibling repos must be readable from each of
   `backend`/`web`/`floor`'s `e2e.yml`, the private-key material ends up duplicated across
   multiple repos' secret stores with no shared revocation point — more keys to leak, rotate and
   track than either option above, for the same read-only outcome.

Whichever is chosen, the token/key must be scoped to **read-only, these 7 repos only** — never
a classic account-wide PAT — and this is an `owner-inbox.md` / `escalate-to-owner` item for
platform-sre, not something to add here.

## Checks
- [x] Only owned paths changed (`git show --stat` per repo, listed above)
- [x] Nothing outside scope (`deploy.yml` untouched; no `.github/workflows` changes beyond the
      card's list; `invai-infra` touches only `scripts/ci/run-e2e.sh`, not `scripts/gate/**`)
- [x] No control was weakened to fix anything — the sibling-checkout gap was left honestly
      broken rather than patched with a secret or a permissive fallback
- [x] Least privilege: `permissions: contents: read` top-level, no widening, no job needs more
- [x] Every third-party action verified pinned by full SHA against its tag (5 distinct pins
      checked with `gh api`)
- [x] No `pull_request_target`, no `secrets.` in `run:`/consuming steps outside the untouched
      deploy workflow, no `github.event.*`/`github.head_ref` interpolated into a `run:` block
- [x] Service images pinned by digest (Postgres, Valkey, MinIO)
- [x] No deploy/`aws` steps introduced

## Optional notes (not blocking)
- `astral-sh/setup-uv` is pinned correctly to v6 but that major is several versions behind
  upstream (now v10) — flag for the next `dependency-and-container-audit`, not this review.
- The dummy CI env values (`FIELD_ENCRYPTION_KEY: ci:AAAA...`, `BETTER_AUTH_SECRET:
  ci-only-secret-...`) are clearly labeled as such in comments; consider a lint/grep in a future
  card that fails CI if a real-shaped (high-entropy, unlabeled) secret ever replaces one of these
  placeholders by accident.
