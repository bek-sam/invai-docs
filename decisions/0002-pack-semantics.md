# 0002: Pack semantics

- Status: accepted (2026-09-24)
- Type: product (made by the tech lead in v1)

## Context
Architecture §3.1 defines item states. The pack station needed a clear meaning for "packed" and "shipped".

## Decision
- A **QC pass** moves the item `pressed → packed`, meaning it passed QC and is ready to pack.
- A **pack scan** records a `pack` scan with no state change. "Mark packed" checks that every non-cancelled unit is `packed`, releases the tote and puts the order in the shipping queue.
- Buying the **label** moves the items `packed → shipped` when tracking is pushed.

## Consequences
The floor, the backend and the E2E suites all rely on this. Changing it means changing the contract, the production module, the floor app and the golden-path tests together.
