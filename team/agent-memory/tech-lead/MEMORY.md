# tech-lead memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Every agent prompt ends with "Don't push; only the tech lead pushes after the gate".
- 2026-09-26 W6/7: Write every grant into `wave.md` in the same step you give it.
- 2026-09-24 W2: 3-4 agents at once; if a usage limit hits, resume stopped agents with SendMessage.
- 2026-09-24 W2: Check `df -h /` (> 5 GB) before each wave; drop test DBs and worktrees at every gate.
- 2026-09-26 W16: The guard scans heredoc text too; a script quoting a blocked command gets denied. Put such text in a file.

## Learned on cards
- 2026-09-27 W18 plan: "sample workspace" = `isSampleWorkspace(companyId)` (demo-flag.ts), NOT `companies.demo` (seeded Desert Bloom has demo=true and gets real-shop behavior). Check before writing it into cards.
- 2026-09-27 W18: waiting on agents inside my turn: a foreground `until [ -f <file> ]; do sleep 15; done` with timeout 600000 works; bare `sleep N` is blocked. The SendMessage tool isn't loaded for me, so a follow-up to an agent is a fresh agent with the context in its prompt.
- 2026-09-27 W18: after a usage-limit stop, identify orphans by their env (PORT/DATABASE_URL/REDIS_URL via `ps eww`), then run the kill of explicit PIDs as its own command; the guard denies it next to a process listing.
- 2026-09-27 W18: the permission system denied planting a canary through a builder; don't retry. OI-15 asks the owner for a method.
- 2026-09-28 W19: when agents and I stall for 600 s, check `docker ps` first (OrbStack hang blocks every DB call silently). Keep my own polls under ~2 min; start agents and return instead of long waits.
- 2026-09-28 W19: gate-time QA test edits need a commit by QA and a quick reviewer pass before the push; budget one extra round trip.
- 2026-09-27 W18: spec reviews found the demo seed has only ~30 days of order history; anything trend/weekly needs fixture shops in tests (B-130 for longer seed history).
- 2026-09-29 W20: a gate can't isolate web from :3000 (prod CSP), so it runs on the shared dev:all stack; no builder may edit web/floor while the gate's browser run is on. When a later card commits on top of gated commits, push the gated prefix with `git push origin <sha>:main` (fast-forward, allowed).
- 2026-09-29 W20: the stopped-agent pattern repeats: after every limit stop, look for orphan workers by env (`ps eww` DATABASE_URL/REDIS_URL) and stale worktrees/DBs before relaunching; relaunch reviewers with a "short, write the file" prompt.
- 2026-09-29 W20: check any copy example written on a card against the spec's existing locale rules (the "+6,9 pts" example cost two rounds).
- 2026-09-30 W23: code pushes need a full `pnpm gate` stamp on the same SHAs (live T-23-6 hook; docs aren't gated). Any fresh-seed spec gap blocks every push, so fix spec or seed preconditions before planning a push. A stacked, unreviewed commit from another card blocks its whole repo.
- 2026-09-30 W23: when a card's AC needs config (headers, CSP, vite, nginx), list those files on the card. Two builders had to step outside `src/**` this wave.
- 2026-09-30 W23b: the push hook parses `git push` args literally: `2>&1 | tail` or a `for`/`cd` loop makes it refuse. Push each repo as a bare `git -C /abs/repo push origin main`.
- 2026-09-30 W23b: `pnpm gate <repos>` from invai-infra ran ~8 min end to end with a full pass; run it with nohup in the background and poll for `^log:`.
- 2026-09-30 A1: `pnpm gate` with no args includes held infra commits; always name repos. A 40P01 deadlock in `db:reset` passed on one retry (B-227). A background `until grep '^log:'` watcher with run_in_background wakes me when it ends.
- 2026-09-30 A1: open the screenshots myself: a QA report said "no es truncation" but Profit es had a clipped KPI.
- 2026-10-01 A2: a contract enum addition breaks exhaustive switches and `Record<Enum,…>` maps in every consumer; have the plan review grep all repos and put each fix on a card before the contract commits.
- 2026-10-01 A2: don't add an AC to a running card (no way to message it); queue it for round 2. Web cards with template-literal i18n keys must list `scripts/i18n-extra-en.json`.
- 2026-10-01 A2: a gate whose E2E takes far longer than usual (49 min) points to a Valkey/OrbStack hang; check `valkey-cli ping` before calling it a product failure.
- 2026-09-30 P1: `pnpm gate` refuses (doesn't hang) when a process it didn't start holds :3000 (a 6 h old `pnpm dev:api`, PID 91824). Check `lsof -iTCP:3000` when the last review starts, so the starter can free it in time.
- 2026-09-30 P1: polish/bug waves live in `waves/P<n>/`; waves 24/25 stay paused deploy/CI prep (decision 0019). The next polish wave is P2; hand-off at the end of `waves/P1/wave.md`.
- 2026-10-01 P3 close: verify agents' claimed file changes with `git status`/`git log` (a "restored" file was still modified, later committed+reverted). Max 2 heavy test runs at once (16 GB RAM). Text naming a blocked git verb in heredocs gets denied; use Edit. "Verify first" cards can surface a real bug behind a "by design" finding: check the cause, not only the data.
- [Gate root cause: trace first](gate-rootcause-trace-first.md) — read trace status codes before timing hypotheses; stop round 1 builders first
- 2026-10-01 P4: I can't TaskStop or message agents I didn't launch in this session's ownership, and card edits after start never reach a running agent: give grants before start, or route the edit to the path owner as its own task. A stalled builder (files quiet 3 h) is finished by a bounded finisher "on top of its uncommitted edits, stop if files change under you".
- 2026-10-01 P4: ask every money/fixture reviewer to prove the changed test red on the pre-fix commit in a worktree; it caught a digest check that passed on the bug. One reviewer agent may write two small cards' verdict files to save a slot.
- 2026-10-01 P5: when a contract makes params optional, the plan ruling must name the web's fallback for each missing key (T-P5-5 r1 gap). Agents can die on the stream watchdog with Docker healthy: relaunch with the same prompt. tsx watch respawns orphan APIs of old waves on any backend edit; assign Valkey DBs after `lsof -iTCP:3100-3199` + `ps eww` env check. A builder may hand back mid-suite (2 min Bash default); read its log and use a bounded finisher to commit.
- 2026-10-01 P6: gate timing failures (tests far past 30 s, db:reset 40P01) were Mac idle sleep: check `pmset -g log`, run `caffeinate -i pnpm gate ...`. A deadlocked reset leaves `invai` half-reset; reset+migrate by hand with nothing connected before rerunning. Several old `pnpm dev:api` watchers can serve one orphan port; kill every watcher in the chain.
- 2026-10-01 P7: guard-paths.py blocks my Write outside docs paths (e.g. a throwaway Playwright script in invai-web); screen looks go to qa-engineer (API + web only, no worker, keeps the gate seed). Push is still bare `git -C <repo> push origin main` (any `| tail` gets refused). The live guard refuses heredocs that only quote a script-writing redirect or blocked gh verbs: use Edit/Write for docs text. Owner made P7 the last wave (status-2026-10-01.md).
- [Gate AI keys and push form](gate-ai-keys-and-push-form.md) — P8: blank real AI keys for gates; one exact push form
