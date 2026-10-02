# Lesson 3.5 — Python/pyvips for pixels, Docker/OrbStack locally, SST on AWS, GitHub Actions

## 1. In one sentence
The one non-TypeScript repo, `invai-imaging`, is Python + FastAPI + pyvips because image work
(nesting hundreds of designs onto a gang sheet, composing a 22-inch-wide, 240-inch-long print
file) needs a real native image library, not a JavaScript one; everything runs locally through
Docker via OrbStack, deploys (when the owner approves it) through SST onto AWS, and every repo's
checks run on GitHub Actions with container images pinned by digest, not by a mutable tag.

## 2. Why it exists
This closes out module 03 with the two layers that aren't "a library you import" so much as
"the ground everything else runs on": the one place the stack steps outside TypeScript, and the
infrastructure that makes "it works on my machine" also work in CI and (eventually) in
production.

## 3. How it works

### Why Python + FastAPI + pyvips for imaging, not a Node library
`invai-docs/research/06-tools-backend.md:163-183` compares **FastAPI** (9/10) against Litestar
(7.5) and Flask (5.5) — FastAPI wins on ecosystem size and Pydantic v2 validation, with the one
real caveat noted: "CPU-bound renders need plain `def` handlers or a process pool, not async,"
because gang-sheet composition is genuinely CPU-heavy work, not I/O-bound work async is built
for.

The library doing the actual pixel work is **pyvips** (`invai-imaging/pyproject.toml:9` —
`"pyvips[binary]>=3.2.0"`), a Python binding for libvips — a streaming image library that
processes images region-by-region instead of loading a whole bitmap into memory at once. That
matters concretely at InvAI's actual sizes: `invai-imaging/app/config.py:39-40`'s own comment
does the math — "22 x 240in at 300 DPI x 1.2 is about 570M pixels" for one gang sheet — a naive
"load the whole image into an array" approach (the kind a plain Node `sharp`/`canvas` script
might default to without care) would risk exactly the peak-RSS blowouts
`imaging-change-with-budget`'s skill exists to prevent. Nesting itself —
`invai-imaging/app/nesting.py:1-11` — runs MaxRects (from the `rectpack` library,
`invai-imaging/pyproject.toml:11` — `"rectpack>=0.2.2"`) with a custom placement rule, because
"a design's footprint is not a plain rectangle to rotate: the order label strip always sits
*under* the placed design."

The render path itself is a deliberate split, per the research's recommendation
(`06-tools-backend.md:177-183`): short renders are called **over plain HTTP from the BullMQ
worker** (simple, one queue system, `invai-backend/src/integrations/imaging/client.ts`), while
genuinely long renders would run through a **BullMQ Python worker** instead (BullMQ ships an
official Python client) — avoiding HTTP timeout limits for the slow case without adding a
second queue system. Celery and Dramatiq were explicitly ruled out: "a second broker and a
second retry/monitoring system on top of BullMQ" for no real gain.

### Docker via OrbStack — why a container layer at all, locally
Every local service — Postgres, Valkey, MinIO, Mailpit — runs as a pinned container
(`invai-infra/local/docker-compose.yml:9,25,35` — `pgvector/pgvector:pg17`,
`valkey/valkey:8`, `quay.io/minio/minio:latest`), so every developer (or agent) gets the exact
same service versions without installing any of them natively. **OrbStack** is the Docker
runtime on this machine specifically (not Docker Desktop) — `CLAUDE.md`'s Environment section
notes the practical consequence: "If `docker` commands or local ports hang, run
`orb stop && orb start`... Data volumes survive." This is a known, named failure mode, not a
hypothetical one.

### SST on AWS — infrastructure as TypeScript, not YAML or HCL
`invai-docs/research/05-tools-hosting.md:284-297` compares **SST v3** against Terraform,
Pulumi and AWS CDK for "best for a solo TypeScript developer on AWS": SST's components
(`Vpc`, `Cluster`/`Service` on Fargate, `Postgres` on RDS, `Redis` on ElastiCache, `Bucket`) are
pre-built and opinionated, written in the same language as the rest of the stack, with state
kept in the project's own S3 bucket rather than a paid vendor backend. `invai-infra/sst.config.ts`
is itself careful about the version mismatch risk `read-before-change` warns about everywhere
else: its own top comment says to check `.sst/platform/src/components` (the generated,
installed component sources) "before changing component options rather than guessing from
docs written for other SST versions" — SST 4.17.1 is newer than most written guidance. As of
this writing nothing has actually been deployed (`sst.config.ts`'s own comment, "T-24-1") —
module 11 covers environments and the deploy gate in full; this lesson only covers the tool
choice.

### GitHub Actions — pinned by digest, not by tag
Every repo's `.github/workflows/ci.yml` runs its own checks (`invai-backend/.github/workflows/ci.yml:1-6`
— on push to `main`, on PR, and on manual dispatch). Two details worth noticing:
1. **Service containers are pinned by image digest**, not a mutable tag —
   `invai-backend/.github/workflows/ci.yml:23` —
   `pgvector/pgvector@sha256:cf134a767f4...` (`# pg17` as a human-readable comment) — so a CI
   run today and a CI run in six months use the *exact* same bytes, not "whatever `pg17` tag
   points to by then."
2. **Third-party actions are pinned by commit SHA**, not a version tag —
   `invai-backend/.github/workflows/ci.yml:60` —
   `actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4` — the `# v4` is a comment
   for humans; the SHA is what actually runs, so a compromised or re-tagged release of a
   third-party action can't silently change what CI executes. This is exactly the kind of
   supply-chain control `dependency-and-container-audit`'s skill checks for across every repo.

## 4. In our code
- `invai-imaging/app/config.py:39-40` — the pixel-cap comment with the actual gang-sheet math.
- `invai-imaging/app/nesting.py:1-11` — the MaxRects-plus-custom-placement docstring explaining
  why a design's footprint isn't a plain rectangle.
- `invai-imaging/pyproject.toml:9-11` — pinned `pyvips[binary]`, `pillow`, `rectpack` versions.
- `invai-infra/local/docker-compose.yml:9,25,35` — the three pinned local service images.
- `invai-infra/sst.config.ts` (top comment) — the version-check instruction and the stage list
  (`production`, `staging`, `demo`).
- `invai-backend/.github/workflows/ci.yml:23,60` — a digest-pinned service container and a
  SHA-pinned third-party action, side by side.

## 5. What it uses
- **Python 3.13, FastAPI, pyvips, rectpack, Pillow** — the one non-TypeScript repo, chosen
  specifically for native, streaming image processing at print-file sizes a JS library isn't
  built for.
- **Docker, via OrbStack** — local service containerization; OrbStack is this machine's
  specific Docker runtime, with its own documented recovery step when it hangs.
- **SST v3 on AWS** — infrastructure as TypeScript, components pre-built for Fargate/RDS/
  ElastiCache/S3, nothing deployed yet as of this writing.
- **GitHub Actions** — CI for every repo, with containers pinned by digest and third-party
  actions pinned by commit SHA.

## 6. Try it yourself
1. Run `cd invai-imaging && uv run pytest 2>&1 | tail -n 20` (per `CLAUDE.md`'s Python section)
   and confirm it passes against the real `uv`-managed environment, not a system Python.
2. Open `invai-infra/local/docker-compose.yml` and find the MinIO image line; confirm it reads
   `quay.io/minio/minio`, not `minio/minio` — and recall from lesson 3.3 why.
3. Open any repo's `.github/workflows/ci.yml` and find one `uses:` line; copy the SHA into
   GitHub's web UI (`github.com/<org>/<action-repo>/commit/<sha>`) and confirm it resolves to a
   real commit — this is what "pinned by digest, not tag" actually buys you.

## 7. Common mistakes
- Writing imaging code that loads a full gang-sheet-sized image into memory "to keep it
  simple." At InvAI's real sizes (570M pixels for one sheet) this is exactly the peak-RSS risk
  `imaging-change-with-budget` exists to catch — pyvips's whole value is *not* doing this.
- Treating a hung local Docker port as an application bug before trying the documented fix
  (`orb stop && orb start`, then bring the compose stack back up) — this is a named, expected
  failure mode on this machine, not a signal something in the code broke.
- Editing an SST component option by guessing from AWS or Pulumi docs written for a different
  SST version. `sst.config.ts`'s own comment is explicit: check the installed
  `.sst/platform/src/components` sources first.

## 8. Check yourself
<details>
<summary>1. Why does pyvips matter specifically for a 22×240-inch gang sheet, more than it
would for a small thumbnail?</summary>

At that size (about 570M pixels at 300 DPI), a library that loads the whole image into memory
at once risks a large peak memory spike; pyvips streams the image region-by-region instead,
keeping memory bounded regardless of the final sheet's size.
</details>

<details>
<summary>2. What's the practical difference between pinning a GitHub Actions service container
by tag (e.g. `pg17`) versus by digest (`@sha256:...`)?</summary>

A tag can silently point to different bytes over time (a new `pg17` patch release); a digest
always refers to the exact same image, so CI behavior can't drift out from under you without
someone deliberately updating the pinned digest.
</details>

<details>
<summary>3. Has InvAI been deployed to AWS as of this course being written?</summary>

No — `sst.config.ts`'s own comment notes nothing has been deployed yet; SST is typechecked and
ready, but every `sst deploy` requires the owner's explicit go-ahead per stage (module 11
covers this gate).
</details>

## 9. Words to know
- **pyvips / libvips** — a streaming image-processing library; processes images in regions
  rather than loading a full bitmap into memory, important at InvAI's large gang-sheet sizes.
- **MaxRects** — a rectangle-packing algorithm (via the `rectpack` library) used to nest
  designs onto a gang sheet efficiently.
- **OrbStack** — the Docker-compatible container runtime used on this machine, with its own
  known hang/recovery behavior distinct from Docker Desktop.
- **Pin by digest / pin by SHA** — referencing an exact, immutable image or commit (a
  cryptographic hash) instead of a mutable tag or version label, so what runs can't silently
  change underneath you.
- **SST (v3)** — infrastructure-as-code written in TypeScript, with pre-built components for
  common AWS resources (Fargate services, RDS, ElastiCache, S3, CloudFront).
