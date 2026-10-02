---
name: red-on-base-depends-on-infra
description: When proving a test is red on base, check whether the base failure depends on local infra (MinIO, imaging) being up
metadata:
  type: feedback
---

2026-09-30 T-P2-2 r2: a "red on base" proof can depend on local services. The imaging-down job test was red on f6002ff only because MinIO was up: the old placeholder putObject succeeded. With MinIO down, the base code throws too and the test passes.

**Why:** red-on-base is the main proof for a fix. If the proof depends on infra state, the reviewer can draw the wrong conclusion.

**How to apply:** when running step 8 of independent-review, write down which services were up. To exercise the imaging client without the stack, run a tsx `.mts` script from the backend's node_modules (`createImagingClient(url)`), with your own imaging on a free port (`uv run uvicorn app.main:app --port 80xx`). Stop it with `kill <PID>`; the guard hook blocks pkill.
