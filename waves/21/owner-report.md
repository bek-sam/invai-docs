# Wave 21 owner report (2026-09-29)

## What works now
- Sign-up shows links to the Terms and the Privacy Policy, and the app has a Help entry. Thirteen help articles in English and Spanish cover getting started, SKU mapping, gang sheets and vendors, the floor tablet, receiving, labels, CSV tracking export, profit and ad spend, AI listings and the trademark check, the assistant, the weekly digest, team roles, and plans.
- Lawyer-ready drafts: terms, privacy policy, data processing agreement, sub-processor list (English and Spanish), a vendor inventory, an incident-response plan and an access-control policy. Every legal page says "Draft, pending legal review". Anything that needs your decision is a visible placeholder, never an invented value.
- The security record is corrected: Amazon wants a vulnerability scan every 30 days (not 180), and the November 2025 Amazon data-protection changes are mapped to what InvAI does and what's missing.
- The runbook is up to date (all 49 settings, how the demo reset works now, E2E steps).

## Evidence
- Every card has approving reviews (`reviews/`); pushed to `main` (docs with wave 20, web `3f383e5`).

## What went wrong
- Two review rounds on the incident plan: it had wrong claims (for example, that rotating one secret was safe when it would break floor PINs). All fixed and re-checked against the code.

## What needs you
- OI-19: when to bring in a lawyer for the drafts (default: wait until the email provider and the Amazon data-protection gaps are settled).
- Four Amazon data-protection gaps are now backlog items (account lockout, password history, 18-month data clean-up, required two-step sign-in for owner and admin: B-185..B-188). They matter before an Amazon SP-API application.
