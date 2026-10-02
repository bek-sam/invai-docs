# Lesson 13.1 — Machine setup: Node, pnpm, Docker, Postgres, Valkey, MinIO

## 1. In one sentence
Before writing any code you'll stand up the four local services every InvAI repo
assumes are already running: Postgres (the database), Valkey (the job queue's
backing store), MinIO (S3-compatible file storage) and the right Node/pnpm versions —
in a tiny practice folder next to, but separate from, the real `invai-infra`.

## 2. Why it exists
Every later lesson in this track says "run `pnpm install`" or "connect to Postgres"
and assumes those words already mean something on your machine. If you skip this step
and hit a wall in lesson 3 ("connection refused" to a database that doesn't exist),
you'll be debugging two problems at once — your new code, and infrastructure you
never actually set up. InvAI itself treats this as separate, foundational work: one
real repo, `invai-infra`, whose entire job is "make local services exist," owned by
the `platform-sre` role, so every other repo gets to assume they're there.

The reason it's **Docker Compose** and not "install Postgres with Homebrew" is
portability: the same compose file describes a stack a teammate's machine, CI, and
(with different images) production can all start from. You'll feel the benefit the
first time you blow away a database by mistake and get it back with one command,
instead of reinstalling anything.

## 3. How it works

### Step 1 — Node and pnpm
InvAI pins Node 24 and pnpm 12.6 (`CLAUDE.md`, "Environment"). Check what you have,
install what's missing:
```bash
node -v          # want v24.x — if you see v22.x, that's the wrong (system) node
corepack enable   # or: npm install -g pnpm@12.6
pnpm -v
```
If your machine's `/usr/local/bin/node` is an older system Node (common on macOS),
don't fight it — just make sure the right one wins on `PATH` for every command you
run in these lessons:
```bash
export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
```

### Step 2 — Docker (via OrbStack on macOS)
Install [OrbStack](https://orbstack.dev) (a lighter Docker Desktop replacement) or
Docker Desktop itself. Either way you end up with a working `docker` and
`docker compose` command:
```bash
docker --version
docker compose version
```
If containers or ports ever hang mid-course (it happens — see "Common mistakes"
below), the fix the real team uses is `orb stop && orb start`, then bring your compose
stack back up. Your data volumes survive a restart.

### Step 3 — a practice compose file
Make a scratch folder *outside* `invai-infra` — you're learning the pattern, not
editing the real stack:
```bash
mkdir -p ~/invai-from-zero/infra && cd ~/invai-from-zero/infra
```
Write `docker-compose.yml`:
```yaml
name: fromzero
services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_USER: fz
      POSTGRES_PASSWORD: fz
      POSTGRES_DB: fz
    ports: ["5433:5432"]       # not 5432 — leave InvAI's real Postgres alone
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fz -d fz"]
      interval: 5s
      timeout: 5s
      retries: 10

  valkey:
    image: valkey/valkey:8
    command: ["valkey-server", "--appendonly", "yes"]
    ports: ["6380:6379"]       # not 6379

  minio:
    image: quay.io/minio/minio:latest
    command: server /data --console-address ":9002"
    environment:
      MINIO_ROOT_USER: fz
      MINIO_ROOT_PASSWORD: fz-secret12
    ports: ["9002:9000", "9003:9001"]
```
Every port is offset from InvAI's real ports (`5432`, `6379`, `9000`/`9001`) on
purpose — this stack runs *alongside* the real one without a collision.

### Step 4 — bring it up and look at it
```bash
cd ~/invai-from-zero/infra
docker compose up -d
docker compose ps                         # all three should say "healthy" or "running"
docker exec -it fromzero-postgres-1 psql -U fz -d fz -c "select version();"
docker exec -it fromzero-valkey-1 valkey-cli ping          # -> PONG
```
Open `http://localhost:9003` in a browser and log into the MinIO console with
`fz` / `fz-secret12` — this is the same web UI InvAI's real MinIO (`:9001`) uses.

## 4. In our code
- `invai-infra/local/docker-compose.yml` — the real stack: `postgres`
  (`pgvector/pgvector:pg17`), `valkey`, `minio` (from `quay.io/minio/minio`, because
  Docker Hub's `minio/minio` image was pulled — a real gotcha worth knowing before you
  copy a compose file from an older tutorial), a one-shot `minio-init` service that
  creates the bucket, and `mailpit` for catching emails.
- `invai-infra/local/init.sql:1-4` — `CREATE ROLE invai_app LOGIN PASSWORD 'invai'`:
  the app connects as a *non-owner* role so Postgres Row-Level Security (lesson 13.4)
  actually applies to it. You'll do the same thing in lesson 13.4.
- `CLAUDE.md` ("Environment") — the real Node/pnpm pin and the exact `PATH` export
  this lesson borrowed, plus the real port table (api 3000, imaging 8000, web 5173,
  floor 5174) you'll meet again in later lessons.
- `invai-infra/README.md` and `invai-infra/scripts/dev.sh` — the real one-command
  runner (`pnpm dev:all`) that starts infra, migrates, seeds, then every app with
  prefixed logs. You're rebuilding a tiny slice of what this script automates.

## 5. What it uses
- **Docker Compose** — declares services as code, so "what's running locally" is a
  file in version control, not tribal knowledge. Module 03.5 covers why this over a
  manually-installed Postgres.
- **OrbStack** — a lighter-weight Docker runtime for macOS; InvAI's own lesson log
  flags that it can hang under heavy use (lesson 13.13 covers the real incident).
- **pgvector/pgvector** image — plain Postgres 17 plus the `vector` extension InvAI
  doesn't strictly need yet in this mini-build, but matches the real image so later
  lessons' SQL behaves identically.

## 6. Try it yourself
1. Stop just the Postgres container (`docker compose stop postgres`), confirm `psql`
   now fails to connect, then `docker compose start postgres` and confirm it's back —
   with your data intact. This is the exact "it hung, don't panic" muscle you'll need
   for real InvAI development.
2. `docker compose down` (no `-v`) and back `up -d` — check your database's one
   test query from Step 4 still returns the Postgres version, proving the named volume
   survived a full container teardown.
3. Open the real `invai-infra/local/docker-compose.yml` and compare the `minio` image
   line to your practice file. Why might a two-year-old MinIO tutorial give you a
   `docker pull` that fails outright?

## 7. Common mistakes
- Using InvAI's real ports (5432/6379/9000) for your practice stack. If InvAI's own
  services are running, you'll get a "port already in use" error, or worse, you'll
  accidentally connect your practice code to the *real* local database. This course's
  compose file uses offset ports specifically to avoid that.
- Forgetting the `PATH` export and silently running the wrong Node. `CLAUDE.md` calls
  this out directly: the system Node on this class of machine is version 22, and
  InvAI's code (and this course's code) is written against Node 24 behavior.
- Treating a hung `docker` command as something to debug deeply. The real team's own
  lesson is blunter: when Docker or local ports hang, `orb stop && orb start` first,
  then bring the compose stack back up — don't spend 20 minutes investigating a
  transient OrbStack issue before trying the restart.

## 8. Check yourself
<details>
<summary>1. Why does the app connect to Postgres as <code>invai_app</code> rather
than as the database owner role?</summary>

Because Row-Level Security (RLS) policies are enforced against non-owner roles. A
table owner (or a role with BYPASSRLS) can see every row regardless of policy, which
would silently defeat the tenant isolation lesson 13.4 builds. Connecting as a
limited role is what makes RLS actually bite.
</details>

<details>
<summary>2. Your compose file uses port 5433 for Postgres instead of 5432. What
breaks if you forget this and InvAI's real stack is also running?</summary>

Either your `docker compose up` fails outright (port already bound), or — more
dangerously — if you reuse the same port number thinking it's isolated, you could
end up pointing your new, half-built code at the real local database that has real
(if fake/demo) data other lessons and the real team depend on.
</details>

<details>
<summary>3. Why is "the stack is defined in a compose file" better than "I installed
Postgres with Homebrew and remember how"?</summary>

Reproducibility: anyone (a teammate, CI, future-you on a new machine) gets the exact
same versions and config by running one command, instead of reconstructing
installation steps from memory. It's also disposable — `docker compose down -v` gets
you back to zero without uninstalling anything from your actual machine.
</details>

## 9. Words to know
- **Docker Compose** — a tool that starts a group of containers (here: Postgres,
  Valkey, MinIO) from one YAML file describing each service's image, ports and
  settings.
- **Container** — a lightweight, isolated process running from a packaged image;
  InvAI's local services all run as containers rather than installed-on-the-metal
  software.
- **Volume** — a Docker-managed storage location that survives a container being
  stopped, restarted, or even removed and recreated (as long as you don't pass `-v`
  to `docker compose down`).
- **Valkey** — an open-source, Redis-compatible key-value store; InvAI uses it as the
  backing store for BullMQ (lesson 13.6) and rate limiting.
- **MinIO** — a self-hosted, S3-API-compatible object storage server; code written
  against it should work unchanged against real AWS S3.
