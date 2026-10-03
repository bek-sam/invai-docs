# 0024. Agents verify with scripts; the owner tests in the browser

- Status: accepted
- Date: 2026-10-03
- Decided by: owner

## Context
Agents were checking features by driving Chrome and looking at screenshots (Claude in Chrome, and screenshot steps in `build-dashboard-screen`, `ux-audit` and the web-engineer's definition of done). Each screenshot costs a lot of tokens, and usage limits stopped the whole team several times during waves 26–27 (see `decisions/0018`). The owner said on 2026-10-03: stop the Chrome testing to save tokens; analyze and explore thoroughly before building; verify with automatic, script-based tests; the owner tests every feature in Chrome personally; report what the owner needs for that in a structured Notion database.

## Decision
- **No agent drives a browser or reads screenshots to verify work.** That means no Claude-in-Chrome tools and no "take a screenshot and look at it" steps. This overrides any role file or playbook step that says otherwise.
  - Exception: when the deliverable is itself an image (app-store or marketplace packets, landing-page drafts), and the owner asked for it.
- **Verification is automatic and script-based:**
  - unit and integration tests (Vitest, pytest)
  - API scripts (`curl` or a `tsx` script as the right role on the agent's own port)
  - headless Playwright E2E suites, which assert in code and print pass/fail only
  - the integration gate
  "Exercised for real" means a script hit the running feature and its assertions passed.
- **Build better before building.** Before coding, the owner of a card reads the existing code and decisions, checks library APIs in `node_modules` or the official docs, and writes the risks and edge cases into the card or report. Tests then cover those edge cases.
- **The owner tests in the browser.** After each wave, the tech lead (or the coordinator) adds one row per user-visible feature to the Notion database "InvAI Feature Test Guide". Each row has:
  - where to click, which demo role to use and what to try
  - what to expect
  - the automated evidence
  - what is mocked
  - the known gaps
  - what needs the owner
  Never put passwords, PINs, tokens or keys in Notion; name the demo role and point to `CLAUDE.md` "Demo data".
- The owner records each feature's result in that database (Passed / Failed + notes). A Failed row becomes a bug card in the next wave.

## Consequences
- Lower token use per card, and reviewers stop re-taking screenshots.
- Visual problems that only a person sees (layout, contrast, wording) are caught by the owner rather than by agents. Product-designer UI co-reviews check code, states, copy and a11y rules, not screenshots.
- Playwright suites must assert visible states in code (roles, text, visibility), because nobody looks at images.
