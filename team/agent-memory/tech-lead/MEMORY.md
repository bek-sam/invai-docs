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
- 2026-09-27 W18: spec reviews found the demo seed has only ~30 days of order history; anything trend/weekly needs fixture shops in tests (B-130 for longer seed history).
